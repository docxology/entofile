"""Shared benchmark CSV row filters for figures and manuscript variables."""

from __future__ import annotations

AUDITABLE_LEVEL = "3"
MEDIUM_TRACK_PREFIX = "medium_tracks"
SMALL_TRACKS_R0_PREFIX = "small_tracks_r0"
OBSERVABILITY_FIGURE_TRACK = "eeg"
TAMPER_DETECTED_TRUE = "True"


def is_tamper_detected(row: dict[str, str]) -> bool:
    """Return whether a benchmark row recorded successful tamper detection."""
    return row.get("tamper_detected") == TAMPER_DETECTED_TRUE


def filter_rows(
    rows: list[dict[str, str]],
    *,
    condition_prefix: str | None = None,
    observability_level: str | None = None,
    track_id: str | None = None,
) -> list[dict[str, str]]:
    filtered = rows
    if condition_prefix is not None:
        filtered = [r for r in filtered if r["condition"].startswith(condition_prefix)]
    if observability_level is not None:
        filtered = [r for r in filtered if r["observability_level"] == observability_level]
    if track_id is not None:
        filtered = [r for r in filtered if r["track_id"] == track_id]
    return filtered
