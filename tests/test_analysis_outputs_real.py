"""Analysis pipeline outputs must match registry and validation gates."""

from __future__ import annotations

import json

from src.analysis import run_benchmark_pipeline
from src.figure_registry import FIGURE_SPECS


def test_benchmark_pipeline_produces_real_figures_and_validation(
    fast_benchmark_project: tuple[object, object],
) -> None:
    root, cfg = fast_benchmark_project
    run_benchmark_pipeline(root, config=cfg)

    validation_path = root / "output" / "reports" / "benchmark_validation.json"
    assert validation_path.is_file()
    report = json.loads(validation_path.read_text(encoding="utf-8"))
    assert float(report["tamper_detection_rate"]) == 1.0
    assert report.get("status") == "pass"

    figures_dir = root / "output" / "figures"
    for spec in FIGURE_SPECS:
        png = figures_dir / spec.filename
        assert png.is_file()
        assert png.stat().st_size > 0

    registry_path = figures_dir / "figure_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry) == len(FIGURE_SPECS)
