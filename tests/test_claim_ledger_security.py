"""Security-related claim ledger bindings."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.analysis import run_benchmark_pipeline


def _claims(root: Path) -> dict[str, dict[str, object]]:
    ledger = yaml.safe_load((root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8"))
    return {c["claim_id"]: c for c in ledger["claims"]}


def test_tamper_detection_rate_claim_matches_benchmark_report(
    fast_benchmark_project: tuple[Path, object],
) -> None:
    root, cfg = fast_benchmark_project
    run_benchmark_pipeline(root, config=cfg)
    claims = _claims(root)
    report = json.loads((root / "output" / "reports" / "benchmark_validation.json").read_text(encoding="utf-8"))
    assert float(report["tamper_detection_rate"]) == float(claims["tamper-detection-rate"]["value"])
    assert report["status"] == "pass"


def test_container_verification_report_claim() -> None:
    root = Path(__file__).resolve().parent.parent
    report_path = root / "output" / "reports" / "container_verification.json"
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert report["sample_count"] >= 1
