"""Tests for ENTO security helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.security import safe_output_path, validate_track_id


def test_validate_track_id_accepts_fixture_ids() -> None:
    for track_id in ("eeg", "vcf", "spectrogram", "track.v1"):
        validate_track_id(track_id)


@pytest.mark.parametrize(
    "track_id",
    ["../escape", "eeg/extra", "..", "UPPER", "has space", ""],
)
def test_validate_track_id_rejects_unsafe(track_id: str) -> None:
    with pytest.raises(ValueError, match="invalid track id"):
        validate_track_id(track_id)


def test_safe_output_path_stays_under_output_dir(tmp_path: Path) -> None:
    out = safe_output_path(tmp_path / "out", "eeg")
    assert out.parent.resolve() == (tmp_path / "out").resolve()
