"""Guards for the 0.4 RedTeam claim and scholarship audit."""

from __future__ import annotations

from pathlib import Path

from src.release_bundle import RELEASE_FILES


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "docs" / "redteam_claim_scholarship_audit_0.4.md"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_claim_scholarship_audit_is_indexed_and_release_bound() -> None:
    assert AUDIT.is_file()
    docs_readme = _read("docs/README.md")
    redteam_ledger = _read("docs/redteam_publish_0.4.md")
    release_paths = {entry.path for entry in RELEASE_FILES}
    assert "redteam_claim_scholarship_audit_0.4.md" in docs_readme
    assert "redteam_claim_scholarship_audit_0.4.md" in redteam_ledger
    assert "docs/redteam_claim_scholarship_audit_0.4.md" in release_paths


def test_claim_scholarship_audit_records_required_vectors_and_oracles() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    for phrase in (
        "Citation scholarship tests",
        "Evidence provenance tests",
        "Claim ledger tests",
        "Template citation prerender",
        "Publication readiness",
        "Wire-format and release labels",
        "AEAD, AAD, and GCM",
        "Key derivation and custody",
        "Proof and JSON hashing",
        "ZIP/path threats",
        "Evidence provenance",
        "Statistics and benchmarks",
        "Supply chain and signing",
        "Preservation positioning",
        "Related formats",
    ):
        assert phrase in text


def test_claim_scholarship_audit_records_perplexity_fallback_and_new_sources() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "401 insufficient_quota" in text
    for source_name in (
        "PLOS reproducible-computing",
        "ACM artifact-badging",
        "NIST SP 800-57",
        "NIST SP 800-161",
        "in-toto",
        "RFC 8452",
        "OAIS",
        "PREMIS",
    ):
        assert source_name in text
    assert "No unresolved critical manuscript-claim findings remain" in text
    assert "readiness remains separate" in text
    assert "RT-CLAIM-006" in text
    assert "RT-CLAIM-007" in text
