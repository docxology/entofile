"""Standalone artifact manifest writer for the working entofile project."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .structured_data import atomic_write_json

_IGNORED_OUTPUT_PARTS = frozenset(
    {".checkpoints", ".pipeline", "hitl", "logs", "snapshots", "__pycache__"}
)
_IGNORED_OUTPUT_FILENAMES = frozenset(
    {
        "artifact_manifest.json",
        "evidence_registry.json",
        "snapshot_compare.json",
        "snapshot_compare.md",
        "transmission_integrity_strip.png",
        "transmission_pairing.png",
    }
)
_IGNORED_OUTPUT_SUFFIXES = frozenset({".aux", ".log", ".nav", ".snm", ".toc", ".vrb"})
_STABLE_REPORT_FILES = frozenset(
    {
        "benchmark_validation.json",
        "container_verification.json",
        "conformance_report.json",
        "figure_layout_report.json",
        "sbom.cyclonedx.json",
    }
)
_STABLE_DATA_FILES = frozenset(
    {"ento_benchmark_results.csv", "manuscript_variables.json"}
)


def compute_sha256(path: Path) -> str:
    """Compute a SHA-256 digest without depending on template infrastructure."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_artifact_manifest(project_root: Path) -> Path:
    """Write ``output/reports/artifact_manifest.json`` for current outputs.

    The shared template pipeline writes stage manifests when projects run under
    `active/`. This project is rendered standalone from `working/entofile`, so the
    RC needs a stage manifest that describes stable project-local analysis artifacts
    and avoids stale `projects/entofile/output` declarations. Renderer-mutated
    outputs such as PDFs, HTML, LaTeX logs, and validation reports are intentionally
    excluded so template validation can re-run after render without hash drift.
    """
    root = project_root.resolve()
    output_dir = root / "output"
    report_path = output_dir / "reports" / "artifact_manifest.json"
    stage_dir = output_dir / ".pipeline" / "artifacts"
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entries: list[dict[str, Any]] = []

    if output_dir.is_symlink():
        raise OSError(f"refusing to inspect symlinked output directory: {output_dir}")
    if output_dir.exists():
        for path in sorted(output_dir.rglob("*")):
            if (
                not path.is_file()
                or path.is_symlink()
                or _is_ignored_output(path, output_dir)
            ):
                continue
            if not _is_stable_release_artifact(path, output_dir):
                continue
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": compute_sha256(path),
                    "stage_num": 99,
                    "stage_name": "standalone_project_outputs",
                    "contract_match": True,
                    "timestamp": timestamp,
                }
            )

    payload = {"entries": entries, "issues": []}
    _refresh_stage_manifest(stage_dir, payload)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(report_path, payload)
    return report_path


def _refresh_stage_manifest(stage_dir: Path, payload: dict[str, Any]) -> None:
    """Replace stale template stage manifests with the standalone project manifest."""
    if stage_dir.is_symlink():
        raise OSError(f"refusing to replace symlinked stage directory: {stage_dir}")
    stage_dir.mkdir(parents=True, exist_ok=True)
    for old_manifest in stage_dir.glob("stage-*.json"):
        old_manifest.unlink()
    stage_path = stage_dir / "stage-99-standalone-project-outputs.json"
    atomic_write_json(stage_path, payload)


def _is_ignored_output(path: Path, output_dir: Path) -> bool:
    rel_parts = path.relative_to(output_dir).parts
    return (
        any(part in _IGNORED_OUTPUT_PARTS for part in rel_parts)
        or path.name in _IGNORED_OUTPUT_FILENAMES
        or path.suffix in _IGNORED_OUTPUT_SUFFIXES
    )


def _is_stable_release_artifact(path: Path, output_dir: Path) -> bool:
    """Return whether a file is stable across render/validate reruns."""
    rel_parts = path.relative_to(output_dir).parts
    if not rel_parts:
        return False
    top = rel_parts[0]
    if top == "figures":
        return path.suffix == ".png" or path.name == "figure_registry.json"
    if top == "docs":
        return path.suffix in {".md", ".json", ".txt"}
    if top == "reports":
        return path.name in _STABLE_REPORT_FILES
    if top == "data":
        return len(rel_parts) == 2 and path.name in _STABLE_DATA_FILES
    if top == "conformance":
        return path.suffix == ".zip" or path.name == "conformance_manifest.json"
    return False
