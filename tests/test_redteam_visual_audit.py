"""Guards for the 0.4 repo-wide RedTeam and visualization audit."""

from __future__ import annotations

from pathlib import Path

from src.figure_registry import FIGURE_SPECS
from src.release_bundle import RELEASE_FILES


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "docs" / "redteam_repo_visual_audit_0.4.md"


def _audit_text() -> str:
    return AUDIT.read_text(encoding="utf-8")


def test_redteam_visual_audit_is_indexed_and_release_bound() -> None:
    assert AUDIT.is_file()
    docs_readme = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    figure_registry = (ROOT / "docs" / "figure_registry.md").read_text(encoding="utf-8")
    release_paths = {entry.path for entry in RELEASE_FILES}
    assert "redteam_repo_visual_audit_0.4.md" in docs_readme
    assert "redteam_repo_visual_audit_0.4.md" in figure_registry
    assert "docs/redteam_repo_visual_audit_0.4.md" in release_paths


def test_redteam_visual_audit_covers_every_registered_figure() -> None:
    text = _audit_text()
    missing = [spec.label for spec in FIGURE_SPECS if spec.label not in text]
    assert not missing, f"Missing figure verdicts: {missing}"
    assert text.count("fig:") >= len(FIGURE_SPECS)
    assert "transmission_integrity_strip.png" in text
    assert "transmission_pairing.png" in text
    assert "| 24 | `transmission_integrity_strip.png` | 42 |" in text


def test_redteam_visual_audit_records_verifier_first_oracles() -> None:
    text = _audit_text()
    for phrase in (
        "Full tests and coverage",
        "No-mock hygiene",
        "Figure layout QA",
        "Template validation",
        "Citation prerender",
        "Conformance verifier",
        "Release manifest",
        "Publication audit",
        "ORACLE-TRUSTWORTHY",
    ):
        assert phrase in text
    assert "2026-06-02 follow-up findings" in text
    for finding_id in ("RT-VIS-001", "RT-VIS-002", "RT-VIS-003"):
        assert finding_id in text
    assert "Figure informativeness rubric" in text
