"""Tests for benchmark analysis pipeline."""

from __future__ import annotations

from src.analysis import run_benchmark_pipeline, validate_generated_outputs


def test_run_benchmark_pipeline_writes_csv(
    fast_benchmark_project: tuple[object, object],
) -> None:
    root, cfg = fast_benchmark_project
    csv_path = run_benchmark_pipeline(root, config=cfg)
    assert csv_path.exists()
    assert csv_path.stat().st_size > 0
    result = validate_generated_outputs(root)
    assert result["ok"] is True
    assert result["report"]["status"] == "pass"
    assert result["tamper_detection_rate"] == 1.0
    assert result["figures_ok"] is True
    assert result["registry_ok"] is True
    assert result["registry_provenance_ok"] is True
    assert result["containers_ok"] is True
