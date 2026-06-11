"""Optional benchmark profile tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.benchmark_profiles import run_benchmark_profile
from src.experiment_config import load_experiment_config
from src.manuscript_variables import benchmark_rows_per_repetition


def test_expanded_benchmark_profile_is_non_default_and_closed_key() -> None:
    root = Path(__file__).resolve().parent.parent
    cfg = load_experiment_config(root, config_path=root / "configs" / "benchmark_expanded.yaml")
    assert cfg.benchmark_repetitions == 30
    assert cfg.large_track_bytes == 1048576
    assert cfg.include_mixed_container is True
    assert benchmark_rows_per_repetition(cfg) == 36


def test_benchmark_profile_runner_isolates_outputs(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    profile = tmp_path / "profile.yaml"
    profile.write_text(
        """
experiment:
  benchmark_repetitions: 1
  observability_levels: [0, 1]
  medium_track_bytes: 4096
  large_track_bytes: 8192
  include_mixed_container: true
  creator: test-profile
""".lstrip(),
        encoding="utf-8",
    )
    summary_path = run_benchmark_profile(
        root, config_path=profile, output_dir=tmp_path / "profile-output"
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["ok"] is True
    assert summary["rows_per_repetition"] == 18
    assert summary["expected_rows"] == summary["actual_rows"] == 18
    assert Path(summary["csv_path"]).is_file()
    assert Path(summary["validation_path"]).is_file()
