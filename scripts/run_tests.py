#!/usr/bin/env python3
"""Run the project test gate and persist its structured summary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.test_results import parse_test_summary  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run entofile tests with coverage")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--coverage-floor",
        type=float,
        default=90.0,
        help="Minimum project coverage percentage (default: 90)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Pytest timeout in seconds (default: 600)",
    )
    args = parser.parse_args()
    if not 0.0 <= args.coverage_floor <= 100.0:
        parser.error("--coverage-floor must be between 0 and 100")
    if args.timeout <= 0.0:
        parser.error("--timeout must be positive")

    root = args.project_root.resolve()
    report_path = root / "output" / "reports" / "test_results.json"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        junit_path = temp / "junit.xml"
        coverage_path = temp / "coverage.json"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            f"--junitxml={junit_path}",
            "--cov=src",
            f"--cov-fail-under={args.coverage_floor:g}",
            f"--cov-report=json:{coverage_path}",
            "-q",
        ]
        try:
            process = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=args.timeout,
                check=False,
            )
            summary = parse_test_summary(
                junit_path,
                coverage_path,
                process.returncode,
                source="pytest",
            )
            returncode = process.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            summary = {
                "all_passed": False,
                "project_coverage": None,
                "collected": 0,
                "source": "pytest",
                "detail": f"test subprocess failed: {exc}",
            }
            returncode = 124

    report = {
        "summary": summary,
        "coverage_floor": args.coverage_floor,
        "command": command,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
