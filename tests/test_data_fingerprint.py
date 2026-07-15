"""Tests for the deterministic benchmark data fingerprint.

The whole-CSV SHA-256 changes every run because the file embeds re-measured
wall-clock timings, so it is not a reproducibility target. ``benchmark_data_fingerprint``
hashes ONLY the run-invariant columns, giving an anchor a reader can actually
reproduce. These tests pin that contract and — critically — include a negative
control proving the fingerprint CHANGES when a deterministic value changes, so it
cannot pass vacuously on a silent relabel.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest

from src.benchmark_io import benchmark_csv_path, load_benchmark_csv
from src.benchmark_stats import (
    DETERMINISTIC_BENCHMARK_COLUMNS,
    EMPTY_DATA_FINGERPRINT,
    VOLATILE_BENCHMARK_COLUMNS,
    benchmark_data_fingerprint,
    expansion_ratio_model,
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _sample_rows() -> list[dict[str, str]]:
    """Two real-shaped benchmark rows with both deterministic and volatile columns."""
    return [
        {
            "format_version": "0.4.0",
            "condition": "small_tracks_r0",
            "track_id": "eeg",
            "track_type": "ento:timeseries.eeg",
            "plaintext_bytes": "42",
            "ciphertext_bytes": "80",
            "expansion_ratio": "1.904762",
            "pack_seconds": "0.001501",
            "unpack_seconds": "0.001421",
            "pack_throughput_mib_s": "0.026678",
            "tamper_detected": "True",
            "observability_level": "3",
            "manifest_bytes": "499",
        },
        {
            "format_version": "0.4.0",
            "condition": "medium_tracks_r0",
            "track_id": "medium",
            "track_type": "ento:spectrogram",
            "plaintext_bytes": "65536",
            "ciphertext_bytes": "67612",
            "expansion_ratio": "1.031311",
            "pack_seconds": "0.001359",
            "unpack_seconds": "0.001298",
            "pack_throughput_mib_s": "45.996740",
            "tamper_detected": "True",
            "observability_level": "0",
            "manifest_bytes": "314",
        },
    ]


def test_fingerprint_is_64_char_lowercase_hex() -> None:
    assert _HEX64.match(benchmark_data_fingerprint(_sample_rows()))


def test_deterministic_and_volatile_columns_are_disjoint() -> None:
    # The split is the whole point: no column may be counted as both reproducible
    # and re-measured, or the fingerprint would silently absorb timing noise.
    assert not (set(DETERMINISTIC_BENCHMARK_COLUMNS) & set(VOLATILE_BENCHMARK_COLUMNS))


def test_empty_rows_returns_sentinel_not_crash() -> None:
    assert benchmark_data_fingerprint([]) == EMPTY_DATA_FINGERPRINT
    # The sentinel must NOT look like a real SHA-256, or a zero-row run could be
    # mistaken for a legitimate fingerprint (advisor finding #4).
    assert not _HEX64.match(EMPTY_DATA_FINGERPRINT)
    assert benchmark_data_fingerprint([]) != benchmark_data_fingerprint(_sample_rows())


def test_fingerprint_columns_cover_benchmark_row_schema() -> None:
    """Completeness lock bound to the CODE (not a regenerated artifact): every column
    `BenchmarkRow.to_csv_row()` emits must be classified as deterministic OR volatile,
    with no overlap and no stray. This fails the instant a new column is added to
    `BenchmarkRow` without classifying it — closing the negative control's completeness
    gap (advisor #3, Forge concern #1). Binds source-of-truth, so it never skips."""
    from src.benchmarks import BenchmarkRow

    schema_columns = set(
        BenchmarkRow(
            format_version="0.4.0",
            condition="c",
            track_id="t",
            track_type="ento:x",
            plaintext_bytes=1,
            ciphertext_bytes=33,
            expansion_ratio=33.0,
            pack_seconds=0.0,
            unpack_seconds=0.0,
            pack_throughput_mib_s=0.0,
            tamper_detected=True,
            observability_level=0,
            manifest_bytes=1,
        )
        .to_csv_row()
        .keys()
    )
    classified = set(DETERMINISTIC_BENCHMARK_COLUMNS) | set(VOLATILE_BENCHMARK_COLUMNS)
    assert schema_columns == classified, (
        f"unclassified BenchmarkRow columns: {schema_columns ^ classified} — add each "
        f"to the deterministic or volatile set in src/benchmark_stats.py"
    )
    # No column may be in both classes.
    assert not (set(DETERMINISTIC_BENCHMARK_COLUMNS) & set(VOLATILE_BENCHMARK_COLUMNS))


def test_fingerprint_columns_match_live_csv_header_when_present() -> None:
    """Same lock against the on-disk CSV header, as a second witness."""
    project_root = Path(__file__).resolve().parent.parent
    rows = load_benchmark_csv(benchmark_csv_path(project_root))
    if not rows:
        pytest.skip("benchmark CSV not generated in this environment")
    if "format_version" not in rows[0]:
        pytest.skip("benchmark CSV predates 0.4.0 format_version column")
    classified = set(DETERMINISTIC_BENCHMARK_COLUMNS) | set(VOLATILE_BENCHMARK_COLUMNS)
    assert set(rows[0].keys()) == classified


def test_fingerprint_is_row_order_independent() -> None:
    rows = _sample_rows()
    assert benchmark_data_fingerprint(rows) == benchmark_data_fingerprint(
        list(reversed(rows))
    )


def test_changing_only_volatile_columns_does_not_change_fingerprint() -> None:
    """Two 'runs' differing only in re-measured timings hash identically."""
    rows = _sample_rows()
    perturbed = [dict(row) for row in rows]
    for row in perturbed:
        for col in VOLATILE_BENCHMARK_COLUMNS:
            row[col] = str(float(row[col]) * 7.3 + 0.5)  # arbitrary timing change
    assert benchmark_data_fingerprint(rows) == benchmark_data_fingerprint(perturbed)


@pytest.mark.parametrize("column", DETERMINISTIC_BENCHMARK_COLUMNS)
def test_changing_any_deterministic_column_changes_fingerprint(column: str) -> None:
    """Negative control: a silent relabel of ANY deterministic cell is detected."""
    rows = _sample_rows()
    mutated = [dict(row) for row in rows]
    mutated[0][column] = mutated[0][column] + "_TAMPERED"
    assert benchmark_data_fingerprint(rows) != benchmark_data_fingerprint(mutated)


def test_fingerprint_matches_live_csv_variable_when_present() -> None:
    """The fingerprint injected into manuscript_variables.json must equal a fresh
    recompute from the CSV on disk (binding, not a stored guess)."""
    project_root = Path(__file__).resolve().parent.parent
    rows = load_benchmark_csv(benchmark_csv_path(project_root))
    if not rows:
        pytest.skip("benchmark CSV not generated in this environment")
    if "format_version" not in rows[0]:
        pytest.skip("benchmark CSV predates 0.4.0 format_version column")
    vars_path = project_root / "output" / "data" / "manuscript_variables.json"
    if not vars_path.is_file():
        pytest.skip("manuscript_variables.json not generated in this environment")
    variables = json.loads(vars_path.read_text(encoding="utf-8"))
    if variables.get("FORMAT_VERSION") != "0.5.0":
        pytest.skip("manuscript variables predate the current default 0.5.0")
    stored = variables.get("BENCHMARK_DATA_FINGERPRINT")
    if stored is None:
        pytest.skip("BENCHMARK_DATA_FINGERPRINT not present (stale variables file)")
    assert stored == benchmark_data_fingerprint(rows)


def test_expansion_ratio_model_is_exact_over_many_sizes() -> None:
    """Property-style: version-aware model matches padded default and legacy law."""
    rng = random.Random(1729)
    for _ in range(500):
        n = rng.randint(1, 10_000_000)
        assert expansion_ratio_model(n, format_version="0.2.0") == pytest.approx(
            1 + 32 / n, rel=0, abs=1e-12
        )
        assert expansion_ratio_model(n) >= 1 + 28 / n


def test_expansion_ratio_model_rejects_nonpositive() -> None:
    for bad in (0, -1, -65536):
        with pytest.raises(ValueError):
            expansion_ratio_model(bad)


def test_fingerprint_is_invariant_to_numeric_representation() -> None:
    """Same value, different valid string spelling → identical fingerprint.

    This is what "reproduces byte-for-byte on any host" actually requires: the anchor
    must not depend on how a number is spelled in the CSV (RedTeam 2026-05-30 Q3a). The
    test FAILS on a raw-string hash and passes only with numeric canonicalization.
    """
    base = _sample_rows()
    respelled = [dict(row) for row in base]
    respelled[0]["expansion_ratio"] = "1.9047620"  # == 1.904762
    respelled[0]["ciphertext_bytes"] = "80.0"  # == 80
    respelled[0]["manifest_bytes"] = " 499 "  # surrounding whitespace, same value
    assert benchmark_data_fingerprint(base) == benchmark_data_fingerprint(respelled)


def test_fingerprint_still_differs_on_real_numeric_change() -> None:
    """Canonicalization must not collapse genuinely different values (non-vacuous)."""
    base = _sample_rows()
    changed = [dict(row) for row in base]
    changed[0]["manifest_bytes"] = "500"  # != 499
    assert benchmark_data_fingerprint(base) != benchmark_data_fingerprint(changed)
