"""Validation that the version-aware ciphertext-expansion law holds."""

from __future__ import annotations

from pathlib import Path

import pytest

from src import crypto, padding
from src.benchmark_io import benchmark_csv_path, load_benchmark_csv
from src.benchmark_stats import (
    TRACK_HEADER_BYTES,
    expansion_ratio_model,
    max_expansion_ratio_residual,
)
from src.crypto import FORMAT_VERSION, TAG_SIZE

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_header_constant_matches_crypto() -> None:
    assert TRACK_HEADER_BYTES == crypto.nonce_size_for(FORMAT_VERSION) + TAG_SIZE == 28


def test_expansion_model_closed_form() -> None:
    # Current default 0.5.0: nonce(12) + tag(16) + PADME(length-prefix + plaintext).
    for n in (32, 42, 64):
        expected = (28 + padding.padme(n + 8)) / n
        assert expansion_ratio_model(n) == pytest.approx(expected)
    # Legacy 0.2.0 remains the simple unpadded identity.
    assert expansion_ratio_model(64, format_version="0.2.0") == pytest.approx(1.5)


def test_expansion_model_rejects_nonpositive() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        expansion_ratio_model(0)


def test_expansion_model_is_monotone_decreasing_to_one() -> None:
    ratios = [expansion_ratio_model(n) for n in (16, 64, 256, 4096, 65536)]
    assert ratios == sorted(ratios, reverse=True)
    assert ratios[-1] > 1.0
    assert 1.0 < expansion_ratio_model(10**9) < 1.01


def test_measured_rows_satisfy_law_to_float_precision() -> None:
    """Every benchmark row's measured expansion_ratio equals the model."""
    csv = benchmark_csv_path(_PROJECT_ROOT)
    if not csv.is_file():
        pytest.skip("benchmark CSV not generated; run scripts/ento_analysis.py")
    rows = load_benchmark_csv(csv)
    assert rows, "benchmark CSV is empty"
    if "format_version" not in rows[0]:
        pytest.skip("benchmark CSV predates 0.4.0 format_version column")
    residual = max_expansion_ratio_residual(rows)
    # Identity, not a fit: residual must be at CSV-rounding / float noise level.
    assert residual < 1e-3, f"expansion law violated: max |residual| = {residual}"


def test_residual_negative_control() -> None:
    """A row that violates the law must produce a large residual (non-vacuity)."""
    good_ratio = expansion_ratio_model(64)
    good = {
        "format_version": FORMAT_VERSION,
        "plaintext_bytes": "64",
        "expansion_ratio": f"{good_ratio:.12f}",
    }
    bad = {"plaintext_bytes": "64", "expansion_ratio": "9.9"}
    assert max_expansion_ratio_residual([good]) < 1e-6
    assert max_expansion_ratio_residual([bad]) > 1.0
