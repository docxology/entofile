"""Behavioral controls for the repository's no-test-double policy."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from src.manuscript_variables import _no_mock_status

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNNER = PROJECT_ROOT / "run.sh"
FORBIDDEN_TOKENS = (
    "unittest." + "mock",
    "from unittest import " + "mock",
    "Magic" + "Mock",
    "Async" + "Mock",
    "Property" + "Mock",
    "Mock" + "(",
    "@" + "patch",
    "patch." + "object",
    "mock." + "patch",
    "create_" + "autospec",
    "monkey" + "patch",
    "Monkey" + "Patch",
)
REAL_TEST = "def test_real_execution():\n    assert 2 + 2 == 4\n"


def _write_test(root: Path, source: str) -> None:
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "test_sample.py").write_text(source, encoding="utf-8")


def _copy_shell_gate(root: Path) -> Path:
    script = root / "run.sh"
    shutil.copy2(RUNNER, script)
    return script


def test_source_scanner_accepts_real_test(tmp_path: Path) -> None:
    _write_test(tmp_path, REAL_TEST)
    assert _no_mock_status(tmp_path) == "Clean"


def test_source_scanner_rejects_every_prohibited_form(tmp_path: Path) -> None:
    _write_test(tmp_path, "\n".join(FORBIDDEN_TOKENS))
    result = _no_mock_status(tmp_path)
    for token in FORBIDDEN_TOKENS:
        assert f"tests/test_sample.py:{token}" in result


def test_shell_scanner_has_clean_and_violating_controls(tmp_path: Path) -> None:
    script = _copy_shell_gate(tmp_path)
    _write_test(tmp_path, REAL_TEST)
    clean = subprocess.run(
        ["bash", str(script), "no-mocks"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert clean.returncode == 0, clean.stderr
    assert clean.stdout.strip() == "Clean"

    (tmp_path / "tests" / "test_sample.py").write_text(
        "\n".join(FORBIDDEN_TOKENS), encoding="utf-8"
    )
    rejected = subprocess.run(
        ["bash", str(script), "no-mocks"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert rejected.returncode == 1
    assert "Mock-based tests are prohibited" in rejected.stderr
    for token in FORBIDDEN_TOKENS:
        assert token in rejected.stderr


def test_scanners_reject_empty_test_directory(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    assert _no_mock_status(tmp_path) == "no Python test files"

    script = _copy_shell_gate(tmp_path)
    empty = subprocess.run(
        ["bash", str(script), "no-mocks"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert empty.returncode == 2
    assert empty.stdout.strip() != "Clean"
    assert "no Python test files" in empty.stderr


def test_shell_scanner_propagates_operational_errors(tmp_path: Path) -> None:
    script = _copy_shell_gate(tmp_path)
    missing = subprocess.run(
        ["bash", str(script), "no-mocks"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert missing.returncode == 2
    assert missing.stdout.strip() != "Clean"
