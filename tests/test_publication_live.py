"""F1 oracle-false-assurance: the certifying path must RE-DERIVE tests, not trust a side file.

These bind the live-rerun fix: a forged/stale test_results.json cannot certify a red
project, fail-closed on no-tests, and the recursion guard prevents nested subprocess
re-entry. The guard is exercised directly; only the positive subprocess test is
excluded from a guarded child run. No mocks — uses real temp projects and subprocesses.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.publication import (
    _LIVE_RUN_ENV,
    _live_test_command,
    _output_tail,
    _run_live_test_summary,
    check_publication_readiness,
)

# Recursion guard: when this test module runs INSIDE a live publication run, skip the
# tests that would spawn another nested pytest (cost + recursion). The guard env is set
# by _run_live_test_summary for its child process.
_INSIDE_LIVE_RUN = bool(os.environ.get(_LIVE_RUN_ENV))


@contextmanager
def _live_run_environment(value: str | None) -> Iterator[None]:
    previous = os.environ.get(_LIVE_RUN_ENV)
    if value is None:
        os.environ.pop(_LIVE_RUN_ENV, None)
    else:
        os.environ[_LIVE_RUN_ENV] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(_LIVE_RUN_ENV, None)
        else:
            os.environ[_LIVE_RUN_ENV] = previous


def _forged_green_project(root: Path) -> None:
    (root / "output" / "reports").mkdir(parents=True)
    (root / "output" / "reports" / "test_results.json").write_text(
        json.dumps({"summary": {"all_passed": True, "project_coverage": 99.0}})
    )


def test_live_command_clears_pytest_cache(tmp_path: Path) -> None:
    command = _live_test_command(tmp_path / "junit.xml", tmp_path / "coverage.json")
    assert "--cache-clear" in command


def test_audit_rejects_invalid_timeout(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parent.parent / "scripts" / "audit_publication_readiness.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--project-root",
            str(tmp_path),
            "--check",
            "--live-test-timeout",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert completed.returncode == 2
    assert "--live-test-timeout must be a positive finite number" in completed.stderr


def test_live_output_tail_is_bounded() -> None:
    output = _output_tail("x" * 2500, limit=100)
    assert output.startswith("[truncated 2400 characters]")
    assert len(output) == len("[truncated 2400 characters] ") + 100


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


def test_live_summary_refuses_recursion_when_guard_set(tmp_path: Path) -> None:
    """When the recursion-guard env is already set, the live runner refuses (fail-closed)
    instead of spawning a nested pytest."""
    with _live_run_environment("1"):
        summary = _run_live_test_summary(tmp_path)
    assert summary["all_passed"] is False
    assert "recursion guard" in summary["detail"]


def test_live_summary_passes_on_a_real_green_temp_project(tmp_path: Path) -> None:
    """A minimal real temp project with a passing test + a covered module must yield
    all_passed True and a numeric coverage — proves the parser binds real success,
    not just fail-closed on everything."""
    # This is an isolated temp project, so it is safe to exercise the subprocess
    # path even when the enclosing certifying suite has the recursion guard set.
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
    with _live_run_environment(None):
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


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_live_summary_kills_timed_out_process_group(tmp_path: Path) -> None:
    """A timeout must terminate pytest and its descendants within bounded cleanup."""
    from tests.test_run_tests_runner import _HANGING_TEST, _assert_process_gone

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_slow.py").write_text(_HANGING_TEST)
    with _live_run_environment(None):
        summary = _run_live_test_summary(tmp_path, timeout=5.0)
    assert summary["all_passed"] is False
    assert "subprocess failed" in summary["detail"]
    _assert_process_gone(int((tmp_path / "descendant.pid").read_text()))


@pytest.mark.skipif(
    _INSIDE_LIVE_RUN, reason="side-file fallback is bypassed inside a live certifying run"
)
def test_sdk_validation_report_is_accepted_by_evidence_fallback(tmp_path: Path) -> None:
    from src.publication import _evidence_issues

    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "validation_report.json").write_text(
        json.dumps(
            {
                "summary": {"all_passed": True, "failed": 0},
                "checks": {"PDF validation": True, "Markdown validation": True},
                "figure_issues": [],
                "output_statistics": {"evidence_issues": []},
            }
        )
    )
    issues, source = _evidence_issues(tmp_path)
    assert source == "side-file"
    assert issues == []


@pytest.mark.skipif(
    _INSIDE_LIVE_RUN, reason="side-file fallback is bypassed inside a live certifying run"
)
def test_failed_sdk_report_is_an_evidence_issue(tmp_path: Path) -> None:
    from src.publication import _evidence_issues

    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "validation_report.json").write_text(
        json.dumps(
            {
                "summary": {"all_passed": False, "failed": 1},
                "checks": {"PDF validation": False},
                "figure_issues": ["broken figure"],
            }
        )
    )
    issues, source = _evidence_issues(tmp_path)
    assert source == "side-file"
    assert "broken figure" in issues


@pytest.mark.skipif(
    _INSIDE_LIVE_RUN, reason="side-file fallback is bypassed inside a live certifying run"
)
def test_failed_standalone_report_is_an_evidence_issue(tmp_path: Path) -> None:
    from src.publication import _evidence_issues

    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "validation_report.json").write_text(
        json.dumps({"ok": False, "issues": ["No manuscript markdown files found"]})
    )
    issues, source = _evidence_issues(tmp_path)
    assert source == ("live" if _INSIDE_LIVE_RUN else "side-file")
    assert "No manuscript markdown files found" in issues


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
