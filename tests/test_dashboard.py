"""Tests for dashboard builder."""

from __future__ import annotations

from pathlib import Path

from src.analysis import run_benchmark_pipeline
from src.dashboard import build_dashboard_payload, render_dashboard_html, run_dashboard_build
from src.figure_registry import FIGURE_SPECS


def test_dashboard_build(fast_benchmark_project: tuple[Path, object]) -> None:
    root, cfg = fast_benchmark_project
    run_benchmark_pipeline(root, config=cfg)
    payload = build_dashboard_payload(root)
    assert payload["project"] == "entofile"
    assert payload["figure_count"] == len(FIGURE_SPECS)
    assert payload["benchmark_rows"] > 0
    path = render_dashboard_html(root)
    assert path.exists()
    html = path.read_text(encoding="utf-8")
    assert "Benchmark figures" in html
    assert "data:image/png;base64," in html
    assert run_dashboard_build(root).exists()
