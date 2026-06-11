"""CycloneDX SBOM skeleton generation for the release evidence bundle.

The SBOM is an optional release gate: ``scripts/export_sbom.py`` is the thin
orchestrator; the document shape and the version-of-record logic live here so
they are unit-testable and cannot drift from the project metadata. The
application component version is read from ``manuscript/config.yaml``
(``paper.version``) — the same release label the public-promotion metadata
checker pins against ``CITATION.cff`` — never hardcoded.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

SBOM_SPEC_VERSION = "1.5"
SBOM_APPLICATION_NAME = "entofile"


def release_label(project_root: Path) -> str:
    """The project release label (``paper.version`` from manuscript config).

    Raises ``ValueError`` when the config or the field is missing — an SBOM
    must never silently fall back to a stale or invented version.
    """
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        raise ValueError(f"manuscript config not found: {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    version = (
        ((config.get("paper") or {}).get("version"))
        if isinstance(config, dict)
        else None
    )
    if not version:
        raise ValueError("paper.version missing from manuscript/config.yaml")
    return str(version)


def parse_requirement_names(requirements_text: str) -> list[str]:
    """Distinct dependency names from ``uv export`` requirements text, in order."""
    names: list[str] = []
    for line in requirements_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        name = stripped.split("==")[0].split("[")[0].strip()
        if name and name not in names:
            names.append(name)
    return names


def build_cyclonedx_skeleton(
    project_root: Path, requirements_text: str
) -> dict[str, Any]:
    """CycloneDX 1.5 skeleton with library components and the real release label."""
    components = [
        {"type": "library", "name": name, "bom-ref": f"pkg:pypi/{name}"}
        for name in parse_requirement_names(requirements_text)
    ]
    return {
        "bomFormat": "CycloneDX",
        "specVersion": SBOM_SPEC_VERSION,
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": {
                "type": "application",
                "name": SBOM_APPLICATION_NAME,
                "version": release_label(project_root),
            },
        },
        "components": components,
    }
