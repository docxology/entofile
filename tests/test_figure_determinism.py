"""Determinism contract for code-derived figures.

A figure marked ``data_derived=True`` plots only byte-count / ratio columns of the
benchmark CSV and must regenerate **byte-identically** from a fixed CSV — no time,
no RNG, no global-state leakage between figures. Figures marked
``data_derived=False`` plot wall-clock timing columns that legitimately vary across
re-measurement, so they are exempt from the cross-run byte-identity assertion.

This guards the documented blind spot that per-plotter smoke tests miss inter-figure
global-state leakage: each data figure is rendered twice (with an unrelated figure
rendered in between) and compared byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from src import figures
from src.experiment_config import VizConfig
from src.figure_registry import FIGURE_SPECS, spec_by_label
from src.viz_theme import bind_viz

_FIXTURE_CSV = Path(__file__).resolve().parent / "fixtures" / "benchmark_minimal.csv"

# The only figures whose pixels depend on wall-clock timing columns.
_EXPECTED_TIMING_FIGURES = {
    "fig:throughput_benchmark",
    "fig:unpack_latency",
    "fig:throughput_by_observability",
    "fig:observability_throughput_tradeoff",
    "fig:benchmark_overview",
    "fig:throughput_dispersion",
    "fig:determinism_cv",
}


def _generator_for(label: str):
    spec = spec_by_label(label)
    return getattr(figures, spec.generator_name)


def test_data_derived_classification_matches_expected() -> None:
    """The registry's data_derived flags must match the known timing-figure set,
    so the determinism contract can't silently drift."""
    timing = {s.label for s in FIGURE_SPECS if not s.data_derived}
    assert timing == _EXPECTED_TIMING_FIGURES, f"data_derived split drifted: {timing}"


def test_data_derived_figures_regenerate_byte_identically(tmp_path: Path) -> None:
    """Every data_derived figure is byte-identical across two separate renders from
    the same fixed CSV, even with an unrelated figure rendered in between
    (catches global-state leakage)."""
    bind_viz(VizConfig(dpi=100, figsize=(5.0, 3.0)))
    try:
        data_specs = [s for s in FIGURE_SPECS if s.data_derived]
        assert data_specs, "expected at least one data-derived figure"
        for spec in data_specs:
            gen = _generator_for(spec.label)
            out_a = tmp_path / f"{spec.label.removeprefix('fig:')}_a.png"
            out_b = tmp_path / f"{spec.label.removeprefix('fig:')}_b.png"
            gen(_FIXTURE_CSV, out_a)
            # Render an unrelated figure in between to surface global-state leakage.
            _generator_for("fig:expansion_ratio")(
                _FIXTURE_CSV, tmp_path / "_interleave.png"
            )
            gen(_FIXTURE_CSV, out_b)
            assert out_a.read_bytes() == out_b.read_bytes(), (
                f"{spec.label} is marked data_derived but not byte-stable across renders"
            )
    finally:
        bind_viz(VizConfig())


def test_expansion_law_figure_is_data_derived() -> None:
    """The new expansion-law figure plots ratios only and must be deterministic."""
    assert spec_by_label("fig:expansion_law").data_derived is True


def test_security_figures_are_data_derived() -> None:
    """Release/security diagrams are registry-driven and do not depend on timings."""
    assert spec_by_label("fig:format_ladder").data_derived is True
    assert spec_by_label("fig:security_control_matrix").data_derived is True
