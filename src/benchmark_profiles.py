"""Optional benchmark profile runner for non-release stress sweeps."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .benchmarks import run_all_benchmarks, write_benchmark_csv, write_validation_report
from .experiment_config import ExperimentConfig, load_experiment_config
from .manuscript_variables import benchmark_rows_per_repetition
from .telemetry import write_json


def run_benchmark_profile(
    project_root: Path,
    *,
    config_path: Path,
    output_dir: Path,
) -> Path:
    """Run a non-default benchmark profile into an isolated output directory."""
    cfg = load_experiment_config(project_root, config_path=config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = run_all_benchmarks(
        project_root,
        repetitions=cfg.benchmark_repetitions,
        observability_levels=cfg.observability_levels,
        medium_track_bytes=cfg.medium_track_bytes,
        large_track_bytes=cfg.large_track_bytes,
        include_mixed_container=cfg.include_mixed_container,
    )
    csv_path = output_dir / "ento_benchmark_results.csv"
    validation_path = output_dir / "benchmark_validation.json"
    summary_path = output_dir / "profile_summary.json"
    write_benchmark_csv(rows, csv_path)
    write_validation_report(rows, validation_path)
    write_json(
        summary_path,
        benchmark_profile_summary(
            cfg,
            config_path=config_path,
            csv_path=csv_path,
            validation_path=validation_path,
            actual_rows=len(rows),
        ),
    )
    return summary_path


def benchmark_profile_summary(
    cfg: ExperimentConfig,
    *,
    config_path: Path,
    csv_path: Path,
    validation_path: Path,
    actual_rows: int,
) -> dict[str, Any]:
    rows_per_repetition = benchmark_rows_per_repetition(cfg)
    expected_rows = cfg.benchmark_repetitions * rows_per_repetition
    return {
        "ok": actual_rows == expected_rows,
        "config_path": str(config_path),
        "csv_path": str(csv_path),
        "validation_path": str(validation_path),
        "benchmark_repetitions": cfg.benchmark_repetitions,
        "observability_levels": list(cfg.observability_levels),
        "medium_track_bytes": cfg.medium_track_bytes,
        "large_track_bytes": cfg.large_track_bytes,
        "include_mixed_container": cfg.include_mixed_container,
        "rows_per_repetition": rows_per_repetition,
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
    }


def count_csv_rows(csv_path: Path) -> int:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))
