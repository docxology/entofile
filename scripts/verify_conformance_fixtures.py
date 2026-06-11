#!/usr/bin/env python3
"""Verify deterministic ENTO conformance fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.conformance import (  # noqa: E402
    generate_conformance_fixtures,
    verify_conformance_fixtures,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "conformance",
        help="Directory containing conformance_manifest.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=PROJECT_ROOT / "output" / "reports" / "conformance_report.json",
        help="JSON report path",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate fixtures before verifying them",
    )
    args = parser.parse_args()

    if args.generate:
        generate_conformance_fixtures(args.fixture_dir)
    report = verify_conformance_fixtures(args.fixture_dir, report_path=args.report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
