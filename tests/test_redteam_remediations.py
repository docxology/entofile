"""Regression tests for the 2026-05-28 RedTeam VectorSpecialists findings.

Each test pins a defect the comprehensive red-team surfaced, so a regression
re-opens it. No mocks: real containers, real ZIPs, the real schema.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from src import container, crypto
from src.manifest import manifest_from_json, manifest_to_json
from src.models import Manifest, ObservabilityLevel, PlainTrack, TrackDescriptor
from src.observability import filter_manifest
from src.proof import export_proof
from src.security import validate_zip_member_names

# --- V-D (HIGH): duplicate ZIP member name must not collapse under set() ------


def test_duplicate_zip_member_names_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate ZIP members"):
        validate_zip_member_names(["manifest.json", "tracks/a.ento", "tracks/a.ento"])


def test_container_with_duplicate_member_is_rejected(tmp_path: Path) -> None:
    """A second blob smuggled under a duplicated allowed name must be caught by
    the membership gate, not collapsed away by set()."""
    key = crypto.generate_master_key()
    track = PlainTrack(track_id="alpha", track_type="ento:blockchain.proof", payload=b"DATA")
    blob = container.pack_container_bytes(key, (track,))
    zin = zipfile.ZipFile(io.BytesIO(blob))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        for name in zin.namelist():
            z.writestr(name, zin.read(name))
        with pytest.warns(UserWarning, match="Duplicate name"):
            z.writestr("tracks/alpha.ento", b"MALICIOUS-SECOND-SHADOW")  # duplicate name
    p = tmp_path / "dup.ento.zip"
    p.write_bytes(out.getvalue())
    with pytest.raises(ValueError, match="duplicate ZIP members"):
        container.inspect_container(p)


# --- V-E (HIGH): SEALED must not leak plaintext byte_length -------------------


def _descriptor(byte_length: int) -> TrackDescriptor:
    return TrackDescriptor(
        id="eeg",
        type="ento:timeseries.eeg",
        sha256_plaintext="a" * 64,
        sha256_ciphertext="b" * 64,
        byte_length=byte_length,
    )


def _manifest(track: TrackDescriptor) -> Manifest:
    return Manifest(
        format_version="0.2.0",
        created="2026-01-01T00:00:00Z",
        creator="t",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(track,),
    )


def test_sealed_zeroes_byte_length() -> None:
    filtered = filter_manifest(_manifest(_descriptor(10)), ObservabilityLevel.SEALED)
    assert filtered.tracks[0].byte_length == 0


def test_sealed_manifest_descriptor_drops_length_channel() -> None:
    """The SEALED manifest descriptor must not differ by plaintext length — two tracks
    differing ONLY in length produce byte-identical descriptors. (This closes the
    manifest-declared length channel; plaintext length is still recoverable from the
    on-disk ciphertext member size — a fundamental AES-GCM length-preservation property
    documented in the threat model, not hidden by observability redaction.)"""
    a = filter_manifest(_manifest(_descriptor(4)), ObservabilityLevel.SEALED)
    b = filter_manifest(_manifest(_descriptor(3)), ObservabilityLevel.SEALED)
    assert a.tracks[0].to_dict() == b.tracks[0].to_dict()


# --- V-F (MED): schema enum and crypto support list must stay in lockstep -----


def test_schema_format_enum_matches_crypto_supported() -> None:
    root = Path(__file__).resolve().parent.parent
    schema = json.loads((root / "data" / "ento_manifest_schema.json").read_text(encoding="utf-8"))
    enum = set(schema["properties"]["format_version"]["enum"])
    assert enum == set(crypto.SUPPORTED_FORMAT_VERSIONS)


# --- Verifier Q4 negative control: cross-track ciphertext swap must fail -------


def test_cross_track_ciphertext_swap_fails_authentication(tmp_path: Path) -> None:
    """Swapping two tracks' ciphertext blobs (keeping manifest ids) must fail GCM:
    each ciphertext is bound to its own track key + (0.3.0) AAD. Proves the
    per-track binding the oracle never explicitly exercised."""
    key = crypto.generate_master_key()
    t_a = PlainTrack(track_id="aaa", track_type="ento:blockchain.proof", payload=b"AAA-PAYLOAD")
    t_b = PlainTrack(track_id="bbb", track_type="ento:blockchain.proof", payload=b"BBB-PAYLOAD")
    blob = container.pack_container_bytes(key, (t_a, t_b), format_version=crypto.FORMAT_VERSION_LATEST)
    zin = zipfile.ZipFile(io.BytesIO(blob))
    blob_a, blob_b = zin.read("tracks/aaa.ento"), zin.read("tracks/bbb.ento")
    man = json.loads(zin.read("manifest.json"))
    # Adversary swaps the blobs AND recomputes the unkeyed ciphertext digests so the
    # digest gate passes — the attack must then be stopped by the per-track key + AAD.
    for t in man["tracks"]:
        t["sha256_ciphertext"] = crypto.sha256_hex(blob_b if t["id"] == "aaa" else blob_a)
    man_obj = manifest_from_json(json.dumps(man))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("manifest.json", manifest_to_json(man_obj))
        z.writestr("tracks/aaa.ento", blob_b)  # swap blobs
        z.writestr("tracks/bbb.ento", blob_a)
        if "proof/chain.json" in zin.namelist():
            z.writestr("proof/chain.json", json.dumps(export_proof(man_obj).to_dict(), indent=2) + "\n")
    p = tmp_path / "swapped.ento.zip"
    p.write_bytes(out.getvalue())
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        container.unpack_container(p, key)
