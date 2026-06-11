#!/usr/bin/env python3
"""Thin orchestrator: export CycloneDX SBOM for entofile (optional release gate).

Document shape and version-of-record logic live in ``src/sbom.py`` (tested);
this script only runs ``uv export``, calls the builder, and writes the file.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for path in (PROJECT_ROOT, PROJECT_ROOT.parent.parent):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from src.sbom import build_cyclonedx_skeleton  # noqa: E402


def uv_export_requirements(project_root: Path) -> str:
    result = subprocess.run(
        ["uv", "export", "--no-dev", "--no-hashes"],
        capture_output=True,
        text=True,
        check=True,
        cwd=project_root,
    )
    return result.stdout


def main() -> int:
    reports = PROJECT_ROOT / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    out_path = reports / "sbom.cyclonedx.json"
    requirements = uv_export_requirements(PROJECT_ROOT)
    bom = build_cyclonedx_skeleton(PROJECT_ROOT, requirements)
    out_path.write_text(json.dumps(bom, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
