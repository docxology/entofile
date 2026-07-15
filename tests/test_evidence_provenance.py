"""Evidence-provenance gates for no-mock and fixture/synthetic boundaries."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "evidence_provenance.md"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_evidence_provenance_doc_is_indexed() -> None:
    assert DOC.is_file()
    assert "evidence_provenance.md" in _read("README.md")
    assert "evidence_provenance.md" in _read("docs/README.md")
    assert "evidence_provenance.md" in _read("docs/methods.md")
    assert "evidence-provenance-boundary" in _read("docs/claim_ledger.md")


def test_evidence_provenance_contract_covers_all_input_and_output_classes() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = {
        "Committed fixture tracks": "data/fixtures/",
        "Medium benchmark track": "src/benchmarks.py::_medium_track",
        "Conformance containers": "scripts/generate_conformance_fixtures.py",
        "Benchmark CSV": "output/data/ento_benchmark_results.csv",
        "Benchmark validation report": "output/reports/benchmark_validation.json",
        "Container verification report": "output/reports/container_verification.json",
        "Registered figures": "src/figure_registry.py",
        "Manuscript variables": "scripts/z_generate_manuscript_variables.py",
        "Release bundle manifest": "scripts/build_release_bundle.py",
        "Rendered PDF/HTML": "scripts/03_render_pdf.py --project working/entofile",
        "Test gate": "uv run python scripts/run_tests.py",
    }
    for label, evidence in required.items():
        assert label in text
        assert evidence in text

    for phrase in (
        "not presented as human-subject or field-collected datasets",
        "not a real-world observational record",
        "test-vector-only",
        "not that every input is a real-world observational dataset",
    ):
        assert phrase in text


def test_manuscript_uses_generated_provenance_tokens() -> None:
    setup = _read("manuscript/05_experimental_setup.md")
    reproducibility = _read("manuscript/06_reproducibility.md")
    for token in (
        "FIXTURE_INPUT_CLASSIFICATION",
        "BENCHMARK_STRESS_INPUT_CLASSIFICATION",
        "CONFORMANCE_INPUT_CLASSIFICATION",
        "EXECUTION_EVIDENCE_CLASSIFICATION",
    ):
        assert f"{{{{{token}}}}}" in setup
    for token in (
        "NO_MOCK_STATUS",
        "CONFORMANCE_REPORT_STATUS",
        "ARTIFACT_MANIFEST_STATUS",
        "RELEASE_MANIFEST_STATUS",
    ):
        assert f"{{{{{token}}}}}" in reproducibility


def test_docs_and_manuscript_do_not_overclaim_real_world_inputs() -> None:
    files = list((ROOT / "docs").rglob("*.md")) + list((ROOT / "manuscript").glob("*.md"))
    offenders: list[str] = []
    forbidden = (
        r"\breal data only\b",
        r"\ball inputs are real-world data\b",
        r"\ball benchmark inputs are real-world\b",
    )
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        if any(re.search(pattern, text) for pattern in forbidden):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "Overbroad real-world input claims: " + ", ".join(offenders)


def test_perplexity_scholarship_lane_records_quota_fallback() -> None:
    text = DOC.read_text(encoding="utf-8")
    one_line = " ".join(text.split())
    assert "2026-06-02" in text
    assert "insufficient_quota" in text
    assert "directly from primary or official sources" in one_line
    for source in (
        "PLOS reproducible-computing papers",
        "RFC 8452",
        "NIST SP 800-57",
        "NIST SP 800-161",
        "ACM artifact-review policy",
        "USENIX in-toto paper",
    ):
        assert source in text
