#!/usr/bin/env python3
"""Generate deterministic ENTO conformance fixtures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.conformance import generate_conformance_fixtures  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "conformance",
        help="Directory for generated fixtures and manifest",
    )
    args = parser.parse_args()
    print(generate_conformance_fixtures(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
