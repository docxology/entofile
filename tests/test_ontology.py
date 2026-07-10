"""Tests for track ontology registry."""

from __future__ import annotations

import pytest

from src.models import PlainTrack
from src.ontology import (
    default_resolution,
    get_type_spec,
    registered_types,
    validate_track_resolution,
)


def test_registered_types_non_empty() -> None:
    types = registered_types()
    assert "ento:timeseries.eeg" in types
    assert len(types) >= 4


def test_required_resolution_enforced() -> None:
    track = PlainTrack("eeg", "ento:timeseries.eeg", b"x", resolution=None)
    with pytest.raises(ValueError, match="missing resolution"):
        validate_track_resolution(track)


def test_unknown_type_raises() -> None:
    with pytest.raises(KeyError, match="unknown track type"):
        get_type_spec("ento:unknown")


def test_default_resolution_for_eeg() -> None:
    res = default_resolution("ento:timeseries.eeg")
    assert res is not None
    assert res.hz == 256.0
