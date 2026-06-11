"""Adversarial container verification tests."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import jsonschema
import pytest

from src.container import (
    inspect_container,
    pack_container,
    unpack_container,
    verify_container,
)
from src.crypto import generate_master_key
from src.models import ObservabilityLevel
from src.security import MAX_ZIP_BYTES
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
    with pytest.raises(ValueError, match="ciphertext digest mismatch"):
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
    with pytest.raises(ValueError, match="ciphertext digest mismatch"):
        unpack_container(tampered, key)


def test_verify_rejects_extra_zip_member(tmp_path: Path) -> None:
    out, key = _pack(tmp_path)
    tampered = tmp_path / "extra.ento.zip"
    with zipfile.ZipFile(out, "r") as zin, zipfile.ZipFile(tampered, "w") as zout:
        for name in zin.namelist():
            zout.writestr(name, zin.read(name))
        zout.writestr("tracks/evil.ento", b"payload")
    with pytest.raises(ValueError, match="unexpected ZIP members"):
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
    with pytest.raises(jsonschema.ValidationError):
        verify_container(tampered, key)


def test_inspect_rejects_oversize_zip(tmp_path: Path) -> None:
    out, _ = _pack(tmp_path)
    huge = tmp_path / "huge.ento.zip"
    with huge.open("wb") as handle:
        handle.write(out.read_bytes())
        handle.seek(MAX_ZIP_BYTES + 1)
        handle.write(b"\0")
    with pytest.raises(ValueError, match="max size"):
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
    with pytest.raises(ValueError, match="proof/chain.json required"):
        verify_container(out, require_proof=True)


def test_pack_rejects_duplicate_track_ids(tmp_path: Path) -> None:
    """Two PlainTracks sharing a track_id must be rejected at pack time, not
    silently collapsed into a lossy-but-'key-authenticated' container
    (the manifest would list 2 tracks while the ZIP held 1)."""
    from src.models import PlainTrack

    key = generate_master_key()
    dup = (
        PlainTrack(
            track_id="dup", track_type="ento:blockchain.proof", payload=b"FIRST"
        ),
        PlainTrack(
            track_id="dup", track_type="ento:blockchain.proof", payload=b"SECOND"
        ),
    )
    with pytest.raises(ValueError, match="duplicate track ids"):
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


_GOOD_MANIFEST = {
    "format_version": "0.2.0",
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


def test_read_path_schema_rejects_string_byte_length(tmp_path: Path) -> None:
    """Schema validation runs on RAW JSON before coercion: a JSON-string
    byte_length ('10') must be rejected, not int()-laundered past the schema."""
    bad = json.loads(json.dumps(_GOOD_MANIFEST))
    bad["tracks"][0]["byte_length"] = "10"
    out = _zip_with_manifest(tmp_path / "bad.zip", bad)
    with pytest.raises(jsonschema.ValidationError):
        verify_container(out)


def test_read_path_schema_rejects_unknown_track_field(tmp_path: Path) -> None:
    """An unknown track field must be caught by additionalProperties:false on the
    raw JSON, not silently dropped by from_dict before validation."""
    bad = json.loads(json.dumps(_GOOD_MANIFEST))
    bad["tracks"][0]["EVIL_EXTRA"] = "x"
    out = _zip_with_manifest(tmp_path / "bad.zip", bad)
    with pytest.raises(jsonschema.ValidationError):
        verify_container(out)


def test_read_path_rejects_duplicate_manifest_track_ids(tmp_path: Path) -> None:
    """A crafted container whose manifest lists a track id more than once must be
    rejected on read — the member-set check uses set() and would otherwise collapse
    the duplicate, verifying ok:True with an inflated track_count."""
    man = json.loads(json.dumps(_GOOD_MANIFEST))
    man["observability_level"] = 0
    t = man["tracks"][0]
    t["sha256_plaintext"] = ""
    t["sha256_ciphertext"] = ""
    man["tracks"] = [dict(t, id="a"), dict(t, id="a"), dict(t, id="b")]
    out = tmp_path / "dup.zip"
    with zipfile.ZipFile(out, "w") as zf:
        zf.writestr("manifest.json", json.dumps(man))
        zf.writestr("tracks/a.ento", b"x" * 32)
        zf.writestr("tracks/b.ento", b"y" * 32)
    with pytest.raises(ValueError, match="duplicate track ids"):
        verify_container(out)


def test_read_path_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    """A manifest with a repeated JSON object key must be rejected rather than
    silently collapsed last-wins (parse-then-validate divergence)."""
    raw = (
        '{"format_version":"0.2.0","format_version":"9.9.9",'
        '"created":"2026-01-01T00:00:00Z","creator":"t",'
        '"observability_level":0,"tracks":[]}'
    )
    out = tmp_path / "dupkey.zip"
    with zipfile.ZipFile(out, "w") as zf:
        zf.writestr("manifest.json", raw)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        verify_container(out)


def test_proof_correspondence_empty_is_not_a_false_pass(tmp_path: Path) -> None:
    """Negative control for the proof correspondence check: a NON-empty manifest
    paired with an empty proof chain must be rejected, even though an empty manifest
    with an empty proof is (correctly) vacuously consistent."""
    from src.manifest import manifest_to_json
    from src.models import Manifest, ObservabilityLevel, ProofExport, TrackDescriptor
    from src.proof import verify_proof_export

    populated = Manifest(
        format_version="0.2.0",
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
    mjson = manifest_to_json(populated)
    import src.crypto as _crypto

    empty_proof = ProofExport(
        format_version="0.2.0",
        created="x",
        manifest_sha256=_crypto.sha256_hex(mjson.encode("utf-8")),
        links=(),
    )
    # Digest matches and the empty chain is vacuously self-consistent, but the
    # links do not cover the manifest's one track -> must fail correspondence.
    assert verify_proof_export(empty_proof, mjson) is False


def test_keyed_verify_rejects_lying_byte_length(tmp_path: Path) -> None:
    """A rewritten byte_length (with the proof removed so the manifest-digest change
    isn't caught there) must be rejected by the keyed byte_length reconciliation —
    not verified key-authenticated while advertising a false size."""
    key = generate_master_key()
    tracks = load_fixture_tracks()
    src = tmp_path / "real.zip"
    pack_container(src, key, tracks, observability_level=ObservabilityLevel.AUDITABLE)
    with zipfile.ZipFile(src) as zf:
        man = json.loads(zf.read("manifest.json"))
        members = {n: zf.read(n) for n in zf.namelist()}
    man["tracks"][0]["byte_length"] = 999999
    out = tmp_path / "lie.zip"
    with zipfile.ZipFile(out, "w") as zf:
        for name, blob in members.items():
            if name.startswith("proof/"):
                continue  # drop proof so only the byte_length check can catch it
            zf.writestr(name, json.dumps(man) if name == "manifest.json" else blob)
    with pytest.raises(ValueError, match="byte_length mismatch"):
        verify_container(out, key, require_integrity=True)


def test_keyed_verify_rejects_sealed_header_byte_length_bypass(tmp_path: Path) -> None:
    """A crafted container that CLAIMS SEALED (observability_level=0, an unauthenticated
    header field) while KEEPING real ciphertext/plaintext digests and a rewritten non-zero
    byte_length must NOT verify key-authenticated. Skipping the byte_length reconcile at
    SEALED let an attacker key off the unauthenticated header to smuggle a false size; the
    SEALED branch now binds byte_length to the redaction sentinel (0)."""
    key = generate_master_key()
    tracks = load_fixture_tracks()
    src = tmp_path / "auditable.zip"
    pack_container(src, key, tracks, observability_level=ObservabilityLevel.AUDITABLE)
    with zipfile.ZipFile(src) as zf:
        man = json.loads(zf.read("manifest.json"))
        members = {n: zf.read(n) for n in zf.namelist()}
    man["observability_level"] = 0  # claim SEALED, but keep the real digests below
    man["tracks"][0]["byte_length"] = 999999
    out = tmp_path / "sealed_bypass.zip"
    with zipfile.ZipFile(out, "w") as zf:
        for name, blob in members.items():
            if name.startswith("proof/"):
                continue
            zf.writestr(name, json.dumps(man) if name == "manifest.json" else blob)
    with pytest.raises(ValueError, match="byte_length mismatch"):
        verify_container(out, key, require_integrity=True)


def test_keyed_verify_accepts_truthful_byte_length_all_levels(tmp_path: Path) -> None:
    """The byte_length reconciliation must not false-reject honest containers at any
    export level (SEALED zeroes byte_length and is skipped; 1/2/3 carry the real value)."""
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
