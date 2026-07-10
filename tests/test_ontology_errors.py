"""Tests for ontology validation branches."""

from __future__ import annotations

import pytest

from src.models import PlainTrack, ResolutionDescriptor
from src.ontology import validate_track_resolution


def test_missing_resolution_keys() -> None:
    track = PlainTrack(
        "s",
        "ento:spectrogram",
        b"x",
        ResolutionDescriptor(hz=1.0),
    )
    with pytest.raises(ValueError, match="missing resolution"):
        validate_track_resolution(track)
