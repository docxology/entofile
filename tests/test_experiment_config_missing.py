"""Tests for experiment config missing file."""

from __future__ import annotations

from pathlib import Path

from src.experiment_config import load_experiment_config


def test_missing_config_uses_defaults(tmp_path: Path) -> None:
    cfg = load_experiment_config(tmp_path)
    assert cfg.benchmark_repetitions == 3
