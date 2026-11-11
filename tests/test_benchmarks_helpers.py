"""Benchmark helper coverage."""

from __future__ import annotations

from dataclasses import replace

from src.benchmarks import manifest_size_for_level
from src.crypto import FORMAT_VERSION
from src.manifest_binding import compute_manifest_binding
from src.models import Manifest, ObservabilityLevel, TrackDescriptor


def test_manifest_size_for_level() -> None:
    template = Manifest(
        format_version=FORMAT_VERSION,
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
    manifest = replace(
        template, manifest_binding=compute_manifest_binding(template)
    )
    size = manifest_size_for_level(manifest, ObservabilityLevel.SEALED)
    assert size > 0
