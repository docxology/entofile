"""Tests for proof chain export."""

from __future__ import annotations

from src import crypto
from src.manifest import manifest_to_json
from src.models import (
    Manifest,
    ObservabilityLevel,
    ProofExport,
    ProofLink,
    TrackDescriptor,
)
from src.proof import export_proof, verify_proof_chain, verify_proof_export


def _manifest() -> Manifest:
    return Manifest(
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
            TrackDescriptor(
                id="b",
                type="ento:genomics.vcf",
                sha256_plaintext="3" * 64,
                sha256_ciphertext="4" * 64,
                byte_length=2,
            ),
        ),
    )


def test_proof_chain_structure() -> None:
    manifest = _manifest()
    proof = export_proof(manifest)
    manifest_json = manifest_to_json(manifest)
    assert verify_proof_export(proof, manifest_json) is True
    assert len(proof.links) == 2
    assert proof.links[0].index == 0
    assert proof.links[1].previous_hash == proof.links[0].entry_hash


def test_verify_proof_chain() -> None:
    manifest = _manifest()
    proof = export_proof(manifest)
    assert verify_proof_chain(proof) is True


def test_verify_proof_export_rejects_wrong_manifest() -> None:
    manifest = _manifest()
    proof = export_proof(manifest)
    assert verify_proof_export(proof, manifest_to_json(manifest)) is True
    assert verify_proof_export(proof, '{"tampered": true}\n') is False


def test_verify_proof_export_rejects_links_describing_other_tracks() -> None:
    """A chain that is internally valid and carries the right manifest digest but
    whose links describe a DIFFERENT track than the manifest must be rejected
    (link <-> manifest correspondence, not just digest binding)."""
    manifest = _manifest()
    manifest_json = manifest_to_json(manifest)
    prev = "0" * 64
    payload = f"{prev}:evil:{'9' * 64}".encode()
    forged = ProofExport(
        format_version="0.2.0",
        created="x",
        manifest_sha256=crypto.sha256_hex(manifest_json.encode("utf-8")),
        links=(
            ProofLink(
                index=0,
                track_id="evil",
                sha256_plaintext="9" * 64,
                previous_hash=prev,
                entry_hash=crypto.sha256_hex(payload),
            ),
        ),
    )
    # Chain is self-consistent and digest matches, but links don't match the manifest.
    assert verify_proof_chain(forged) is True
    assert forged.manifest_sha256 == crypto.sha256_hex(manifest_json.encode("utf-8"))
    assert verify_proof_export(forged, manifest_json) is False


def test_verify_proof_export_rejects_wrong_format_version() -> None:
    """A proof whose format_version disagrees with the manifest is rejected."""
    manifest = _manifest()
    manifest_json = manifest_to_json(manifest)
    rebuilt = export_proof(manifest)
    mismatched = ProofExport(
        format_version="9.9.9",
        created=rebuilt.created,
        manifest_sha256=rebuilt.manifest_sha256,
        links=rebuilt.links,
    )
    assert verify_proof_export(mismatched, manifest_json) is False


def test_verify_proof_export_rejects_reordered_links() -> None:
    """Reordering the links (same set, wrong order) breaks the chain binding."""
    manifest = _manifest()
    manifest_json = manifest_to_json(manifest)
    proof = export_proof(manifest)
    reordered = ProofExport(
        format_version=proof.format_version,
        created=proof.created,
        manifest_sha256=proof.manifest_sha256,
        links=tuple(reversed(proof.links)),
    )
    assert verify_proof_export(reordered, manifest_json) is False
