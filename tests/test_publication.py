"""Tests for publication readiness gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src import crypto
from src.publication import check_publication_readiness


def _write_config(root: Path, *, doi: str = "") -> None:
    config_dir = root / "manuscript"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_dir.joinpath("config.yaml").write_text(
        f'publication:\n  doi: "{doi}"\n',
        encoding="utf-8",
    )


def _write_passing_test_report(
    root: Path, *, all_passed: bool = True, coverage: float = 91.0
) -> None:
    reports = root / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    reports.joinpath("test_results.json").write_text(
        json.dumps(
            {"summary": {"all_passed": all_passed, "project_coverage": coverage}}
        ),
        encoding="utf-8",
    )


def _write_variables(root: Path, *, unresolved: bool = False) -> None:
    data = root / "output" / "data"
    data.mkdir(parents=True, exist_ok=True)
    payload = {"FORMAT_VERSION": crypto.FORMAT_VERSION}
    if unresolved:
        payload["BAD"] = "{{UNRESOLVED}}"
    data.joinpath("manuscript_variables.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def _write_validation_report(
    root: Path, *, evidence_issues: list[str] | None = None
) -> None:
    reports = root / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    issues = evidence_issues or []
    reports.joinpath("validation_report.json").write_text(
        json.dumps({"output_statistics": {"evidence_issues": issues}}),
        encoding="utf-8",
    )


def _write_benchmark_gate(
    root: Path, *, status: str = "pass", tamper_rate: float = 1.0
) -> None:
    reports = root / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    reports.joinpath("benchmark_validation.json").write_text(
        json.dumps({"status": status, "tamper_detection_rate": tamper_rate}),
        encoding="utf-8",
    )
    data = root / "output" / "data"
    data.mkdir(parents=True, exist_ok=True)
    data.joinpath("ento_benchmark_results.csv").write_text(
        "condition,bytes\n", encoding="utf-8"
    )


def test_publication_readiness_after_pipeline() -> None:
    root = Path(__file__).resolve().parent.parent
    result = check_publication_readiness(root)
    assert "ok" in result
    assert result["release"] == "0.5"
    assert result["format_version"] == crypto.FORMAT_VERSION
    if not result["ok"]:
        assert result["blockers"], "expected blocker messages when not ok"


def test_blocker_missing_combined_pdf(tmp_path: Path) -> None:
    _write_config(tmp_path)
    _write_passing_test_report(tmp_path)
    _write_variables(tmp_path)
    _write_validation_report(tmp_path)
    _write_benchmark_gate(tmp_path)

    result = check_publication_readiness(tmp_path)
    assert result["ok"] is False
    assert result["checks"]["combined_pdf"] is False
    assert any("combined manuscript PDF" in item for item in result["blockers"])


def test_blocker_failed_tests(tmp_path: Path) -> None:
    _write_config(tmp_path)
    _write_passing_test_report(tmp_path, all_passed=False)
    _write_variables(tmp_path)
    _write_validation_report(tmp_path)

    result = check_publication_readiness(tmp_path)
    assert result["ok"] is False
    assert result["checks"]["tests_passed"] is False
    assert any("test_results.json" in item for item in result["blockers"])


def test_blocker_low_coverage(tmp_path: Path) -> None:
    _write_config(tmp_path)
    _write_passing_test_report(tmp_path, coverage=80.0)
    _write_variables(tmp_path)
    _write_validation_report(tmp_path)

    result = check_publication_readiness(tmp_path)
    assert result["ok"] is False
    assert result["checks"]["coverage_floor"] is False


def test_blocker_benchmark_validation_fail(tmp_path: Path) -> None:
    _write_config(tmp_path)
    _write_passing_test_report(tmp_path)
    _write_variables(tmp_path)
    _write_validation_report(tmp_path)
    _write_benchmark_gate(tmp_path, status="fail", tamper_rate=0.5)

    result = check_publication_readiness(tmp_path)
    assert result["ok"] is False
    assert result["checks"]["analysis_outputs"] is False


def test_blocker_evidence_registry(tmp_path: Path) -> None:
    _write_config(tmp_path)
    _write_passing_test_report(tmp_path)
    _write_variables(tmp_path)
    _write_validation_report(
        tmp_path, evidence_issues=["unsupported literal 90% in abstract"]
    )
    pdf_dir = tmp_path / "output" / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    # Real %PDF header + non-trivial size so the (now substance-checking) combined_pdf
    # gate passes — this test isolates the evidence_registry blocker.
    pdf_dir.joinpath("entofile_combined.pdf").write_bytes(b"%PDF-1.4\n" + b"0" * 2048)

    result = check_publication_readiness(tmp_path)
    assert result["ok"] is False
    assert result["checks"]["evidence_registry"] is False


def test_blocker_unresolved_variables(tmp_path: Path) -> None:
    _write_config(tmp_path)
    _write_passing_test_report(tmp_path)
    _write_variables(tmp_path, unresolved=True)
    _write_validation_report(tmp_path)

    result = check_publication_readiness(tmp_path)
    assert result["ok"] is False
    assert any("manuscript_variables" in item for item in result["blockers"])


def test_blocker_missing_variables_file(tmp_path: Path) -> None:
    _write_config(tmp_path)
    _write_passing_test_report(tmp_path)
    _write_validation_report(tmp_path)

    result = check_publication_readiness(tmp_path)
    assert result["ok"] is False
    assert result["checks"]["manuscript_variables"] is False


def test_doi_warning_when_empty(tmp_path: Path) -> None:
    _write_config(tmp_path, doi="")
    _write_passing_test_report(tmp_path)
    _write_variables(tmp_path)
    _write_validation_report(tmp_path)

    result = check_publication_readiness(tmp_path)
    assert result["checks"]["doi_configured"] is False
    assert any("doi" in item.lower() for item in result["warnings"])


def test_doi_configured_no_warning(tmp_path: Path) -> None:
    _write_config(tmp_path, doi="10.5281/zenodo.12345678")
    _write_passing_test_report(tmp_path)
    _write_variables(tmp_path)
    _write_validation_report(tmp_path)

    result = check_publication_readiness(tmp_path)
    assert result["checks"]["doi_configured"] is True
    assert not any("doi" in item.lower() for item in result["warnings"])


def test_crypto_constants_present(tmp_path: Path) -> None:
    _write_config(tmp_path)
    result = check_publication_readiness(tmp_path)
    constants = result["crypto_constants"]
    assert constants["master_key_bytes"] == 32
    assert constants["track_header_bytes"] == 28


def test_audit_publication_readiness_help() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "audit_publication_readiness.py"),
            "--help",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--check" in result.stdout


def test_audit_publication_readiness_check_json() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "audit_publication_readiness.py"),
            "--check",
            "--no-live-tests",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["release"] == "0.5"
    assert "checks" in payload
    assert "blockers" in payload
    assert isinstance(payload["ok"], bool)


def test_publication_rejects_fake_pdf(tmp_path: Path) -> None:
    """RedTeam Phase-1A control: a 1-byte non-PDF at the combined-PDF path must NOT
    pass the combined_pdf check (substance, not bare is_file existence)."""
    from src.publication import _is_real_pdf

    fake = tmp_path / "entofile_combined.pdf"
    fake.write_bytes(b"X")
    assert _is_real_pdf(fake) is False
    real_header = tmp_path / "real.pdf"
    real_header.write_bytes(b"%PDF-1.7\n" + b"0" * 2048)
    assert _is_real_pdf(real_header) is True


def test_publication_flags_na_valued_token(tmp_path: Path) -> None:
    """A manuscript token resolved to literal 'N/A' must be flagged (it renders as a
    fake metric and the unresolved-{{TOKEN}} regex misses it)."""
    from src.publication import _na_valued_tokens

    text = json.dumps(
        {
            "RESULT_BENCHMARK_ROWS": "N/A",
            "FORMAT_VERSION": crypto.FORMAT_VERSION,
            "FIG_CAPTION_X": "N/A",  # prose token, legitimately excluded
        }
    )
    flagged = _na_valued_tokens(text)
    assert flagged == {"RESULT_BENCHMARK_ROWS"}
