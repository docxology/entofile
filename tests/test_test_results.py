"""Structured pytest-report parser tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.test_results import parse_test_summary


def _write_reports(root: Path, *, failures: int = 0) -> tuple[Path, Path]:
    junit = root / "junit.xml"
    coverage = root / "coverage.json"
    junit.write_text(
        f'<testsuites><testsuite tests="2" failures="{failures}" errors="0" /></testsuites>',
        encoding="utf-8",
    )
    coverage.write_text(
        json.dumps({"totals": {"percent_covered": 92.345}}),
        encoding="utf-8",
    )
    return junit, coverage


def test_parse_test_summary_accepts_clean_reports(tmp_path: Path) -> None:
    junit, coverage = _write_reports(tmp_path)
    result = parse_test_summary(junit, coverage, 0, source="pytest")
    assert result["all_passed"] is True
    assert result["collected"] == 2
    assert result["project_coverage"] == 92.34
    assert result["source"] == "pytest"


def test_parse_test_summary_rejects_nonzero_exit(tmp_path: Path) -> None:
    junit, coverage = _write_reports(tmp_path)
    result = parse_test_summary(junit, coverage, 1, source="live")
    assert result["all_passed"] is False
    assert "returncode=1" in result["detail"]


def test_parse_test_summary_fails_closed_on_missing_junit(tmp_path: Path) -> None:
    result = parse_test_summary(
        tmp_path / "missing.xml", tmp_path / "missing.json", 0, source="pytest"
    )
    assert result["all_passed"] is False
    assert result["collected"] == 0


def test_parse_test_summary_keeps_test_verdict_when_coverage_is_malformed(
    tmp_path: Path,
) -> None:
    junit, coverage = _write_reports(tmp_path)
    coverage.write_text("not-json", encoding="utf-8")
    result = parse_test_summary(junit, coverage, 0, source="pytest")
    assert result["all_passed"] is True
    assert result["project_coverage"] is None
