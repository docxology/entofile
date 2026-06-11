"""Tests for export_level zero (SEALED) handling."""

from __future__ import annotations

import zipfile
from pathlib import Path

from src.container import pack_container
from src.crypto import generate_master_key
from src.models import ObservabilityLevel
from tests.fixtures import load_fixture_tracks


def test_sealed_export_level_zero(tmp_path: Path) -> None:
    key = generate_master_key()
    out = tmp_path / "sealed.ento.zip"
    pack_container(
        out,
        key,
        load_fixture_tracks(),
        observability_level=ObservabilityLevel.AUDITABLE,
        export_level=ObservabilityLevel.SEALED,
    )
    with zipfile.ZipFile(out, "r") as zf:
        assert "proof/chain.json" not in zf.namelist()
