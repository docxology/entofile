"""Tests for fixture loading edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.fixtures import fixtures_dir, load_fixture_tracks


def test_fixtures_dir_resolution() -> None:
    p = fixtures_dir()
    assert p.is_dir()
    assert (p / "eeg.csv").is_file()


def test_load_fixture_tracks_partial_and_missing(tmp_path: Path) -> None:
    # Empty dir with require_all=False raises "no fixtures"
    with pytest.raises(FileNotFoundError, match="no fixtures"):
        load_fixture_tracks(fixtures_path=tmp_path, require_all=False)

    # Empty dir with require_all=True raises "missing fixture files"
    with pytest.raises(FileNotFoundError, match="missing fixture files"):
        load_fixture_tracks(fixtures_path=tmp_path, require_all=True)

    # Allowed when require_all=False and some fixtures present
    (tmp_path / "eeg.csv").write_bytes(b"eeg")
    tracks = load_fixture_tracks(fixtures_path=tmp_path, require_all=False)
    assert len(tracks) == 1
    assert tracks[0].track_id == "eeg"
