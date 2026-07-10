"""Tests for ENTO ZIP container pack/unpack."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from src.container import container_zip_listing, inspect_container, pack_container, unpack_container
from src.crypto import FORMAT_VERSION, generate_master_key
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
    assert manifest.format_version == FORMAT_VERSION == "0.4.0"


def test_unpack_rejects_forged_plaintext_hash(tmp_path: Path) -> None:
    key = generate_master_key()
    tracks = load_fixture_tracks()
    out = tmp_path / "sample.ento.zip"
    pack_container(out, key, tracks)
    tampered = tmp_path / "tampered.ento.zip"
    with zipfile.ZipFile(out, "r") as zin, zipfile.ZipFile(tampered, "w") as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name == "manifest.json":
                manifest = json.loads(data.decode("utf-8"))
                manifest["tracks"][0]["sha256_plaintext"] = "f" * 64
                data = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
            zout.writestr(name, data)
    with pytest.raises(ValueError, match=r"proof chain does not match|plaintext digest mismatch"):
        unpack_container(tampered, key)
