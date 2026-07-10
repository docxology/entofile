"""Tests for experiment config loader."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.experiment_config import ExperimentConfig, load_experiment_config
from src.manuscript_variables import benchmark_rows_per_repetition


def test_load_experiment_config_defaults() -> None:
    root = Path(__file__).resolve().parent.parent
    cfg = load_experiment_config(root)
    assert cfg.benchmark_repetitions >= 1
    assert len(cfg.observability_levels) == 4
    assert cfg.viz.dpi == 300


def test_release_config_uses_150_repetitions_and_2400_rows() -> None:
    root = Path(__file__).resolve().parent.parent
    cfg = load_experiment_config(root)
    assert cfg.benchmark_repetitions == 150
    assert benchmark_rows_per_repetition(cfg) == 16
    assert cfg.benchmark_repetitions * benchmark_rows_per_repetition(cfg) == 2400
    assert cfg.large_track_bytes == 0
    assert cfg.include_mixed_container is False


def test_optional_benchmark_dimensions_are_opt_in() -> None:
    cfg = ExperimentConfig(
        benchmark_repetitions=150,
        large_track_bytes=131072,
        include_mixed_container=True,
    )
    assert benchmark_rows_per_repetition(cfg) == 36


def test_load_experiment_config_viz_from_yaml(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text(
        yaml.dump(
            {
                "experiment": {
                    "benchmark_repetitions": 2,
                    "observability_levels": [0, 3],
                    "medium_track_bytes": 4096,
                    "viz": {
                        "dpi": 150,
                        "figsize": [6, 4],
                        "figure_width_percent": 85,
                        "font_size": 9,
                        "grid_alpha": 0.2,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    cfg = load_experiment_config(tmp_path)
    assert cfg.benchmark_repetitions == 2
    assert cfg.observability_levels == (0, 3)
    assert cfg.medium_track_bytes == 4096
    assert cfg.viz.dpi == 150
    assert cfg.viz.figsize == (6.0, 4.0)
    assert cfg.viz.figure_width_percent == 85
    assert cfg.viz.font_size == 9.0
    assert cfg.viz.grid_alpha == 0.2
