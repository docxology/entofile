#!/usr/bin/env python3
"""Thin orchestrator: publication readiness gate for the entofile manuscript release."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for path in (PROJECT_ROOT, PROJECT_ROOT.parent.parent):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from src.publication import check_publication_readiness  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit entofile publication readiness")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root (default: parent of scripts/)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="Exit 1 when blockers remain"
    )
    mode.add_argument(
        "--no-live-tests",
        action="store_true",
        help="Read test_results.json instead of re-running pytest live (display-only; "
        "NOT for certification — the side file is not trusted on the --check path)",
    )
    parser.add_argument(
        "--live-test-timeout",
        type=float,
        default=600.0,
        help="Certifying pytest timeout in seconds (default: 600)",
    )
    args = parser.parse_args()
    if not math.isfinite(args.live_test_timeout) or args.live_test_timeout <= 0:
        parser.error("--live-test-timeout must be a positive finite number")

    # The certifying path (--check) re-derives the test/coverage verdict live so a stale
    # or forged test_results.json cannot certify a red project (F1 oracle false-assurance).
    # --no-live-tests opts into the side-file read for a quick display pass only.
    live = args.check
    result = check_publication_readiness(
        args.project_root,
        live_tests=live,
        live_test_timeout=args.live_test_timeout,
    )
    print(json.dumps(result, indent=2))
    if args.check and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
