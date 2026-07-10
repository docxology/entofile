"""Blockchain-style proof chain export for ENTO containers."""

from __future__ import annotations

from datetime import datetime, timezone

from . import crypto
from .manifest import manifest_from_json, manifest_to_json
from .models import Manifest, ProofExport, ProofLink


def export_proof(manifest: Manifest) -> ProofExport:
    """Build hash-chained proof from manifest track plaintext hashes."""
    manifest_json = manifest_to_json(manifest)
    manifest_hash = crypto.sha256_hex(manifest_json.encode("utf-8"))
    previous = "0" * 64
    links: list[ProofLink] = []
    for index, track in enumerate(manifest.tracks):
        payload = f"{previous}:{track.id}:{track.sha256_plaintext}".encode()
        entry_hash = crypto.sha256_hex(payload)
        links.append(
            ProofLink(
                index=index,
                track_id=track.id,
                sha256_plaintext=track.sha256_plaintext,
                previous_hash=previous,
                entry_hash=entry_hash,
            )
        )
        previous = entry_hash
    created = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return ProofExport(
        format_version=manifest.format_version,
        created=created,
        manifest_sha256=manifest_hash,
        links=tuple(links),
    )


def verify_proof_chain(proof: ProofExport) -> bool:
    """Verify consecutive entry hashes."""
    previous = "0" * 64
    for link in proof.links:
        if link.previous_hash != previous:
            return False
        payload = f"{previous}:{link.track_id}:{link.sha256_plaintext}".encode()
        expected = crypto.sha256_hex(payload)
        if link.entry_hash != expected:
            return False
        previous = link.entry_hash
    return True


def verify_proof_export(proof: ProofExport, manifest_json: str) -> bool:
    """Verify a proof export against the manifest it claims to describe.

    Three independent checks, all of which must hold:

    1. **Digest binding** — ``proof.manifest_sha256`` equals the SHA-256 of the
       supplied manifest bytes (the proof is bound to *these* bytes).
    2. **Chain self-consistency** — each link's ``previous_hash``/``entry_hash``
       form a valid hash chain (``verify_proof_chain``).
    3. **Link↔track correspondence (NEW)** — the chain is the canonical export of
       *this* manifest: ``format_version`` matches, and the links correspond 1:1
       and in order to the manifest's tracks by ``(track_id, sha256_plaintext)``.

    Check 3 closes a gap where a chain that was internally valid and carried the
    right manifest digest could still describe a *different* set of tracks than the
    manifest lists (the digest binds the bytes, but nothing previously tied the
    link contents to the manifest's tracks). The proof remains unkeyed — this is a
    *consistency* guarantee, not authentication of origin; adversarial integrity
    still comes only from key-based decryption ([sec:security_verification]).

    ``manifest_json`` must be the exact bytes the proof was exported from (the
    *exported*, observability-redacted manifest — see ``_write_container_zip``), so
    redacted ``sha256_plaintext`` fields compare equal on both sides.
    """
    expected = crypto.sha256_hex(manifest_json.encode("utf-8"))
    if proof.manifest_sha256 != expected:
        return False
    if not verify_proof_chain(proof):
        return False
    return _links_match_manifest(proof, manifest_from_json(manifest_json))


def _links_match_manifest(proof: ProofExport, manifest: Manifest) -> bool:
    """True iff the proof's links are the canonical export of ``manifest``'s tracks.

    Rebuilds the expected chain from the manifest with :func:`export_proof` and
    compares the link tuples (track_id, sha256_plaintext, previous/entry hashes)
    plus the bound ``format_version``. This makes the proof reject a chain whose
    links describe a different track set, a reordering, or a different
    ``format_version`` than the manifest, even when the manifest digest matches.
    """
    if proof.format_version != manifest.format_version:
        return False
    rebuilt = export_proof(manifest)
    if len(proof.links) != len(rebuilt.links):
        return False
    for got, want in zip(proof.links, rebuilt.links, strict=False):
        if (
            got.index,
            got.track_id,
            got.sha256_plaintext,
            got.previous_hash,
            got.entry_hash,
        ) != (
            want.index,
            want.track_id,
            want.sha256_plaintext,
            want.previous_hash,
            want.entry_hash,
        ):
            return False
    return True
