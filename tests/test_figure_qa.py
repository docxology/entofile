"""Renderer-aware figure layout QA."""

from __future__ import annotations

from pathlib import Path

from src.analysis import run_benchmark_pipeline
from src.figure_qa import text_layout_issues, validate_registered_figure_layout
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
