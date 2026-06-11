"""Tests for analysis output gates."""

from __future__ import annotations

import json
from pathlib import Path

from src.artifact_manifest import write_artifact_manifest
from src.output_gates import (
    benchmark_artifacts_ok,
    benchmark_report_ok,
    container_verification_report_ok,
    validate_all_outputs,
)


def _write_minimal_outputs(root: Path) -> None:
    (root / "output" / "data").mkdir(parents=True, exist_ok=True)
    (root / "output" / "reports").mkdir(parents=True, exist_ok=True)
    (root / "output" / "figures").mkdir(parents=True, exist_ok=True)
    (root / "output" / "data" / "ento_benchmark_results.csv").write_text(
        "condition,track_id\nsmall_tracks_r0,eeg\n",
        encoding="utf-8",
    )
    (root / "output" / "reports" / "benchmark_validation.json").write_text(
        json.dumps({"status": "pass", "tamper_detection_rate": 1.0}) + "\n",
        encoding="utf-8",
    )
    (root / "output" / "reports" / "container_verification.json").write_text(
        json.dumps(
            {
                "ok": True,
                "samples": [
                    {"path": "output/data/_bench_tmp/medium_3.ento.zip", "ok": True}
                ],
                # A substantive report (as build_container_verification_report emits)
                # carries a fired negative control; the gate now requires it so a bare
                # {ok:true} shell cannot certify the crypto core.
                "negative_control": {
                    "available": True,
                    "rejected": True,
                    "integrity": "unverified",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_benchmark_report_ok_passes(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    ok, report = benchmark_report_ok(tmp_path)
    assert ok is True
    assert report["tamper_detection_rate"] == 1.0


def test_container_verification_report_ok_requires_file(tmp_path: Path) -> None:
    assert container_verification_report_ok(tmp_path) is False
    _write_minimal_outputs(tmp_path)
    assert container_verification_report_ok(tmp_path) is True


def test_validate_all_outputs_fails_without_figures(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    assert benchmark_artifacts_ok(tmp_path) is True
    result = validate_all_outputs(tmp_path)
    assert result["containers_ok"] is True
    assert result["figures_ok"] is False
    assert result["ok"] is False


def test_validate_all_outputs_reports_containers_live_provenance(tmp_path: Path) -> None:
    """validate_all_outputs records HOW containers_ok was derived (live re-run vs
    side-file read), so a certifying consumer can refuse to treat a display-grade check
    as a certification. Pins the contract the publication cert-path assertion relies on."""
    _write_minimal_outputs(tmp_path)
    assert validate_all_outputs(tmp_path)["containers_live"] is False
    assert validate_all_outputs(tmp_path, live_containers=True)["containers_live"] is True


def test_container_gate_rejects_stale_ok_shell(tmp_path: Path) -> None:
    """RedTeam Phase-1A control: a forged {ok:true} report with zero samples (a stale
    side file) must NOT certify the crypto core — the F1 oracle false-assurance gap."""
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "container_verification.json").write_text(
        json.dumps({"ok": True, "sample_count": 0, "samples": []}) + "\n",
        encoding="utf-8",
    )
    assert container_verification_report_ok(tmp_path) is False


def test_container_gate_rejects_ok_without_negative_control(tmp_path: Path) -> None:
    """A report with a passing sample but no fired negative control is insufficient —
    the gate must require proof that a bad container is rejected, not just accepted."""
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "container_verification.json").write_text(
        json.dumps({"ok": True, "samples": [{"path": "x", "ok": True}]}) + "\n",
        encoding="utf-8",
    )
    assert container_verification_report_ok(tmp_path) is False


def test_container_gate_live_ignores_lying_side_file(tmp_path: Path) -> None:
    """live=True re-runs the crypto and certifies from real samples, IGNORING the
    on-disk report — so a side file that LIES (claims failure, or claims a forged
    pass) cannot drive the certifying verdict. Closes the last side-file-trust residual."""
    from src.container import pack_container
    from src.crypto import generate_master_key
    from src.fixtures import load_fixture_tracks
    from src.models import ObservabilityLevel

    bench = tmp_path / "output" / "data" / "_bench_tmp"
    bench.mkdir(parents=True)
    pack_container(
        bench / "medium_3.ento.zip",
        generate_master_key(),
        load_fixture_tracks(require_all=True),
        observability_level=ObservabilityLevel.AUDITABLE,
    )
    # A side file that LIES "ok: false" — display mode honors it, live mode overrides
    # it by re-deriving from the real container (which genuinely verifies digest-only).
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "container_verification.json").write_text(
        json.dumps({"ok": False, "samples": []}) + "\n", encoding="utf-8"
    )
    assert container_verification_report_ok(tmp_path, live=False) is False
    assert container_verification_report_ok(tmp_path, live=True) is True


def test_container_gate_live_rejects_forgery_without_real_crypto(
    tmp_path: Path,
) -> None:
    """The reproduced residual: a forged green report passes display mode (it trusts the
    side file) but live mode fails closed when no real container exists to verify —
    a certification cannot pass without crypto actually running this call."""
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "container_verification.json").write_text(
        json.dumps(
            {
                "ok": True,
                "sample_count": 1,
                "negative_control": {"available": True, "rejected": True},
                "samples": [
                    {"path": "output/data/_bench_tmp/medium_3.ento.zip", "ok": True}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert (
        container_verification_report_ok(tmp_path, live=False) is True
    )  # trusts forgery
    assert (
        container_verification_report_ok(tmp_path, live=True) is False
    )  # crypto can't certify


def test_standalone_artifact_manifest_declares_actual_output_tree(
    tmp_path: Path,
) -> None:
    """The working-project manifest should describe output/ directly, not stale template paths."""
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "figures" / "format_ladder.png").write_bytes(b"png")
    (tmp_path / "output" / "figures" / "transmission_pairing.png").write_bytes(
        b"renderer-owned"
    )
    (tmp_path / "output" / "figures" / "transmission_integrity_strip.png").write_bytes(
        b"renderer-owned"
    )
    (tmp_path / "output" / "conformance").mkdir(parents=True)
    (tmp_path / "output" / "conformance" / "good-0.2.0.ento.zip").write_bytes(b"zip")
    (tmp_path / "output" / "conformance" / "conformance_manifest.json").write_text(
        json.dumps({"cases": []}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "output" / "reports" / "conformance_report.json").write_text(
        json.dumps({"ok": True, "cases": []}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "output" / "reports" / "figure_layout_report.json").write_text(
        json.dumps({"ok": True, "figures": []}) + "\n",
        encoding="utf-8",
    )
    manifest_path = write_artifact_manifest(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["issues"] == []
    entries = payload["entries"]
    assert entries
    paths = {entry["path"] for entry in entries}
    assert "output/reports/artifact_manifest.json" not in paths
    assert "output/figures/format_ladder.png" in paths
    assert "output/figures/transmission_pairing.png" not in paths
    assert "output/figures/transmission_integrity_strip.png" not in paths
    assert "output/conformance/conformance_manifest.json" in paths
    assert "output/conformance/good-0.2.0.ento.zip" in paths
    assert "output/reports/conformance_report.json" in paths
    assert "output/reports/figure_layout_report.json" in paths
    assert all(not path.startswith("projects/entofile/") for path in paths)
    assert all(entry["contract_match"] is True for entry in entries)
    stage_manifests = sorted(
        (tmp_path / "output" / ".pipeline" / "artifacts").glob("stage-*.json")
    )
    assert [path.name for path in stage_manifests] == [
        "stage-99-standalone-project-outputs.json"
    ]
    assert json.loads(stage_manifests[0].read_text(encoding="utf-8"))["issues"] == []
