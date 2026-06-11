"""Shared fixture loaders for tests."""

from __future__ import annotations

from pathlib import Path

from src.fixtures import load_fixture_tracks as _load_fixture_tracks


def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


def load_fixture_tracks() -> tuple:
    return _load_fixture_tracks(Path(__file__).resolve().parent.parent, require_all=True)
