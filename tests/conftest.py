"""Pytest configuration for entofile tests."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.experiment_config import ExperimentConfig, load_experiment_config  # noqa: E402


@pytest.fixture
def project_root() -> Path:
    return Path(ROOT)


@pytest.fixture
def fast_benchmark_project(
    tmp_path: Path, project_root: Path
) -> tuple[Path, ExperimentConfig]:
    """Temporary project root for small-rep pipeline tests.

    The production project config drives the 150-repetition release run. Tests
    still exercise the real pipeline with a 3-repetition override, but write into
    a temp root so test execution never overwrites release benchmark artifacts.
    """
    root = tmp_path / "entofile"
    shutil.copytree(project_root / "data" / "fixtures", root / "data" / "fixtures")
    claim_ledger = project_root / "data" / "claim_ledger.yaml"
    if claim_ledger.is_file():
        (root / "data").mkdir(parents=True, exist_ok=True)
        shutil.copy2(claim_ledger, root / "data" / claim_ledger.name)
    (root / "manuscript").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        project_root / "manuscript" / "config.yaml",
        root / "manuscript" / "config.yaml",
    )
    cfg = replace(load_experiment_config(project_root), benchmark_repetitions=3)
    return root, cfg
