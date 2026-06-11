"""Release manifest and checksum bundle tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src import crypto
from src.release_bundle import RELEASE_FILES, build_release_bundle


def _write_release_fixture(root: Path) -> None:
    (root / "manuscript").mkdir(parents=True)
    (root / "manuscript" / "config.yaml").write_text(
        """
paper:
  title: "ENTO test release"
  version: "0.4"
publication:
  doi: "10.5281/zenodo.20396329"
""".lstrip(),
        encoding="utf-8",
    )
    for release_file in RELEASE_FILES:
        path = root / release_file.path
        if path.name == "config.yaml":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{release_file.path}\n", encoding="utf-8")


def test_release_bundle_manifest_and_checksums(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    manifest_path = build_release_bundle(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["release_label"] == "0.4"
    assert payload["planned_public_home"] == "https://github.com/docxology/entofile"
    assert payload["wire_format_default"] == crypto.FORMAT_VERSION
    assert payload["supported_wire_formats"] == list(crypto.SUPPORTED_FORMAT_VERSIONS)
    assert payload["source_dirty"] is False
    assert payload["source_dirty_project"] is False
    assert payload["source_dirty_repository"] is False
    paths = {entry["path"] for entry in payload["entries"]}
    assert "output/pdf/entofile_combined.pdf" in paths
    assert "docs/evidence_provenance.md" in paths
    assert "docs/publication_checklist.md" in paths
    assert "docs/public_release_checklist.md" in paths
    assert "docs/public_ci_dry_run.md" in paths
    assert "docs/provenance_signing.md" in paths
    assert "docs/methods.md" in paths
    assert "docs/figure_registry.md" in paths
    assert "docs/output_inventory.md" in paths
    assert "docs/research/reproducible_figures_crypto_vectors.md" in paths
    assert "docs/redteam_claim_scholarship_audit_0.4.md" in paths
    assert "docs/redteam_repo_visual_audit_0.4.md" in paths
    assert "SECURITY.md" in paths
    checksums = (tmp_path / "output" / "release" / "SHA256SUMS").read_text(
        encoding="utf-8"
    )
    assert "output/pdf/entofile_combined.pdf" in checksums
    assert "output/release/release_manifest.json" not in checksums


def test_release_bundle_dirty_status_is_project_scoped(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = repo / "project"
    project.mkdir(parents=True)
    _write_release_fixture(project)
    subprocess.run(
        ["git", "init"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", "project"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / "dirty-sibling.txt").write_text("not part of project\n", encoding="utf-8")

    manifest_path = build_release_bundle(project)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["source_dirty"] is False
    assert payload["source_dirty_project"] is False
    assert payload["source_dirty_repository"] is True


def test_release_bundle_reports_missing_required_artifacts(tmp_path: Path) -> None:
    (tmp_path / "manuscript").mkdir(parents=True)
    (tmp_path / "manuscript" / "config.yaml").write_text(
        "paper:\n  version: '0.4'\n", encoding="utf-8"
    )
    manifest_path = build_release_bundle(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "output/pdf/entofile_combined.pdf" in payload["missing_required"]
    assert "LICENSE" in payload["missing_required"]
