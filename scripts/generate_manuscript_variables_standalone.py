#!/usr/bin/env python3
"""Generate manuscript variables JSON for entofile (standalone, no template required).

Unlike ``z_generate_manuscript_variables.py`` which also resolves ``{{TOKEN}}``
injection and writes the resolved manuscript tree (requiring ``infrastructure.rendering``
from the template repository), this script writes only the variables JSON file.

This is sufficient for the release manifest to record the file as present and
for downstream consumers to inspect the measured values.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.manuscript_variables import generate_variables, save_variables  # noqa: E402


def main() -> int:
    out_path = _PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    try:
        variables = generate_variables(
            _PROJECT_ROOT,
            require_analysis_outputs=True,
        )
    except FileNotFoundError as exc:
        sys.stderr.write(
            f"Analysis outputs required: {exc}\n"
            "Run `uv run python scripts/ento_analysis.py` first.\n"
        )
        return 2

    save_variables(variables, out_path)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
