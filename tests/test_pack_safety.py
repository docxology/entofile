"""Packing preserves destinations and stays within reader resource limits."""

from __future__ import annotations

from pathlib import Path

import jsonschema
import pytest

from src.container import pack_container, pack_container_bytes, verify_container
from src.errors import ContainerError
from src.models import PlainTrack


def _tracks(count: int) -> tuple[PlainTrack, ...]:
    return tuple(PlainTrack(f"track-{index}", "ento:blockchain.proof", b"data") for index in range(count))


def test_invalid_manifest_preserves_existing_destination(tmp_path: Path) -> None:
    destination = tmp_path / "existing.zip"
    destination.write_bytes(b"original")
    with pytest.raises(jsonschema.ValidationError):
        pack_container(destination, bytes(32), _tracks(1), creator=123)
    assert destination.read_bytes() == b"original"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["existing.zip"]


def test_pack_refuses_symlink_destination(tmp_path: Path) -> None:
    original = tmp_path / "original"
    original.write_bytes(b"preserve")
    link = tmp_path / "link.zip"
    link.symlink_to(original)
    with pytest.raises(ContainerError, match="symlink"):
        pack_container(link, bytes(32), _tracks(1))
    assert original.read_bytes() == b"preserve"


def test_pack_entry_limit_boundary_roundtrip(tmp_path: Path) -> None:
    destination = tmp_path / "boundary.zip"
    pack_container(destination, bytes(32), _tracks(254))
    assert verify_container(destination, bytes(32))["ok"] is True
    original = destination.read_bytes()
    with pytest.raises(ContainerError, match="too many ZIP entries"):
        pack_container(destination, bytes(32), _tracks(255))
    assert destination.read_bytes() == original
    with pytest.raises(ContainerError, match="too many ZIP entries"):
        pack_container_bytes(bytes(32), _tracks(255))
