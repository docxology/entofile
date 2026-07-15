"""Black-box process lifecycle tests for scripts/run_tests.py."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNNER = PROJECT_ROOT / "scripts" / "run_tests.py"


def _write_temp_project(root: Path, test_source: str) -> None:
    (root / "src").mkdir(parents=True)
    (root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "sample.py").write_text(
        "def identity(value):\n    return value\n", encoding="utf-8"
    )
    (root / "tests").mkdir()
    (root / "tests" / "test_sample.py").write_text(test_source, encoding="utf-8")


def _runner_command(root: Path, *, timeout: float) -> list[str]:
    return [
        sys.executable,
        str(RUNNER),
        "--project-root",
        str(root),
        "--coverage-floor",
        "0",
        "--timeout",
        str(timeout),
    ]


def _report(root: Path) -> dict[str, object]:
    path = root / "output" / "reports" / "test_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _wait_for_file(path: Path, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if path.is_file():
            return
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=2.0)
            pytest.fail(
                f"runner exited before creating {path.name}: "
                f"returncode={process.returncode} stdout={stdout!r} stderr={stderr!r}"
            )
        time.sleep(0.02)
    pytest.fail(f"runner did not create {path.name} within 10 seconds")


def _assert_process_gone(pid: int) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.02)
    pytest.fail(f"descendant process {pid} survived runner cleanup")


_HANGING_TEST = """\
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def test_hangs_after_forging_reports(capsys):
    subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os, signal, time\\n"
            "from pathlib import Path\\n"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\\n"
            "Path('descendant.pid').write_text(str(os.getpid()), encoding='utf-8')\\n"
            "time.sleep(60)\\n",
        ]
    )
    deadline = time.monotonic() + 5
    while not Path("descendant.pid").is_file():
        if time.monotonic() >= deadline:
            raise RuntimeError("descendant did not become ready")
        time.sleep(0.01)
    for argument in sys.argv:
        if argument.startswith("--junitxml="):
            Path(argument.split("=", 1)[1]).write_text(
                '<testsuites><testsuite tests="1" failures="0" errors="0" /></testsuites>',
                encoding="utf-8",
            )
        if argument.startswith("--cov-report=json:"):
            Path(argument.split(":", 1)[1]).write_text(
                json.dumps({"totals": {"percent_covered": 100.0}}),
                encoding="utf-8",
            )
    with capsys.disabled():
        print("X" * 2500 + "RUNNER_DIAGNOSTIC_MARKER", flush=True)
    time.sleep(60)
"""


def test_runner_preserves_success_json_contract(tmp_path: Path) -> None:
    _write_temp_project(
        tmp_path,
        "from src.sample import identity\n\n\ndef test_identity():\n"
        "    assert identity('ento') == 'ento'\n",
    )

    completed = subprocess.run(
        _runner_command(tmp_path, timeout=10.0),
        capture_output=True,
        text=True,
        timeout=15.0,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    stdout_report = json.loads(completed.stdout)
    disk_report = _report(tmp_path)
    assert stdout_report == disk_report
    assert set(disk_report) == {"command", "coverage_floor", "summary"}
    summary = disk_report["summary"]
    assert isinstance(summary, dict)
    assert set(summary) == {
        "all_passed",
        "collected",
        "detail",
        "project_coverage",
        "source",
    }
    assert summary["all_passed"] is True
    assert summary["collected"] == 1
    assert summary["source"] == "pytest"


def test_runner_launch_failure_writes_fail_closed_report(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing-project"

    completed = subprocess.run(
        _runner_command(missing_root, timeout=10.0),
        capture_output=True,
        text=True,
        timeout=15.0,
        check=False,
    )

    assert completed.returncode == 124, completed.stderr
    report = _report(missing_root)
    assert json.loads(completed.stdout) == report
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["all_passed"] is False
    assert summary["project_coverage"] is None
    assert summary["collected"] == 0
    assert summary["source"] == "pytest"
    assert "pytest subprocess failed to start: FileNotFoundError" in str(
        summary["detail"]
    )


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_runner_timeout_kills_group_and_ignores_forged_reports(tmp_path: Path) -> None:
    _write_temp_project(tmp_path, _HANGING_TEST)
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True)
    reports.joinpath("test_results.json").write_text(
        json.dumps(
            {
                "summary": {
                    "all_passed": True,
                    "project_coverage": 100.0,
                    "collected": 999,
                    "source": "stale-side-file",
                    "detail": "forged green result",
                }
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        _runner_command(tmp_path, timeout=5.0),
        capture_output=True,
        text=True,
        timeout=15.0,
        check=False,
    )

    assert completed.returncode == 124, completed.stderr
    report = _report(tmp_path)
    assert json.loads(completed.stdout) == report
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["all_passed"] is False
    assert summary["project_coverage"] is None
    assert summary["collected"] == 0
    assert summary["source"] == "pytest"
    detail = str(summary["detail"])
    assert "pytest timed out after 5 seconds" in detail
    assert "pytest process group" in detail
    assert "SIGKILL" in detail
    assert "[truncated" in detail
    assert "RUNNER_DIAGNOSTIC_MARKER" in detail
    assert "forged green result" not in detail
    _assert_process_gone(int(tmp_path.joinpath("descendant.pid").read_text()))


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_runner_sigint_kills_group_and_writes_diagnostics(tmp_path: Path) -> None:
    _write_temp_project(tmp_path, _HANGING_TEST)
    process = subprocess.Popen(
        _runner_command(tmp_path, timeout=30.0),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    _wait_for_file(tmp_path / "descendant.pid", process)

    os.kill(process.pid, signal.SIGINT)
    stdout, stderr = process.communicate(timeout=10.0)

    assert process.returncode == 130, stderr
    report = _report(tmp_path)
    assert json.loads(stdout) == report
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["all_passed"] is False
    assert summary["project_coverage"] is None
    assert summary["collected"] == 0
    detail = str(summary["detail"])
    assert "pytest interrupted by SIGINT" in detail
    assert "pytest process group" in detail
    assert "SIGKILL" in detail
    assert "[truncated" in detail
    assert "RUNNER_DIAGNOSTIC_MARKER" in detail
    _assert_process_gone(int(tmp_path.joinpath("descendant.pid").read_text()))
