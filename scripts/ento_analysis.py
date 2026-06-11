#!/usr/bin/env python3
"""Thin orchestrator for ENTO benchmark analysis."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for path in (PROJECT_ROOT, PROJECT_ROOT.parent.parent):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from src.analysis import main  # noqa: E402

if __name__ == "__main__":
    main()
