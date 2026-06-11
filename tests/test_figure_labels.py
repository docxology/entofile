"""Figure filter descriptions and captions stay aligned with registry."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.benchmark_filters import AUDITABLE_LEVEL
from src.benchmark_io import load_benchmark_csv
from src.experiment_config import VizConfig
from src.figure_plotters import (
    plot_crypto_overhead,
    plot_expansion,
    plot_expansion_heatmap,
    plot_throughput,
    plot_throughput_by_observability,
)
from src.figure_registry import (
    FIGURE_SPECS,
    plot_title,
    spec_by_label,
    spec_filter_description,
)
from src.viz_theme import bind_viz

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "benchmark_minimal.csv"

_PLOTTER_SMOKE: tuple[tuple[str, object], ...] = (
    ("fig:throughput_benchmark", plot_throughput),
    ("fig:expansion_ratio", plot_expansion),
    ("fig:crypto_overhead", plot_crypto_overhead),
    ("fig:throughput_by_observability", plot_throughput_by_observability),
    ("fig:expansion_heatmap", plot_expansion_heatmap),
)


def _has_filter_fields(spec: object) -> bool:
    return bool(
        getattr(spec, "condition_prefix", None)
        or getattr(spec, "observability_level", None)
        or getattr(spec, "track_id", None)
    )


def test_spec_filter_description_uses_registry_fields() -> None:
    spec = spec_by_label("fig:throughput_benchmark")
    desc = spec_filter_description(spec)
    assert f"observability level {AUDITABLE_LEVEL}" in desc
    assert "medium_tracks" in desc


def test_plot_title_includes_filter_phrase() -> None:
    spec = spec_by_label("fig:expansion_ratio")
    title = plot_title("Expansion ratio", spec)
    assert f"observability level {spec.observability_level}" in title


def test_registry_captions_reference_filters_and_csv() -> None:
    for spec in FIGURE_SPECS:
        assert "ento_benchmark_results.csv" in spec.caption
        assert "Filters:" in spec.caption
        assert "legacy" not in spec.caption.lower()
        assert "CTR" not in spec.caption
        assert "0.1.0" not in spec.caption
    throughput = spec_by_label("fig:throughput_benchmark")
    assert f"observability level {AUDITABLE_LEVEL}" in throughput.caption


def test_caption_includes_spec_filter_description_when_filtered() -> None:
    for spec in FIGURE_SPECS:
        if not _has_filter_fields(spec):
            continue
        desc = spec_filter_description(spec)
        assert desc in spec.caption, f"{spec.label}: missing filter phrase {desc!r}"


def test_plotter_titles_include_filter_phrase() -> None:
    bind_viz(VizConfig(dpi=100, figsize=(4.0, 3.0)))
    rows = load_benchmark_csv(_FIXTURE)
    for label, plotter in _PLOTTER_SMOKE:
        spec = spec_by_label(label)
        desc = spec_filter_description(spec)
        _fig, ax = plt.subplots()
        try:
            plotter(rows, ax, spec)
            title = ax.get_title()
        finally:
            plt.close(_fig)
        assert desc in title, f"{label}: title {title!r} missing {desc!r}"
