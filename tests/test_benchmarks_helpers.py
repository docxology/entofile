"""Benchmark helper coverage."""

from __future__ import annotations

from src.benchmarks import manifest_size_for_level
from src.models import Manifest, ObservabilityLevel, TrackDescriptor


def test_manifest_size_for_level() -> None:
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
    size = manifest_size_for_level(manifest, ObservabilityLevel.SEALED)
    assert size > 0
