"""Tests for benchmark CSV I/O."""

from __future__ import annotations

from pathlib import Path

from src.benchmark_io import benchmark_csv_path, load_benchmark_csv


def test_load_benchmark_csv_missing_returns_empty(tmp_path: Path) -> None:
    assert load_benchmark_csv(tmp_path / "missing.csv") == []


def test_benchmark_csv_path_under_output_data() -> None:
    root = Path(__file__).resolve().parent.parent
    path = benchmark_csv_path(root)
    assert path == root / "output" / "data" / "ento_benchmark_results.csv"


def test_load_benchmark_csv_reads_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "bench.csv"
    csv_path.write_text(
        "condition,track_id,tamper_detected\nsmall_tracks_r0,eeg,True\n",
        encoding="utf-8",
    )
    rows = load_benchmark_csv(csv_path)
    assert len(rows) == 1
    assert rows[0]["track_id"] == "eeg"
