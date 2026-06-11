#!/usr/bin/env python3
"""Run a non-default benchmark profile without overwriting release outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark_profiles import run_benchmark_profile  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "benchmark_expanded.yaml",
        help="Profile YAML file with an experiment section",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "benchmark_profiles" / "expanded",
        help="Directory for profile CSV, validation report, and summary",
    )
    args = parser.parse_args()
    summary_path = run_benchmark_profile(
        PROJECT_ROOT, config_path=args.config, output_dir=args.output_dir
    )
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
