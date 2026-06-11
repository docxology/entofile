#!/usr/bin/env python3
"""Generate API docs for entofile."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.documentation import run_api_doc_generation  # noqa: E402


def main() -> int:
    path = run_api_doc_generation(PROJECT_ROOT)
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
