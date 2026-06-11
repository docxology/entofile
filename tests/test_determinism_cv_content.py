"""Content tests for the determinism-CV figure (RedTeam 2026-05-30 Q3b remediation).

``fig:determinism_cv`` is registered ``data_derived=False``, so it is EXEMPT from the
byte-identity determinism test — that test only proves a figure renders stably, never
that its content is correct. These tests bind the figure's *content*: the metric→class
mapping must agree with the fingerprint's column split, and the computed CV must be
exactly zero for the deterministic columns and strictly positive for the wall-clock
columns. Without them, the figure the manuscript calls a "visual proof" of the split
could paint the deterministic metric as wall-clock noise and every other gate stays green.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.benchmark_stats import (
    DETERMINISTIC_BENCHMARK_COLUMNS,
    VOLATILE_BENCHMARK_COLUMNS,
    summary_stats,
)
from src.experiment_config import VizConfig
from src.figure_plotters import _DETERMINISM_METRICS, plot_determinism_cv
from src.figure_registry import spec_by_label
from src.viz_theme import active_palette, bind_viz

# Two repetitions of the medium-track condition: IDENTICAL deterministic cells,
# DIFFERENT wall-clock cells — the exact shape the figure summarizes.
_REPEATED_ROWS: list[dict[str, str]] = [
    {
        "condition": "medium_tracks_r0",
        "track_id": "medium",
        "track_type": "ento:spectrogram",
        "plaintext_bytes": "65536",
        "ciphertext_bytes": "65568",
        "expansion_ratio": "1.000488",
        "pack_seconds": "0.001400",
        "unpack_seconds": "0.001300",
        "pack_throughput_mib_s": "120.000000",
        "tamper_detected": "True",
        "observability_level": "3",
        "manifest_bytes": "581",
    },
    {
        "condition": "medium_tracks_r1",
        "track_id": "medium",
        "track_type": "ento:spectrogram",
        "plaintext_bytes": "65536",
        "ciphertext_bytes": "65568",
        "expansion_ratio": "1.000488",
        "pack_seconds": "0.001700",
        "unpack_seconds": "0.001600",
        "pack_throughput_mib_s": "110.000000",
        "tamper_detected": "True",
        "observability_level": "3",
        "manifest_bytes": "581",
    },
]


def test_every_plotted_metric_is_classified() -> None:
    classified = set(DETERMINISTIC_BENCHMARK_COLUMNS) | set(VOLATILE_BENCHMARK_COLUMNS)
    for column, _label in _DETERMINISM_METRICS:
        assert column in classified, f"{column!r} is plotted but unclassified"


def test_cv_is_zero_for_deterministic_and_positive_for_volatile() -> None:
    """The figure's headline claim, asserted: deterministic CV == 0, wall-clock CV > 0."""
    saw_deterministic = saw_volatile = False
    for column, _label in _DETERMINISM_METRICS:
        cv = summary_stats([float(r[column]) for r in _REPEATED_ROWS]).cv
        if column in DETERMINISTIC_BENCHMARK_COLUMNS:
            assert cv == 0.0, f"{column} marked deterministic but CV={cv}"
            saw_deterministic = True
        else:
            assert cv > 0.0, f"{column} marked wall-clock but CV={cv} (no dispersion)"
            saw_volatile = True
    assert saw_deterministic and saw_volatile  # both classes are actually exercised


def test_bar_colors_match_the_fingerprint_split() -> None:
    """Render the plotter and assert each bar's color is the class color derived from
    the fingerprint split — so a metric can never be painted in the wrong class."""
    bind_viz(VizConfig(dpi=100, figsize=(8.0, 4.0)))
    try:
        spec = spec_by_label("fig:determinism_cv")
        fig, ax = plt.subplots()
        try:
            plot_determinism_cv(_REPEATED_ROWS, ax, spec)
            deterministic_color = active_palette()[2]
            volatile_color = active_palette()[3]
            bars = [p for p in ax.patches]
            # One bar per plotted metric, in _DETERMINISM_METRICS order.
            plotted = [
                (col, lbl)
                for col, lbl in _DETERMINISM_METRICS
                if any(r.get(col) not in (None, "") for r in _REPEATED_ROWS)
            ]
            assert len(bars) == len(plotted)
            for bar, (column, _label) in zip(bars, plotted, strict=True):
                expected = (
                    deterministic_color
                    if column in DETERMINISTIC_BENCHMARK_COLUMNS
                    else volatile_color
                )
                assert bar.get_facecolor() == _to_rgba(expected), column
        finally:
            plt.close(fig)
    finally:
        bind_viz(VizConfig())


def _to_rgba(color: str) -> tuple[float, float, float, float]:
    from matplotlib.colors import to_rgba

    return to_rgba(color)
