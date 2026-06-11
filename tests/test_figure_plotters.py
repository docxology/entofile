"""Plotter smoke tests on a minimal real benchmark CSV fixture."""

from __future__ import annotations

from pathlib import Path

from src.benchmark_io import load_benchmark_csv
from src.experiment_config import VizConfig
from src.figure_plotters import (
    _sparse_repetition_ticks,
    plot_expansion,
    plot_expansion_heatmap,
    plot_throughput,
    render_to_path,
)
from src.figure_registry import spec_by_label
from src.viz_theme import bind_viz


def _fixture_csv() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "benchmark_minimal.csv"


def test_plotters_write_png_from_fixture(tmp_path: Path) -> None:
    bind_viz(VizConfig(dpi=100, figsize=(4.0, 3.0)))
    rows = load_benchmark_csv(_fixture_csv())
    spec = spec_by_label("fig:throughput_benchmark")
    out = render_to_path(rows, tmp_path / "throughput.png", spec, plot_throughput)
    assert out.is_file()
    assert out.stat().st_size > 500


def test_expansion_heatmap_non_empty_axes(tmp_path: Path) -> None:
    bind_viz(VizConfig(dpi=100, figsize=(5.0, 4.0)))
    rows = load_benchmark_csv(_fixture_csv())
    spec = spec_by_label("fig:expansion_heatmap")
    out = render_to_path(rows, tmp_path / "heatmap.png", spec, plot_expansion_heatmap)
    assert out.is_file()


def test_expansion_bar_from_fixture(tmp_path: Path) -> None:
    bind_viz(VizConfig(dpi=100, figsize=(4.0, 3.0)))
    rows = load_benchmark_csv(_fixture_csv())
    spec = spec_by_label("fig:expansion_ratio")
    out = render_to_path(rows, tmp_path / "expansion.png", spec, plot_expansion)
    assert out.is_file()


def test_sparse_repetition_ticks_stay_readable_for_release_n() -> None:
    ticks = _sparse_repetition_ticks(150)
    assert ticks[0] == 1
    assert ticks[-1] == 150
    assert len(ticks) <= 9
    assert ticks == sorted(set(ticks))
