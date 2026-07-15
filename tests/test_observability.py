"""Tests for observability manifest filtering."""

from __future__ import annotations

import zipfile

import pytest

from src.container import pack_container
from src.crypto import generate_master_key
from src.models import Manifest, ObservabilityLevel, TrackDescriptor
from src.observability import filter_manifest, include_proof_chain
from src.ontology import default_resolution
from tests.fixtures import load_fixture_tracks


def _sample_manifest() -> Manifest:
    track = TrackDescriptor(
        id="eeg",
        type="ento:timeseries.eeg",
        sha256_plaintext="a" * 64,
        sha256_ciphertext="b" * 64,
        byte_length=10,
    )
    return Manifest(
        format_version="0.2.0",
        created="2026-01-01T00:00:00Z",
        creator="test",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(track,),
    )


def test_auditable_passthrough() -> None:
    manifest = _sample_manifest()
    filtered = filter_manifest(manifest, ObservabilityLevel.AUDITABLE)
    assert filtered.tracks[0].sha256_plaintext == "a" * 64


def test_sealed_hides_types_and_hashes() -> None:
    manifest = _sample_manifest()
    filtered = filter_manifest(manifest, ObservabilityLevel.SEALED)
    assert filtered.tracks[0].type == "ento:opaque"
    assert filtered.tracks[0].sha256_plaintext == ""


def test_typed_hides_resolution_and_plaintext_hash() -> None:
    track = TrackDescriptor(
        id="eeg",
        type="ento:timeseries.eeg",
        sha256_plaintext="a" * 64,
        sha256_ciphertext="b" * 64,
        byte_length=10,
        resolution=default_resolution("ento:timeseries.eeg"),
    )
    manifest = Manifest(
        format_version="0.2.0",
        created="2026-01-01T00:00:00Z",
        creator="test",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(track,),
    )
    filtered = filter_manifest(manifest, ObservabilityLevel.TYPED)
    assert filtered.tracks[0].resolution is None
    assert filtered.tracks[0].sha256_plaintext == ""
    assert filtered.tracks[0].type == "ento:timeseries.eeg"


def test_resolved_keeps_resolution() -> None:
    track = TrackDescriptor(
        id="eeg",
        type="ento:timeseries.eeg",
        sha256_plaintext="a" * 64,
        sha256_ciphertext="b" * 64,
        byte_length=10,
        resolution=default_resolution("ento:timeseries.eeg"),
    )
    manifest = Manifest(
        format_version="0.2.0",
        created="2026-01-01T00:00:00Z",
        creator="test",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(track,),
    )
    filtered = filter_manifest(manifest, ObservabilityLevel.RESOLVED)
    assert filtered.tracks[0].resolution is not None
    assert filtered.tracks[0].sha256_plaintext == ""


def test_proof_included_for_typed_and_above() -> None:
    assert include_proof_chain(ObservabilityLevel.SEALED) is False
    assert include_proof_chain(ObservabilityLevel.TYPED) is True


def test_sealed_container_omits_proof_chain(tmp_path) -> None:
    key = generate_master_key()
    tracks = load_fixture_tracks()
    out = tmp_path / "sealed.ento.zip"
    pack_container(
        out,
        key,
        tracks,
        observability_level=ObservabilityLevel.AUDITABLE,
        export_level=ObservabilityLevel.SEALED,
    )
    with zipfile.ZipFile(out, "r") as zf:
        assert "proof/chain.json" not in zf.namelist()


def test_pack_rejects_export_level_above_source_observability(tmp_path) -> None:
    key = generate_master_key()
    tracks = load_fixture_tracks()
    with pytest.raises(ValueError, match="cannot expose more metadata"):
        pack_container(
            tmp_path / "escalated.ento.zip",
            key,
            tracks,
            observability_level=ObservabilityLevel.SEALED,
            export_level=ObservabilityLevel.AUDITABLE,
        )
