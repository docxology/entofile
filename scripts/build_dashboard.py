#!/usr/bin/env python3
"""Build ENTO dashboard HTML."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import run_dashboard_build  # noqa: E402


def main() -> int:
    path = run_dashboard_build(PROJECT_ROOT)
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
