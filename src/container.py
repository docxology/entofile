"""ENTO ZIP container pack/unpack."""

from __future__ import annotations

import json
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Literal

from . import crypto
from . import track as track_mod
from .crypto import FORMAT_VERSION
from .errors import ContainerError, IntegrityError
from .manifest import (
    build_track_descriptor,
    manifest_from_json,
    manifest_to_json,
    validate_manifest_dict,
    validate_plain_tracks,
)
from .manifest_binding import compute_manifest_binding
from .models import (
    EncryptedTrack,
    Manifest,
    ObservabilityLevel,
    PlainTrack,
    ProofExport,
)
from .observability import filter_manifest, include_proof_chain, validate_export_level
from .proof import export_proof, verify_proof_export
from .security import (
    MAX_MANIFEST_BYTES,
    assert_zip_members_match_manifest,
    safe_read_member,
    validate_track_id,
    validate_zip_archive,
)

IntegrityMode = Literal["manifest_only", "full"]

# The integrity levels verify_container can report, in decreasing assurance order.
# Single source of truth: the assignment branches below use these names, and the
# manuscript's "one of three values" count derives from len(REPORTED_INTEGRITY_LEVELS).
ReportedIntegrity = Literal["key-authenticated", "digest-only", "unverified"]
REPORTED_INTEGRITY_LEVELS: tuple[ReportedIntegrity, ...] = (
    "key-authenticated",
    "digest-only",
    "unverified",
)


@dataclass(frozen=True)
class VerifiedContainerContext:
    """Shared state after ZIP policy and manifest checks."""

    zf: zipfile.ZipFile
    manifest: Manifest
    track_ids: tuple[str, ...]
    proof_present: bool


def _track_ids(manifest: Manifest) -> tuple[str, ...]:
    return tuple(entry.id for entry in manifest.tracks)


def _read_manifest_from_zip(zf: zipfile.ZipFile) -> Manifest:
    if "manifest.json" not in zf.namelist():
        raise ContainerError("missing manifest.json in container")
    raw = safe_read_member(zf, "manifest.json", max_bytes=MAX_MANIFEST_BYTES)
    # Parse and validate the raw JSON before dataclass coercion. The shared parser
    # rejects duplicate keys and validates the requested schema before ``from_dict``
    # can coerce values or discard unknown fields.
    manifest = manifest_from_json(raw.decode("utf-8"))
    if manifest.format_version in crypto.MANIFEST_BINDING_FORMATS and not manifest.tracks:
        raise ContainerError("0.5.0 containers require at least one track")
    # Manifest-track uniqueness is a READ-path invariant too: a crafted container can
    # list a track id more than once even though the ZIP can hold only one member per
    # name and the encrypted dict is keyed by id. The member-set check uses set() and
    # so collapses the duplicate; without this guard such a container verifies ok:True
    # with an inflated track_count. The write path enforces the same via
    # validate_plain_tracks; this closes the producer-untrusted case.
    ids = [entry.id for entry in manifest.tracks]
    if len(ids) != len(set(ids)):
        dupes = sorted({tid for tid in ids if ids.count(tid) > 1})
        raise ContainerError(f"manifest lists duplicate track ids: {dupes}")
    for entry in manifest.tracks:
        validate_track_id(entry.id)
    return manifest


def _ciphertext_digests_present(manifest: Manifest) -> bool:
    """True only when every track carries a non-empty ciphertext digest."""
    return bool(manifest.tracks) and all(
        bool(e.sha256_ciphertext) for e in manifest.tracks
    )


def _reconcile_byte_length(
    manifest: Manifest, track_id: str, manifest_byte_length: int, plaintext: bytes
) -> None:
    """Cross-check a track's declared ``byte_length`` against the decrypted plaintext.

    ``byte_length`` is an unauthenticated manifest field; with the master key we hold
    the *true* plaintext, so this is the one moment its declared length can be bound to
    reality. Without this check a container with a rewritten ``byte_length`` (and no
    proof chain to catch the manifest-digest change) verifies ``key-authenticated`` while
    advertising a false size — the same manifest-field-unbound-to-reality class the
    digest check closes for content. At the SEALED level redaction deliberately zeroes
    ``byte_length`` (``observability.py``), so it cannot be reconciled against the real
    plaintext length; instead it is bound to the redaction SENTINEL (``0``). Skipping
    SEALED entirely would let an attacker key off the *unauthenticated*
    ``observability_level`` header — claim SEALED while KEEPING real digests and a
    rewritten non-zero ``byte_length`` — to smuggle a false size past a keyed verify as
    ``key-authenticated``. Requiring the sentinel closes that, while every legitimately
    produced SEALED container (``byte_length == 0``) still passes. The non-SEALED
    comparison uses the *unpadded* plaintext, so 0.3.1/0.4.0 PADMÉ padding does not
    affect it.
    """
    if manifest.observability_level == ObservabilityLevel.SEALED:
        if manifest_byte_length != 0:
            raise IntegrityError(
                f"byte_length mismatch for track {track_id!r}: SEALED redaction requires "
                f"byte_length 0 (the redaction sentinel), manifest declares {manifest_byte_length}"
            )
        return
    if manifest_byte_length != len(plaintext):
        raise IntegrityError(
            f"byte_length mismatch for track {track_id!r}: "
            f"manifest declares {manifest_byte_length}, plaintext is {len(plaintext)} bytes"
        )


def _verify_ciphertext_hashes(zf: zipfile.ZipFile, manifest: Manifest) -> None:
    """Compare present ciphertext digests. Empty digests are NOT silently treated
    as verified — their absence is surfaced via ``ciphertext_digests_present`` in
    the verification result so callers cannot mistake a redacted/stripped manifest
    for one whose integrity was checked."""
    for entry in manifest.tracks:
        raw = safe_read_member(zf, f"tracks/{entry.id}.ento")
        if not entry.sha256_ciphertext:
            continue
        digest = crypto.sha256_hex(raw)
        if digest != entry.sha256_ciphertext:
            raise IntegrityError(
                f"ciphertext digest mismatch for track {entry.id!r}: expected {entry.sha256_ciphertext}, got {digest}"
            )


def _verify_proof_if_present(zf: zipfile.ZipFile, manifest: Manifest) -> bool:
    """Check the proof chain is internally consistent, bound to the manifest bytes,
    AND that its links correspond 1:1 to the manifest's tracks (see
    ``verify_proof_export``).

    NOTE: the proof chain is an *unkeyed* SHA-256 structure. It detects accidental
    corruption and binds the proof to a given manifest, but carries no secret —
    any party that can rewrite the container can recompute a self-consistent proof.
    It is therefore NOT an authentication of origin. Adversarial integrity comes
    only from decrypting with the master key (AES-256-GCM)."""
    names = zf.namelist()
    if "proof/chain.json" not in names:
        return False
    raw = safe_read_member(zf, "proof/chain.json", max_bytes=MAX_MANIFEST_BYTES)
    proof = ProofExport.from_dict(json.loads(raw.decode("utf-8")))
    manifest_json = safe_read_member(
        zf, "manifest.json", max_bytes=MAX_MANIFEST_BYTES
    ).decode("utf-8")
    if not verify_proof_export(proof, manifest_json):
        raise IntegrityError("proof chain does not match manifest.json")
    return True


def _apply_integrity_checks(
    ctx: VerifiedContainerContext,
    *,
    integrity: IntegrityMode,
    require_proof: bool = False,
) -> None:
    if integrity == "full":
        _verify_ciphertext_hashes(ctx.zf, ctx.manifest)
        if ctx.proof_present:
            _verify_proof_if_present(ctx.zf, ctx.manifest)
        elif require_proof:
            raise ContainerError("proof/chain.json required but absent")


@contextmanager
def _with_verified_container(
    source: Path,
    *,
    integrity: IntegrityMode,
    require_proof: bool = False,
) -> Iterator[VerifiedContainerContext]:
    """Open a container, validate ZIP policy and manifest membership."""
    validate_zip_archive(source)
    with zipfile.ZipFile(source, "r") as zf:
        manifest = _read_manifest_from_zip(zf)
        track_ids = _track_ids(manifest)
        proof_present = "proof/chain.json" in zf.namelist()
        assert_zip_members_match_manifest(
            zf.namelist(),
            track_ids,
            include_proof=proof_present,
        )
        ctx = VerifiedContainerContext(
            zf=zf,
            manifest=manifest,
            track_ids=track_ids,
            proof_present=proof_present,
        )
        _apply_integrity_checks(ctx, integrity=integrity, require_proof=require_proof)
        yield ctx


def verify_container(
    source: Path,
    master_key: bytes | None = None,
    *,
    require_proof: bool = False,
    require_integrity: bool = False,
) -> dict[str, object]:
    """Verify container integrity, decrypting only when ``master_key`` is supplied.

    The ``integrity`` field reports what was *actually* established:

    - ``"key-authenticated"`` — every track decrypted under AES-256-GCM and any
      plaintext digests matched. This is the only level that resists an adversary
      who controls the container bytes. It authenticates **track plaintext content**
      (and the track_id, bound via the HKDF key-derivation label). For 0.5.0, the
      canonical exported manifest context is also bound into each track tag; for
      earlier profiles, unkeyed manifest header fields such as format_version,
      observability_level, and creator remain outside the GCM AAD. External
      signatures are still required for origin. The level is derived from the
      decrypt attempt, never read from a manifest field, so header mutation cannot
      downgrade it.
    - ``"digest-only"`` — no key supplied, but every track carried a ciphertext
      digest and all matched. Detects *accidental* corruption ONLY; an attacker
      can recompute digests (and the unkeyed proof chain), so this is NOT
      adversarial integrity.
    - ``"unverified"`` — no key and at least one track lacked a ciphertext digest
      (e.g. a redacted export or a stripped manifest). Nothing about the track
      bytes was checked.

    With ``require_integrity=True`` a result whose integrity is ``"unverified"``
    fails closed (``ok: False``) rather than reporting a well-formed-but-unchecked
    container as acceptable. ``require_integrity`` defaults to ``False`` so ``ok``
    keeps its structural-validity meaning for existing callers; every *shipped*
    entrypoint sets it ``True`` (the CLI ``verify`` and the pipeline
    ``build_container_verification_report``). A library caller doing keyless
    verification should pass ``require_integrity=True`` or read the ``integrity``
    field directly — ``ok`` alone is structural, not an integrity guarantee.
    """
    with _with_verified_container(
        source, integrity="full", require_proof=require_proof
    ) as ctx:
        digests_present = _ciphertext_digests_present(ctx.manifest)
        key_authenticated = False
        if master_key is not None:
            for entry in ctx.manifest.tracks:
                raw = safe_read_member(ctx.zf, f"tracks/{entry.id}.ento")
                encrypted = track_mod.parse_track_bytes(
                    entry.id, raw, format_version=ctx.manifest.format_version
                )
                # decrypt_track raises ValueError on GCM authentication failure,
                # so any ciphertext tamper is caught here regardless of digests.
                plaintext = track_mod.decrypt_track(
                    master_key,
                    encrypted,
                    format_version=ctx.manifest.format_version,
                    manifest_binding=ctx.manifest.manifest_binding,
                )
                if entry.sha256_plaintext:
                    digest = crypto.sha256_hex(plaintext)
                    if digest != entry.sha256_plaintext:
                        raise IntegrityError(
                            f"plaintext digest mismatch for track {entry.id!r}: "
                            f"expected {entry.sha256_plaintext}, got {digest}"
                        )
                _reconcile_byte_length(
                    ctx.manifest, entry.id, entry.byte_length, plaintext
                )
            # Any decrypt/digest/byte_length failure above raises, so reaching
            # here means every track authenticated; empty containers stay False.
            key_authenticated = bool(ctx.manifest.tracks)

        if key_authenticated:
            integrity = "key-authenticated"
        elif master_key is None and digests_present:
            integrity = "digest-only"
        else:
            integrity = "unverified"

        ok = not (require_integrity and integrity == "unverified")
        return {
            "ok": ok,
            "track_count": len(ctx.manifest.tracks),
            # proof_present means the chain was present AND matched manifest bytes —
            # full-mode verification raises on an inconsistent proof, so a returned
            # result with proof_present True implies it validated. The proof is
            # unkeyed, so this is consistency, not origin authentication.
            "proof_present": ctx.proof_present,
            "observability_level": int(ctx.manifest.observability_level),
            "integrity": integrity,
            "ciphertext_digests_present": digests_present,
            "plaintext_verified": key_authenticated,
        }


def _build_manifest(
    tracks: tuple[PlainTrack, ...],
    encrypted: dict[str, EncryptedTrack],
    *,
    creator: str,
    observability_level: ObservabilityLevel,
    format_version: str = FORMAT_VERSION,
    created: str | None = None,
    manifest_binding: str | None = None,
) -> Manifest:
    if created is None:
        created = _utc_timestamp()
    descriptors = [
        build_track_descriptor(
            plain,
            encrypted[plain.track_id].to_bytes(),
            observability=int(observability_level),
        )
        for plain in tracks
    ]
    return Manifest(
        format_version=format_version,
        created=created,
        creator=creator,
        observability_level=observability_level,
        tracks=tuple(descriptors),
        manifest_binding=manifest_binding,
    )


def _utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _prepare_pack(
    master_key: bytes,
    tracks: tuple[PlainTrack, ...],
    *,
    creator: str,
    observability_level: ObservabilityLevel,
    export_level: ObservabilityLevel | None,
    format_version: str,
) -> tuple[Manifest, dict[str, EncryptedTrack], ObservabilityLevel]:
    """Build the manifest/encrypted payload pair shared by both pack facades."""
    validate_plain_tracks(tracks)
    if crypto.requires_manifest_binding(format_version) and not tracks:
        raise ContainerError("0.5.0 containers require at least one track")
    level = observability_level if export_level is None else export_level
    validate_export_level(observability_level, level)
    created = _utc_timestamp()
    manifest_binding: str | None = None

    if crypto.requires_manifest_binding(format_version):
        # The binding must cover the manifest view that is actually exported. A
        # provisional descriptor is enough because the circular ciphertext digest
        # is excluded from the canonical projection.
        empty_encrypted = {
            plain.track_id: EncryptedTrack(plain.track_id, b"", b"", b"")
            for plain in tracks
        }
        template = _build_manifest(
            tracks,
            empty_encrypted,
            creator=creator,
            observability_level=observability_level,
            format_version=format_version,
            created=created,
        )
        manifest_binding = compute_manifest_binding(filter_manifest(template, level))

    encrypted = {
        plain.track_id: track_mod.encrypt_track(
            master_key,
            plain,
            format_version=format_version,
            manifest_binding=manifest_binding,
        )
        for plain in tracks
    }
    full_manifest = _build_manifest(
        tracks,
        encrypted,
        creator=creator,
        observability_level=observability_level,
        format_version=format_version,
        created=created,
        manifest_binding=manifest_binding,
    )
    return full_manifest, encrypted, level


def _write_container_zip(
    zf: zipfile.ZipFile,
    full_manifest: Manifest,
    encrypted: dict[str, EncryptedTrack],
    export_level: ObservabilityLevel,
) -> None:
    export_manifest = filter_manifest(full_manifest, export_level)
    validate_manifest_dict(export_manifest.to_dict())
    zf.writestr("manifest.json", manifest_to_json(export_manifest))
    for track_id, enc in encrypted.items():
        zf.writestr(f"tracks/{track_id}.ento", enc.to_bytes())
    if include_proof_chain(export_manifest.observability_level):
        proof = export_proof(export_manifest)
        zf.writestr("proof/chain.json", json.dumps(proof.to_dict(), indent=2) + "\n")


def pack_container(
    destination: Path,
    master_key: bytes,
    tracks: tuple[PlainTrack, ...],
    *,
    creator: str = "entofile",
    observability_level: ObservabilityLevel = ObservabilityLevel.AUDITABLE,
    export_level: ObservabilityLevel | None = None,
    format_version: str = FORMAT_VERSION,
) -> Manifest:
    """Pack tracks into an ENTO ZIP at destination.

    ``format_version`` defaults to the 0.4.0 release-candidate profile (standard
    nonce, AAD binding, and PADMÉ length padding). Pass ``0.5.0`` explicitly for
    exported-manifest context binding, or a prior supported version for a
    compatibility container."""
    full_manifest, encrypted, level = _prepare_pack(
        master_key,
        tracks,
        creator=creator,
        observability_level=observability_level,
        export_level=export_level,
        format_version=format_version,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as zf:
        _write_container_zip(zf, full_manifest, encrypted, level)
    return filter_manifest(full_manifest, level)


def unpack_container(
    source: Path,
    master_key: bytes,
) -> tuple[Manifest, dict[str, bytes]]:
    """Unpack ENTO ZIP; return manifest and decrypted payloads keyed by track id."""
    with _with_verified_container(source, integrity="full") as ctx:
        payloads: dict[str, bytes] = {}
        for entry in ctx.manifest.tracks:
            raw = safe_read_member(ctx.zf, f"tracks/{entry.id}.ento")
            encrypted = track_mod.parse_track_bytes(
                entry.id, raw, format_version=ctx.manifest.format_version
            )
            plaintext = track_mod.decrypt_track(
                master_key,
                encrypted,
                format_version=ctx.manifest.format_version,
                manifest_binding=ctx.manifest.manifest_binding,
            )
            if entry.sha256_plaintext:
                digest = crypto.sha256_hex(plaintext)
                if digest != entry.sha256_plaintext:
                    raise IntegrityError(
                        f"plaintext digest mismatch for track {entry.id!r}: "
                        f"expected {entry.sha256_plaintext}, got {digest}"
                    )
            _reconcile_byte_length(ctx.manifest, entry.id, entry.byte_length, plaintext)
            payloads[entry.id] = plaintext
        return ctx.manifest, payloads


def inspect_container(source: Path) -> Manifest:
    """Read manifest.json without decryption or ciphertext digest checks."""
    with _with_verified_container(source, integrity="manifest_only") as ctx:
        return ctx.manifest


def container_zip_listing(source: Path) -> list[str]:
    """Return sorted ZIP member names."""
    with zipfile.ZipFile(source, "r") as zf:
        return sorted(zf.namelist())


def pack_container_bytes(
    master_key: bytes,
    tracks: tuple[PlainTrack, ...],
    *,
    creator: str = "entofile",
    observability_level: ObservabilityLevel = ObservabilityLevel.AUDITABLE,
    export_level: ObservabilityLevel | None = None,
    format_version: str = FORMAT_VERSION,
) -> bytes:
    """Pack container to in-memory bytes (for benchmarks)."""
    full_manifest, encrypted, level = _prepare_pack(
        master_key,
        tracks,
        creator=creator,
        observability_level=observability_level,
        export_level=export_level,
        format_version=format_version,
    )
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
        _write_container_zip(zf, full_manifest, encrypted, level)
    return buf.getvalue()
