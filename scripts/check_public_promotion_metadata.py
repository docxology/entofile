#!/usr/bin/env python3
"""Check public-promotion metadata consistency."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.public_promotion import check_public_endpoints, check_public_promotion_metadata  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero when any metadata consistency check fails",
    )
    parser.add_argument(
        "--require-public-endpoints",
        action="store_true",
        help="With --check, also require public-release readiness blockers to be clear",
    )
    parser.add_argument(
        "--live-public-endpoints",
        action="store_true",
        help="Perform live HEAD checks for the planned GitHub, Zenodo, and DOI endpoints",
    )
    args = parser.parse_args()
    endpoint_state = check_public_endpoints() if args.live_public_endpoints else None
    report = check_public_promotion_metadata(
        args.project_root, public_endpoint_state=endpoint_state
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not args.check:
        return 0
    if not report["ok"]:
        return 1
    if args.require_public_endpoints and not report["release_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
