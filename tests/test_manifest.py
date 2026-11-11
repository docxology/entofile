"""Tests for manifest schema and validation."""

from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from src.crypto import sha256_hex
from src.errors import ManifestError
from src.manifest import (
    build_track_descriptor,
    manifest_from_json,
    manifest_to_json,
    validate_manifest_dict,
)
from src.manifest_binding import compute_manifest_binding
from src.models import Manifest, ObservabilityLevel, PlainTrack, TrackDescriptor
from src.ontology import default_resolution


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _valid_manifest() -> Manifest:
    template = Manifest(
        format_version="0.5.0",
        created="2026-01-01T00:00:00Z",
        creator="test",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(
            TrackDescriptor(
                id="eeg",
                type="ento:timeseries.eeg",
                sha256_plaintext=sha256_hex(b"payload"),
                sha256_ciphertext=sha256_hex(b"cipher"),
                byte_length=10,
                resolution=default_resolution("ento:timeseries.eeg"),
            ),
        ),
    )
    return replace(
        template, manifest_binding=compute_manifest_binding(template)
    )


def test_schema_accepts_valid_manifest() -> None:
    manifest = _valid_manifest()
    data = manifest.to_dict()
    validate_manifest_dict(data, _project_root())
    roundtrip = manifest_from_json(manifest_to_json(manifest))
    assert roundtrip.tracks[0].type == "ento:timeseries.eeg"


def test_schema_rejects_unknown_version() -> None:
    bad = _valid_manifest().to_dict()
    bad["format_version"] = "9.9.9"
    with pytest.raises(ManifestError, match=r"9.9.9"):
        validate_manifest_dict(bad, _project_root())


@pytest.mark.parametrize("format_version", ["0.2.0", "0.3.0", "0.3.1", "0.4.0"])
def test_schema_rejects_legacy_version(format_version: str) -> None:
    bad = _valid_manifest().to_dict()
    bad["format_version"] = format_version
    with pytest.raises(ManifestError, match=format_version):
        validate_manifest_dict(bad, _project_root())


def test_schema_requires_manifest_binding() -> None:
    bad = _valid_manifest().to_dict()
    del bad["manifest_binding"]
    with pytest.raises(ManifestError, match="manifest_binding"):
        validate_manifest_dict(bad, _project_root())


def test_schema_requires_nonempty_tracks() -> None:
    bad = _valid_manifest().to_dict()
    bad["tracks"] = []
    with pytest.raises(ManifestError):
        validate_manifest_dict(bad, _project_root())


def test_schema_rejects_invalid_hash() -> None:
    bad = _valid_manifest().to_dict()
    bad["tracks"][0]["sha256_plaintext"] = "not-a-hash"
    with pytest.raises(ManifestError, match="not-a-hash"):
        validate_manifest_dict(bad, _project_root())


def test_manifest_from_json_validates_before_coercion() -> None:
    raw = _valid_manifest().to_dict()
    raw["unknown"] = True
    with pytest.raises(ManifestError):
        manifest_from_json(json.dumps(raw))


def test_schema_cache_isolated_by_project_root(tmp_path: Path) -> None:
    custom_data = tmp_path / "data"
    custom_data.mkdir()
    shutil.copy(_project_root() / "data" / "ento_manifest_schema.json", custom_data)
    schema_path = custom_data / "ento_manifest_schema.json"
    custom_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    custom_schema["properties"]["format_version"]["enum"] = ["custom"]
    schema_path.write_text(json.dumps(custom_schema), encoding="utf-8")
    manifest = _valid_manifest().to_dict()
    with pytest.raises(ManifestError):
        validate_manifest_dict(manifest, tmp_path)
    validate_manifest_dict(manifest, _project_root())


def test_build_track_descriptor() -> None:

    plain = PlainTrack("eeg", "ento:timeseries.eeg", b"abc", default_resolution("ento:timeseries.eeg"))
    desc = build_track_descriptor(plain, b"cipher", observability=3)
    assert desc.byte_length == 3
