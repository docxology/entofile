"""Deterministic conformance fixture generation."""

from __future__ import annotations

import json
from pathlib import Path

from src.cli import main
from src.conformance import (
    CONFORMANCE_KEY,
    generate_conformance_fixtures,
    verify_conformance_fixtures,
)
from src.crypto import SUPPORTED_FORMAT_VERSIONS


def test_conformance_generator_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_manifest = generate_conformance_fixtures(first)
    second_manifest = generate_conformance_fixtures(second)
    assert first_manifest.read_text(encoding="utf-8") == second_manifest.read_text(
        encoding="utf-8"
    )


def test_conformance_cases_have_expected_cli_behavior(tmp_path: Path) -> None:
    out = tmp_path / "conformance"
    manifest_path = generate_conformance_fixtures(out)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    key_path = tmp_path / "conformance.key"
    key_path.write_bytes(CONFORMANCE_KEY)
    cases = {case["case_id"]: case for case in manifest["cases"]}
    for version in SUPPORTED_FORMAT_VERSIONS:
        assert f"good-{version}" in cases

    for case in manifest["cases"]:
        container = out / case["path"]
        verify_with_key = main(["verify", "-i", str(container), "-k", str(key_path)])
        verify_without_key = main(["verify", "-i", str(container)])
        unpack = main(
            [
                "unpack",
                "-i",
                str(container),
                "-k",
                str(key_path),
                "-o",
                str(tmp_path / "unpacked" / case["case_id"]),
            ]
        )
        assert (verify_with_key == 0) is case["expected_verify_with_key"]
        assert (verify_without_key == 0) is case["expected_verify_without_key"]
        assert (unpack == 0) is case["expected_unpack"]


def test_conformance_verifier_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "conformance"
    generate_conformance_fixtures(out)
    report_path = tmp_path / "reports" / "conformance_report.json"
    report = verify_conformance_fixtures(out, report_path=report_path)
    expected_count = len(SUPPORTED_FORMAT_VERSIONS) + 3
    assert report["ok"] is True
    assert report["case_count"] == expected_count
    assert report["failed_cases"] == []
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert written["passed"] == expected_count
    assert "key_hex" not in report_path.read_text(encoding="utf-8")


def test_run_live_conformance_derives_verdict_without_side_file(tmp_path: Path) -> None:
    """The certifying conformance check regenerates and verifies fixtures in one
    call — no on-disk report is read, so a stale/forged conformance_report.json
    cannot certify conformance."""

    from src.conformance import run_live_conformance

    result = run_live_conformance(tmp_path / "scratch")
    expected_count = len(SUPPORTED_FORMAT_VERSIONS) + 3
    assert result["ok"] is True
    assert result["case_count"] == expected_count
    assert result["failed_cases"] == []
    # Default (no scratch dir) uses an ephemeral temp dir and must also pass.
    ephemeral = run_live_conformance()
    assert ephemeral["ok"] is True
    assert ephemeral["case_count"] == expected_count


def test_ok_or_error_rejects_nondict_verifier_result() -> None:
    """Cross-vendor regression (ENTO-XV-F2, 2026-06-10): `_ok_or_error` returned
    success for ANY non-dict result. For the `verify_*` axes (the strongest
    laundering defence) a non-dict means an out-of-contract verifier — it must
    be an oracle error, not a silent pass — while `unpack`'s (payload, manifest)
    tuple stays a valid success. Tested directly with real callables (no mocks)."""
    from src.conformance import _ok_or_error

    # verify_* contract: dict carrying `ok`.
    assert _ok_or_error(lambda: {"ok": True}, dict_result_required=True) == (True, "")
    assert _ok_or_error(lambda: {"ok": False}, dict_result_required=True) == (False, "")

    # A non-dict verifier result must NOT launder into a pass.
    ok, error = _ok_or_error(lambda: True, dict_result_required=True)
    assert ok is False
    assert "expected dict" in error

    # unpack-style success (tuple) is still valid when a dict is not required.
    assert _ok_or_error(lambda: ("payload", {"format_version": "0.4.0"}))[0] is True

    # Exceptions remain failures on both axes.
    def _raise() -> object:
        raise ValueError("boom")

    assert _ok_or_error(_raise, dict_result_required=True)[0] is False
    assert _ok_or_error(_raise)[0] is False
