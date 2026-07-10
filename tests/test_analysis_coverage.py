"""Additional coverage for analysis and proof edge cases."""

from __future__ import annotations

from pathlib import Path

from src.analysis import validate_generated_outputs
from src.figure_registry import register_with_infrastructure
from src.models import Manifest, ObservabilityLevel, ProofExport, ProofLink, TrackDescriptor
from src.ontology import default_resolution
from src.proof import export_proof, verify_proof_chain


def test_register_with_infrastructure_no_crash(tmp_path: Path) -> None:
    figures_dir = tmp_path / "output" / "figures"
    figures_dir.mkdir(parents=True)
    png = figures_dir / "throughput_benchmark.png"
    png.write_bytes(b"png")
    register_with_infrastructure(tmp_path, {"fig:throughput_benchmark": png})
    assert png.exists()


def test_validate_outputs_requires_pass_report() -> None:
    root = Path(__file__).resolve().parent.parent
    result = validate_generated_outputs(root)
    assert "ok" in result
    if result["ok"]:
        assert result["report"]["status"] == "pass"
        assert result["tamper_detection_rate"] == 1.0


def test_default_resolution_blockchain() -> None:
    assert default_resolution("ento:blockchain.proof") is None


def test_verify_proof_chain_failure() -> None:
    manifest = Manifest(
        format_version="0.2.0",
        created="2026-01-01T00:00:00Z",
        creator="test",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(
            TrackDescriptor(
                id="a",
                type="ento:timeseries.eeg",
                sha256_plaintext="1" * 64,
                sha256_ciphertext="2" * 64,
                byte_length=1,
            ),
        ),
    )
    proof = export_proof(manifest)
    bad = ProofExport(
        format_version=proof.format_version,
        created=proof.created,
        manifest_sha256=proof.manifest_sha256,
        links=(
            ProofLink(
                index=0,
                track_id="a",
                sha256_plaintext="1" * 64,
                previous_hash="0" * 64,
                entry_hash="dead" * 16,
            ),
        ),
    )
    assert verify_proof_chain(bad) is False
