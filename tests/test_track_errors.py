"""Tests for track parse errors."""

from __future__ import annotations

import pytest

from src.track import parse_track_bytes


def test_parse_track_bytes_too_short() -> None:
    with pytest.raises(ValueError, match="too short"):
        parse_track_bytes("x", b"\x00" * 10)
