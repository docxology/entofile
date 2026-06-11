#!/usr/bin/env python3
"""Run renderer-aware text layout QA for registered figures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.figure_qa import validate_registered_figure_layout  # noqa: E402
from src.telemetry import write_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=PROJECT_ROOT / "output" / "data" / "ento_benchmark_results.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=PROJECT_ROOT / "output" / "reports" / "figure_layout_report.json",
    )
    args = parser.parse_args()
    report = validate_registered_figure_layout(args.csv)
    write_json(args.report, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
