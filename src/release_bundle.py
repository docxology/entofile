"""Release manifest and checksum bundle generation."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import crypto
from .artifact_manifest import compute_sha256
from .structured_data import atomic_write_text, read_yaml_mapping


@dataclass(frozen=True)
class ReleaseFile:
    path: str
    role: str
    required: bool = True


RELEASE_FILES: tuple[ReleaseFile, ...] = (
    ReleaseFile("output/pdf/entofile_combined.pdf", "combined manuscript PDF"),
    ReleaseFile("output/web/index.html", "combined manuscript HTML"),
    ReleaseFile("output/reports/sbom.cyclonedx.json", "CycloneDX SBOM"),
    ReleaseFile("output/reports/artifact_manifest.json", "artifact manifest"),
    ReleaseFile("output/reports/validation_report.json", "render validation report"),
    ReleaseFile(
        "output/reports/benchmark_validation.json", "benchmark validation report"
    ),
    ReleaseFile(
        "output/reports/container_verification.json", "container verification report"
    ),
    ReleaseFile(
        "output/reports/conformance_report.json", "conformance verification report"
    ),
    ReleaseFile("output/reports/figure_layout_report.json", "figure layout QA report"),
    ReleaseFile("output/data/ento_benchmark_results.csv", "benchmark CSV"),
    ReleaseFile(
        "output/data/manuscript_variables.json", "hydrated manuscript variables"
    ),
    ReleaseFile("output/conformance/conformance_manifest.json", "conformance manifest"),
    ReleaseFile("manuscript/config.yaml", "manuscript configuration"),
    ReleaseFile("manuscript/references.bib", "bibliography"),
    ReleaseFile("docs/evidence_provenance.md", "evidence provenance boundary"),
    ReleaseFile("docs/publication_checklist.md", "publication readiness checklist"),
    ReleaseFile("docs/public_release_checklist.md", "public release checklist"),
    ReleaseFile("docs/public_ci_dry_run.md", "public CI dry-run map"),
    ReleaseFile("docs/provenance_signing.md", "provenance and signing recipe"),
    ReleaseFile("docs/methods.md", "methods and visualization contract"),
    ReleaseFile("docs/format_0_5_0.md", "opt-in authenticated-manifest format profile"),
    ReleaseFile("docs/research/agenda.md", "preregistered research agenda"),
    ReleaseFile("experiment_plan.yaml", "machine-readable research protocol"),
    ReleaseFile("docs/figure_registry.md", "code-derived figure registry"),
    ReleaseFile("docs/output_inventory.md", "output artifact inventory"),
    ReleaseFile(
        "docs/research/reproducible_figures_crypto_vectors.md",
        "figure and crypto verification research notes",
    ),
    ReleaseFile("docs/redteam_publish_0.4.md", "RedTeam release ledger"),
    ReleaseFile(
        "docs/redteam_claim_scholarship_audit_0.4.md",
        "RedTeam claim and scholarship audit",
    ),
    ReleaseFile(
        "docs/redteam_repo_visual_audit_0.4.md",
        "RedTeam repo-wide and visualization confirmation",
    ),
    ReleaseFile("README.md", "project README"),
    ReleaseFile("TODO.md", "roadmap"),
    ReleaseFile("LICENSE", "license"),
    ReleaseFile("SECURITY.md", "security disclosure policy"),
    ReleaseFile("CITATION.cff", "citation metadata"),
    ReleaseFile("CONTRIBUTING.md", "contribution guide"),
)


def build_release_bundle(project_root: Path, *, output_dir: Path | None = None) -> Path:
    """Write release manifest and SHA256SUMS under ``output/release``.

    The generated files are designed to be signed externally. ENTO does not
    shell out to Cosign or upload a release here; it binds the local artifacts
    into a deterministic checksum surface that a release operator can sign.
    """
    root = project_root.resolve()
    source_dirty_project = bool(_git_text(root, "status", "--porcelain", "--", "."))
    source_dirty_repository = bool(_git_text(root, "status", "--porcelain"))
    release_dir = output_dir or root / "output" / "release"
    if release_dir.is_symlink():
        raise OSError(f"refusing to write release bundle through symlink: {release_dir}")
    release_dir.mkdir(parents=True, exist_ok=True)
    config = _load_config(root)
    entries: list[dict[str, Any]] = []
    missing: list[str] = []

    for release_file in RELEASE_FILES:
        path = root / release_file.path
        if not path.is_file() or path.is_symlink():
            if release_file.required:
                missing.append(release_file.path)
            continue
        entries.append(
            {
                "path": release_file.path,
                "role": release_file.role,
                "required": release_file.required,
                "size_bytes": path.stat().st_size,
                "sha256": compute_sha256(path),
            }
        )

    checksums_path = release_dir / "SHA256SUMS"
    atomic_write_text(
        checksums_path,
        "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in entries),
    )
    manifest_path = release_dir / "release_manifest.json"
    payload: dict[str, Any] = {
        "ok": not missing,
        "schema_version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": "entofile",
        "planned_public_home": "https://github.com/docxology/entofile",
        "release_label": str(config.get("paper", {}).get("version", "")),
        "paper_title": str(config.get("paper", {}).get("title", "")),
        "doi": str(config.get("publication", {}).get("doi", "")),
        "wire_format_default": crypto.FORMAT_VERSION,
        "supported_wire_formats": list(crypto.SUPPORTED_FORMAT_VERSIONS),
        "source_revision": _git_text(root, "rev-parse", "HEAD"),
        "source_dirty": source_dirty_project,
        "source_dirty_project": source_dirty_project,
        "source_dirty_repository": source_dirty_repository,
        "checksum_file": checksums_path.relative_to(root).as_posix(),
        "entries": entries,
        "missing_required": missing,
        "signing_note": (
            "Sign output/release/SHA256SUMS and output/release/release_manifest.json "
            "with the external Sigstore/Cosign process documented in docs/provenance_signing.md."
        ),
    }
    atomic_write_text(manifest_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return manifest_path


def _load_config(root: Path) -> dict[str, Any]:
    config_path = root / "manuscript" / "config.yaml"
    try:
        return read_yaml_mapping(config_path, required=False)
    except (OSError, TypeError, ValueError):
        return {}


def _git_text(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()
