"""Adversarial container verification tests."""

from __future__ import annotations

import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from src.container import (
    inspect_container,
    pack_container,
    unpack_container,
    verify_container,
)
from src.crypto import generate_master_key, sha256_hex
from src.errors import ContainerError, IntegrityError, ManifestError
from src.manifest import build_track_descriptor, manifest_to_json
from src.manifest_binding import compute_manifest_binding
from src.models import Manifest, ObservabilityLevel, PlainTrack
from src.proof import export_proof
from src.security import MAX_ZIP_BYTES
from src.track import encrypt_track
from tests.fixtures import load_fixture_tracks


def _pack(tmp_path: Path) -> tuple[Path, bytes]:
    key = generate_master_key()
    tracks = load_fixture_tracks()
    out = tmp_path / "sample.ento.zip"
    pack_container(out, key, tracks)
    return out, key


def test_verify_container_without_key(tmp_path: Path) -> None:
    out, _ = _pack(tmp_path)
    result = verify_container(out)
    assert result["ok"] is True
    assert result["proof_present"] is True
    assert result["plaintext_verified"] is False


def test_verify_container_with_key(tmp_path: Path) -> None:
    out, key = _pack(tmp_path)
    result = verify_container(out, key)
    assert result["plaintext_verified"] is True


def test_inspect_skips_ciphertext_digest_but_verify_fails(tmp_path: Path) -> None:
    out, key = _pack(tmp_path)
    tampered = tmp_path / "cipher-only.ento.zip"
    with zipfile.ZipFile(out, "r") as zin, zipfile.ZipFile(tampered, "w") as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name.startswith("tracks/"):
                data = data[:-1] + bytes([data[-1] ^ 0x01])
            zout.writestr(name, data)
    inspect_container(tampered)
    with pytest.raises(IntegrityError, match="ciphertext digest mismatch"):
        verify_container(tampered, key)


def test_unpack_rejects_ciphertext_hash_mismatch(tmp_path: Path) -> None:
    out, key = _pack(tmp_path)
    tampered = tmp_path / "bad-cipher.ento.zip"
    with zipfile.ZipFile(out, "r") as zin, zipfile.ZipFile(tampered, "w") as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name.startswith("tracks/"):
                data = data[:-1] + bytes([data[-1] ^ 0x01])
            zout.writestr(name, data)
    with pytest.raises(IntegrityError, match="ciphertext digest mismatch"):
        unpack_container(tampered, key)


def test_verify_rejects_extra_zip_member(tmp_path: Path) -> None:
    out, key = _pack(tmp_path)
    tampered = tmp_path / "extra.ento.zip"
    with zipfile.ZipFile(out, "r") as zin, zipfile.ZipFile(tampered, "w") as zout:
        for name in zin.namelist():
            zout.writestr(name, zin.read(name))
        zout.writestr("tracks/evil.ento", b"payload")
    with pytest.raises(ContainerError, match="unexpected ZIP members"):
        verify_container(tampered, key)


def test_verify_rejects_malicious_track_id_in_manifest(tmp_path: Path) -> None:
    out, key = _pack(tmp_path)
    tampered = tmp_path / "evil-id.ento.zip"
    with zipfile.ZipFile(out, "r") as zin, zipfile.ZipFile(tampered, "w") as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name == "manifest.json":
                manifest = json.loads(data.decode("utf-8"))
                manifest["tracks"][0]["id"] = "../escape"
                data = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
            zout.writestr(name, data)
    with pytest.raises(ManifestError):
        verify_container(tampered, key)


def test_inspect_rejects_oversize_zip(tmp_path: Path) -> None:
    out, _ = _pack(tmp_path)
    huge = tmp_path / "huge.ento.zip"
    with huge.open("wb") as handle:
        handle.write(out.read_bytes())
        handle.seek(MAX_ZIP_BYTES + 1)
        handle.write(b"\0")
    with pytest.raises(ContainerError, match="max size"):
        inspect_container(huge)


def test_verify_requires_proof_when_missing(tmp_path: Path) -> None:
    key = generate_master_key()
    tracks = load_fixture_tracks()
    out = tmp_path / "sealed.ento.zip"
    pack_container(
        out,
        key,
        tracks,
        observability_level=ObservabilityLevel.SEALED,
        export_level=ObservabilityLevel.SEALED,
    )
    with pytest.raises(ContainerError, match=r"proof/chain.json required"):
        verify_container(out, require_proof=True)


def test_pack_rejects_duplicate_track_ids(tmp_path: Path) -> None:
    """Two PlainTracks sharing a track_id must be rejected at pack time, not
    silently collapsed into a lossy-but-'key-authenticated' container
    (the manifest would list 2 tracks while the ZIP held 1)."""
    key = generate_master_key()
    dup = (
        PlainTrack(
            track_id="dup", track_type="ento:blockchain.proof", payload=b"FIRST"
        ),
        PlainTrack(
            track_id="dup", track_type="ento:blockchain.proof", payload=b"SECOND"
        ),
    )
    with pytest.raises(ManifestError, match="duplicate track ids"):
        pack_container(
            tmp_path / "c.zip",
            key,
            dup,
            observability_level=ObservabilityLevel.AUDITABLE,
            export_level=ObservabilityLevel.RESOLVED,
        )


def _zip_with_manifest(path: Path, manifest_dict: dict) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest_dict))
    return path


def _rebind(manifest_dict: dict) -> dict:
    manifest_dict.pop("manifest_binding", None)
    manifest = Manifest.from_dict(manifest_dict)
    manifest_dict["manifest_binding"] = compute_manifest_binding(manifest)
    return manifest_dict


def _good_manifest() -> dict:
    return _rebind(
        {
            "format_version": "0.5.0",
            "created": "2026-01-01T00:00:00Z",
            "creator": "t",
            "observability_level": 3,
            "tracks": [
                {
                    "id": "a",
                    "type": "ento:blockchain.proof",
                    "sha256_plaintext": "1" * 64,
                    "sha256_ciphertext": "2" * 64,
                    "byte_length": 10,
                }
            ],
        }
    )


def test_read_path_schema_rejects_string_byte_length(tmp_path: Path) -> None:
    """Schema validation runs on RAW JSON before coercion: a JSON-string
    byte_length ('10') must be rejected, not int()-laundered past the schema."""
    bad = json.loads(json.dumps(_good_manifest()))
    bad["tracks"][0]["byte_length"] = "10"
    out = _zip_with_manifest(tmp_path / "bad.zip", bad)
    with pytest.raises(ManifestError):
        verify_container(out)


def test_read_path_schema_rejects_unknown_track_field(tmp_path: Path) -> None:
    """An unknown track field must be caught by additionalProperties:false on the
    raw JSON, not silently dropped by from_dict before validation."""
    bad = json.loads(json.dumps(_good_manifest()))
    bad["tracks"][0]["EVIL_EXTRA"] = "x"
    out = _zip_with_manifest(tmp_path / "bad.zip", bad)
    with pytest.raises(ManifestError):
        verify_container(out)


def test_read_path_rejects_duplicate_manifest_track_ids(tmp_path: Path) -> None:
    """A crafted container whose manifest lists a track id more than once must be
    rejected on read — the member-set check uses set() and would otherwise collapse
    the duplicate, verifying ok:True with an inflated track_count."""
    man = json.loads(json.dumps(_good_manifest()))
    man["observability_level"] = 0
    t = man["tracks"][0]
    t["sha256_plaintext"] = ""
    t["sha256_ciphertext"] = ""
    man["tracks"] = [dict(t, id="a"), dict(t, id="a"), dict(t, id="b")]
    _rebind(man)
    out = tmp_path / "dup.zip"
    with zipfile.ZipFile(out, "w") as zf:
        zf.writestr("manifest.json", json.dumps(man))
        zf.writestr("tracks/a.ento", b"x" * 32)
        zf.writestr("tracks/b.ento", b"y" * 32)
    with pytest.raises(ContainerError, match="duplicate track ids"):
        verify_container(out)


def test_read_path_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    """A manifest with a repeated JSON object key must be rejected rather than
    silently collapsed last-wins (parse-then-validate divergence)."""
    raw = (
        '{"format_version":"0.5.0","format_version":"9.9.9",'
        '"created":"2026-01-01T00:00:00Z","creator":"t",'
        '"observability_level":0,"tracks":[]}'
    )
    out = tmp_path / "dupkey.zip"
    with zipfile.ZipFile(out, "w") as zf:
        zf.writestr("manifest.json", raw)
    with pytest.raises(ManifestError, match="duplicate JSON key"):
        verify_container(out)


def test_proof_correspondence_empty_is_not_a_false_pass() -> None:
    """A non-empty bound manifest paired with an empty proof chain is rejected."""
    from src.models import ProofExport, TrackDescriptor
    from src.proof import verify_proof_export

    template = Manifest(
        format_version="0.5.0",
        created="2026-01-01T00:00:00Z",
        creator="t",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(
            TrackDescriptor(
                id="a",
                type="ento:blockchain.proof",
                sha256_plaintext="1" * 64,
                sha256_ciphertext="2" * 64,
                byte_length=1,
            ),
        ),
    )
    populated = replace(
        template, manifest_binding=compute_manifest_binding(template)
    )
    mjson = manifest_to_json(populated)
    empty_proof = ProofExport(
        format_version="0.5.0",
        created="x",
        manifest_sha256=sha256_hex(mjson.encode("utf-8")),
        links=(),
    )
    # The digest and binding match, but the empty chain does not cover the track.
    assert verify_proof_export(empty_proof, mjson) is False


def _write_bound_byte_length_container(
    path: Path,
    key: bytes,
    tracks: tuple[PlainTrack, ...],
    *,
    declared_byte_length: int,
    level: ObservabilityLevel,
) -> None:
    """Build a real bound container whose authenticated declaration is false."""
    descriptors = tuple(
        replace(
            build_track_descriptor(track, b"", observability=int(level)),
            byte_length=declared_byte_length,
        )
        for track in tracks
    )
    template = Manifest(
        format_version="0.5.0",
        created="2026-01-01T00:00:00Z",
        creator="byte-length-control",
        observability_level=level,
        tracks=descriptors,
    )
    binding = compute_manifest_binding(template)
    encrypted = {
        track.track_id: encrypt_track(key, track, manifest_binding=binding)
        for track in tracks
    }
    manifest = replace(
        template,
        tracks=tuple(
            replace(
                descriptor,
                sha256_ciphertext=sha256_hex(
                    encrypted[descriptor.id].to_bytes()
                ),
            )
            for descriptor in descriptors
        ),
        manifest_binding=binding,
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", manifest_to_json(manifest))
        for track_id, encrypted_track in encrypted.items():
            zf.writestr(f"tracks/{track_id}.ento", encrypted_track.to_bytes())
        if level != ObservabilityLevel.SEALED:
            zf.writestr(
                "proof/chain.json",
                json.dumps(
                    export_proof(manifest).to_dict(), indent=2, sort_keys=True
                )
                + "\n",
            )


def test_keyed_verify_rejects_lying_byte_length(tmp_path: Path) -> None:
    """Binding, proof, ciphertext digest, and AEAD all pass before length fails."""
    key = generate_master_key()
    out = tmp_path / "lie.zip"
    _write_bound_byte_length_container(
        out,
        key,
        load_fixture_tracks(),
        declared_byte_length=999999,
        level=ObservabilityLevel.AUDITABLE,
    )
    with pytest.raises(IntegrityError, match="byte_length mismatch"):
        verify_container(out, key, require_integrity=True)


def test_keyed_verify_rejects_sealed_byte_length_sentinel_violation(
    tmp_path: Path,
) -> None:
    """A bound SEALED producer fixture must declare the redaction sentinel zero."""
    key = generate_master_key()
    out = tmp_path / "sealed-bad-length.zip"
    _write_bound_byte_length_container(
        out,
        key,
        load_fixture_tracks(),
        declared_byte_length=999999,
        level=ObservabilityLevel.SEALED,
    )
    with pytest.raises(IntegrityError, match="byte_length mismatch"):
        verify_container(out, key, require_integrity=True)


def test_keyed_verify_accepts_truthful_byte_length_all_levels(tmp_path: Path) -> None:
    """Honest length declarations pass at every export level (SEALED uses zero)."""
    key = generate_master_key()
    tracks = load_fixture_tracks()
    for level in ObservabilityLevel:
        out = tmp_path / f"l{int(level)}.zip"
        pack_container(
            out,
            key,
            tracks,
            observability_level=ObservabilityLevel.AUDITABLE,
            export_level=level,
        )
        result = verify_container(out, key, require_integrity=True)
        assert result["ok"] is True, f"level {int(level)} should verify"
