"""Renderer-aware figure layout QA."""

from __future__ import annotations

from pathlib import Path

from src.analysis import run_benchmark_pipeline
from src.figure_qa import (
    compare_figure_pixels,
    pixel_digest,
    text_layout_issues,
    validate_registered_figure_layout,
)
from src.figure_registry import FIGURE_SPECS


def test_registered_figures_have_no_text_layout_collisions(
    fast_benchmark_project: tuple[Path, object],
) -> None:
    root, cfg = fast_benchmark_project
    csv_path = run_benchmark_pipeline(root, config=cfg)
    report = validate_registered_figure_layout(csv_path)
    assert report["ok"] is True, report
    assert report["figure_count"] == len(FIGURE_SPECS)


def test_text_layout_qa_detects_overlap() -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(3, 2), dpi=100)
    try:
        ax.text(0.5, 0.5, "overlap", transform=ax.transAxes)
        ax.text(0.5, 0.5, "overlap", transform=ax.transAxes)
        issues = text_layout_issues(fig)
    finally:
        plt.close(fig)
    assert any(issue["type"] == "overlapping_text" for issue in issues)


def test_pixel_digest_self_consistent(tmp_path: Path) -> None:
    """pixel_digest for the same figure is self-consistent."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    try:
        ax.plot([0, 1], [0, 1], label="self-check")
        ax.legend()
        fig.tight_layout()
        path = tmp_path / "self_check.png"
        fig.savefig(path, dpi=100)
    finally:
        plt.close(fig)
    d1 = pixel_digest(path)
    d2 = pixel_digest(path)
    assert d1["width"] == d2["width"]
    assert d1["digest"] == d2["digest"]
    assert d1["mean_per_channel"] == d2["mean_per_channel"]


def test_compare_figure_pixels_self_match(tmp_path: Path) -> None:
    """compare_figure_pixels passes for the same figure vs itself."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    try:
        ax.bar(["a", "b"], [1, 2])
        fig.tight_layout()
        path = tmp_path / "bar.png"
        fig.savefig(path, dpi=100)
    finally:
        plt.close(fig)
    ref = pixel_digest(path)
    result = compare_figure_pixels(path, ref)
    assert result["ok"] is True, result["drifts"]


def test_compare_figure_pixels_detects_dimension_drift(tmp_path: Path) -> None:
    """compare_figure_pixels detects a dimension change."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_a, ax_a = plt.subplots(figsize=(4, 3), dpi=100)
    try:
        ax_a.plot([0, 1], [0, 1])
        fig_a.tight_layout()
        path_a = tmp_path / "a.png"
        fig_a.savefig(path_a, dpi=100)
    finally:
        plt.close(fig_a)
    ref = pixel_digest(path_a)

    fig_b, ax_b = plt.subplots(figsize=(8, 6), dpi=100)
    try:
        ax_b.plot([0, 1], [0, 1])
        fig_b.tight_layout()
        path_b = tmp_path / "b.png"
        fig_b.savefig(path_b, dpi=100)
    finally:
        plt.close(fig_b)
    result = compare_figure_pixels(path_b, ref, max_dimension_drift_px=0)
    assert result["ok"] is False
    assert "dimensions" in result["drifts"]
