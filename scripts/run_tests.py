#!/usr/bin/env python3
"""Run the project test gate and persist its structured summary.

Thin orchestrator: argparse + path bootstrap + one delegated call into
``src.test_runner`` (2026-09 scripts audit code motion).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.test_runner import run_test_gate, validate_gate_options  # noqa: E402


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
    try:
        validate_gate_options(args.coverage_floor, args.timeout)
    except ValueError as exc:
        parser.error(str(exc))
    return run_test_gate(
        args.project_root,
        coverage_floor=args.coverage_floor,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    raise SystemExit(main())
