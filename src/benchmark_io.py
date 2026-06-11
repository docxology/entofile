"""Benchmark CSV I/O shared by figures, dashboard, and manuscript variables."""

from __future__ import annotations

import csv
from pathlib import Path


def benchmark_csv_path(project_root: Path) -> Path:
    """Return the canonical benchmark CSV path under ``output/data/``."""
    return project_root / "output" / "data" / "ento_benchmark_results.csv"


def load_benchmark_csv(path: Path) -> list[dict[str, str]]:
    """Load benchmark rows from ``path``; return an empty list when missing."""
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
