#!/usr/bin/env python3
"""Build the local ENTO release manifest and checksum list."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.release_bundle import build_release_bundle  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Exit zero even if the manifest reports missing required artifacts",
    )
    args = parser.parse_args()
    manifest_path = build_release_bundle(args.project_root, output_dir=args.output_dir)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(manifest_path)
    return 0 if payload["ok"] or args.allow_missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
