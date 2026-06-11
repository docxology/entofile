#!/usr/bin/env python3
"""Thin orchestrator: publication readiness gate for the entofile manuscript release."""

from __future__ import annotations

import argparse
import json
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
    parser.add_argument(
        "--check", action="store_true", help="Exit 1 when blockers remain"
    )
    parser.add_argument(
        "--no-live-tests",
        action="store_true",
        help="Read test_results.json instead of re-running pytest live (display-only; "
        "NOT for certification — the side file is not trusted on the --check path)",
    )
    args = parser.parse_args()

    # The certifying path (--check) re-derives the test/coverage verdict live so a stale
    # or forged test_results.json cannot certify a red project (F1 oracle false-assurance).
    # --no-live-tests opts into the side-file read for a quick display pass only.
    live = args.check and not args.no_live_tests
    result = check_publication_readiness(args.project_root, live_tests=live)
    print(json.dumps(result, indent=2))
    if args.check and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
