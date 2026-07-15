"""F1 oracle-false-assurance: the certifying path must RE-DERIVE tests, not trust a side file.

These bind the live-rerun fix: a forged/stale test_results.json cannot certify a red
project, fail-closed on no-tests, and the recursion guard prevents nested subprocess
re-entry. The guard is exercised directly; only the positive subprocess test is
excluded from a guarded child run. No mocks — uses real temp projects and subprocesses.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.publication import (
    _LIVE_RUN_ENV,
    _run_live_test_summary,
    check_publication_readiness,
)

# Recursion guard: when this test module runs INSIDE a live publication run, skip the
# tests that would spawn another nested pytest (cost + recursion). The guard env is set
# by _run_live_test_summary for its child process.
_INSIDE_LIVE_RUN = bool(os.environ.get(_LIVE_RUN_ENV))


def _forged_green_project(root: Path) -> None:
    (root / "output" / "reports").mkdir(parents=True)
    (root / "output" / "reports" / "test_results.json").write_text(
        json.dumps({"summary": {"all_passed": True, "project_coverage": 99.0}})
    )


def test_forged_side_file_does_not_certify_under_live(tmp_path: Path) -> None:
    """A hand-written green test_results.json must NOT make the live certifying path pass
    when there are no real tests to run (the F1 false-assurance scenario)."""
    _forged_green_project(tmp_path)
    result = check_publication_readiness(tmp_path, live_tests=True)
    assert result["tests_source"] == "live"
    assert result["checks"]["tests_passed"] is False
    assert result["ok"] is False


def test_side_file_path_is_labelled_not_certified(tmp_path: Path) -> None:
    """The display path reads the side file but labels its source so it cannot be
    mistaken for certification (no live subprocess, safe inside a live run)."""
    _forged_green_project(tmp_path)
    result = check_publication_readiness(tmp_path, live_tests=False)
    assert result["tests_source"] == "side-file"
    # It does read the (forged) side file — that's why it must be labelled, never
    # used as the certifying path.
    assert result["checks"]["tests_passed"] is True


def test_live_summary_fail_closed_on_no_tests(tmp_path: Path) -> None:
    """A project with no tests/ dir must report all_passed False + collected 0
    (pytest exit-5/usage must never read as a pass)."""
    summary = _run_live_test_summary(tmp_path)
    assert summary["all_passed"] is False
    assert summary["collected"] == 0
    assert summary["source"] == "live"


def test_live_summary_refuses_recursion_when_guard_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the recursion-guard env is already set, the live runner refuses (fail-closed)
    instead of spawning a nested pytest."""
    monkeypatch.setenv(_LIVE_RUN_ENV, "1")
    summary = _run_live_test_summary(tmp_path)
    assert summary["all_passed"] is False
    assert "recursion guard" in summary["detail"]


@pytest.mark.skipif(
    _INSIDE_LIVE_RUN, reason="recursion guard: do not spawn nested live pytest"
)
def test_live_summary_passes_on_a_real_green_temp_project(tmp_path: Path) -> None:
    """A minimal real temp project with a passing test + a covered module must yield
    all_passed True and a numeric coverage — proves the parser binds real success,
    not just fail-closed on everything."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("")
    (tmp_path / "src" / "mod.py").write_text("def add(a, b):\n    return a + b\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_mod.py").write_text(
        "from src.mod import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n"
    )
    (tmp_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\npythonpath = ['.']\n"
    )
    summary = _run_live_test_summary(tmp_path)
    assert summary["all_passed"] is True, summary
    assert summary["collected"] >= 1
    assert isinstance(summary["project_coverage"], float)


def test_live_summary_fails_on_a_real_failing_temp_project(tmp_path: Path) -> None:
    """Negative control: a temp project with a FAILING test must yield all_passed False."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_bad.py").write_text(
        "def test_bad():\n    assert False\n"
    )
    summary = _run_live_test_summary(tmp_path)
    assert summary["all_passed"] is False
    if _INSIDE_LIVE_RUN:
        assert summary["collected"] == 0
    else:
        assert summary["collected"] >= 1


@pytest.mark.skipif(
    _INSIDE_LIVE_RUN, reason="recursion guard: do not spawn nested live pytest"
)
def test_live_summary_kills_timed_out_process_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A timeout must terminate pytest descendants instead of hanging on open pipes."""
    from src import publication

    monkeypatch.setattr(publication, "_LIVE_RUN_TIMEOUT_S", 0.05)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_slow.py").write_text(
        "import time\n\n\ndef test_slow():\n    time.sleep(10)\n"
    )
    summary = _run_live_test_summary(tmp_path)
    assert summary["all_passed"] is False
    assert "subprocess failed" in summary["detail"]


def test_certifying_path_runs_live_conformance(tmp_path: Path) -> None:
    """The certifying path re-derives conformance by regenerating + verifying the
    deterministic fixture set this call — a forged conformance_report.json plays
    no part. The check key must be present (and green: fixtures are self-
    contained constants, independent of the broken tmp project)."""
    _forged_green_project(tmp_path)
    # A forged green conformance side file must be irrelevant to the verdict path.
    (tmp_path / "output" / "reports" / "conformance_report.json").write_text(
        json.dumps({"ok": True, "case_count": 999})
    )
    result = check_publication_readiness(tmp_path, live_tests=True)
    assert result["checks"]["conformance_live"] is True
    # Display path must NOT claim live conformance ran.
    display = check_publication_readiness(tmp_path, live_tests=False)
    assert "conformance_live" not in display["checks"]
