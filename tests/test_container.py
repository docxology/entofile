"""Tests for ENTO ZIP container pack/unpack."""

from __future__ import annotations

import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from src.container import container_zip_listing, inspect_container, pack_container, unpack_container
from src.crypto import FORMAT_VERSION, generate_master_key, sha256_hex
from src.errors import ContainerError, IntegrityError
from src.manifest import build_track_descriptor, manifest_to_json
from src.manifest_binding import compute_manifest_binding
from src.models import Manifest, ObservabilityLevel, TrackDescriptor
from src.proof import export_proof
from src.track import encrypt_track
from tests.fixtures import load_fixture_tracks


def test_pack_unpack_round_trip(tmp_path: Path) -> None:
    key = generate_master_key()
    tracks = load_fixture_tracks()
    out = tmp_path / "sample.ento.zip"
    pack_container(out, key, tracks)
    listing = container_zip_listing(out)
    assert "manifest.json" in listing
    assert any(name.startswith("tracks/") for name in listing)
    manifest, payloads = unpack_container(out, key)
    assert len(manifest.tracks) == len(tracks)
    for track in tracks:
        assert payloads[track.track_id] == track.payload


def test_inspect_without_key(tmp_path: Path) -> None:
    key = generate_master_key()
    tracks = load_fixture_tracks()
    out = tmp_path / "sample.ento.zip"
    pack_container(out, key, tracks)
    manifest = inspect_container(out)
    assert manifest.format_version == FORMAT_VERSION == "0.5.0"


@pytest.mark.parametrize("format_version", ["0.2.0", "0.3.0", "0.3.1", "0.4.0"])
def test_pack_rejects_legacy_format(tmp_path: Path, format_version: str) -> None:
    with pytest.raises(ValueError, match="unsupported format_version"):
        pack_container(
            tmp_path / "legacy.ento.zip",
            generate_master_key(),
            load_fixture_tracks(),
            format_version=format_version,
        )


def test_pack_rejects_empty_tracks(tmp_path: Path) -> None:
    with pytest.raises(ContainerError, match="at least one track"):
        pack_container(tmp_path / "empty.ento.zip", generate_master_key(), ())


def test_unpack_rejects_forged_plaintext_hash(tmp_path: Path) -> None:
    """A validly bound producer fixture reaches the plaintext digest control."""
    key = generate_master_key()
    tracks = load_fixture_tracks()
    descriptors: list[TrackDescriptor] = []
    for index, track in enumerate(tracks):
        descriptor = build_track_descriptor(track, b"", observability=3)
        if index == 0:
            descriptor = replace(descriptor, sha256_plaintext="f" * 64)
        descriptors.append(descriptor)
    template = Manifest(
        format_version=FORMAT_VERSION,
        created="2026-01-01T00:00:00Z",
        creator="digest-control",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=tuple(descriptors),
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
            for descriptor in template.tracks
        ),
        manifest_binding=binding,
    )
    tampered = tmp_path / "tampered.ento.zip"
    with zipfile.ZipFile(tampered, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", manifest_to_json(manifest))
        for track_id, encrypted_track in encrypted.items():
            zf.writestr(f"tracks/{track_id}.ento", encrypted_track.to_bytes())
        zf.writestr(
            "proof/chain.json",
            json.dumps(export_proof(manifest).to_dict(), indent=2, sort_keys=True)
            + "\n",
        )
    with pytest.raises(IntegrityError, match="plaintext digest mismatch"):
        unpack_container(tampered, key)
