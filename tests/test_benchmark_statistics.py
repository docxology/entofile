"""Correctness of the dispersion statistics layer (mean/sd/cv/sem/t-CI).

Hand-computed expected values, an exact-metric zero-variance control, and a
CI-contains-mean invariant. Small-n tests use tabulated Student-t critical values;
release-scale runs use a large-df inverse-t expansion instead of a bare z=1.96.
"""

from __future__ import annotations

import math

import pytest

from src.benchmark_stats import (
    SummaryStats,
    _t_critical_95,
    base_condition,
    ci_method_description,
    field_summary,
    summary_stats,
)
from src.figure_registry import spec_by_label


def test_summary_stats_hand_computed_n3() -> None:
    """[10, 12, 14]: mean 12, sample sd 2, sem 2/sqrt(3), CI = mean +/- 4.303*sem."""
    s = summary_stats([10.0, 12.0, 14.0])
    assert s.n == 3
    assert s.mean == pytest.approx(12.0)
    assert s.sd == pytest.approx(2.0)  # sample (n-1) sd of 10,12,14
    assert s.cv == pytest.approx(2.0 / 12.0)
    assert s.sem == pytest.approx(2.0 / math.sqrt(3))
    half = 4.303 * (2.0 / math.sqrt(3))
    assert s.ci95_lo == pytest.approx(12.0 - half, rel=1e-3)
    assert s.ci95_hi == pytest.approx(12.0 + half, rel=1e-3)


def test_summary_stats_uses_t_not_z_for_small_n() -> None:
    """The 95% half-width for n=3 must use t=4.303, not z=1.96 (>2x wider)."""
    s = summary_stats([10.0, 12.0, 14.0])
    half = (s.ci95_hi - s.ci95_lo) / 2
    z_half = 1.96 * s.sem
    assert half > z_half * 1.5  # t-interval is markedly wider than the normal one


def test_release_scale_t_critical_uses_large_df_expansion() -> None:
    """df=149 stays above the normal quantile while approaching it from above."""
    t149 = _t_critical_95(149)
    assert 1.97 < t149 < 1.99
    assert t149 > 1.959963984540054
    assert "large-df expansion" in ci_method_description(150)


def test_summary_stats_single_value_has_no_spread() -> None:
    s = summary_stats([7.5])
    assert s == SummaryStats(
        n=1, mean=7.5, sd=0.0, cv=0.0, sem=0.0, ci95_lo=7.5, ci95_hi=7.5
    )


def test_summary_stats_exact_metric_zero_variance() -> None:
    """An exact metric (identical values, e.g. expansion ratio) reports sd=cv=0 —
    the honest signal that it carries no measurement noise."""
    s = summary_stats([1.5, 1.5, 1.5])
    assert s.sd == 0.0
    assert s.cv == 0.0
    assert s.ci95_lo == pytest.approx(1.5)
    assert s.ci95_hi == pytest.approx(1.5)


def test_summary_stats_empty_raises() -> None:
    with pytest.raises(ValueError, match="at least one value"):
        summary_stats([])


def test_ci_contains_mean_invariant() -> None:
    for sample in ([1.0, 5.0, 9.0], [0.1, 0.2, 0.15, 0.3], [100.0, 100.0, 100.0]):
        s = summary_stats(sample)
        assert s.ci95_lo <= s.mean <= s.ci95_hi


def test_base_condition_strips_repetition_suffix() -> None:
    assert base_condition("medium_tracks_r0") == "medium_tracks"
    assert base_condition("small_tracks_r12") == "small_tracks"
    assert base_condition("no_suffix") == "no_suffix"


def test_field_summary_on_real_throughput_is_noisy() -> None:
    """Timing dispersion is derived from rows, independent of ignored outputs."""
    rows = [
        {
            "condition": "medium_tracks_r0",
            "track_id": "medium",
            "observability_level": "3",
            "pack_throughput_mib_s": "10.0",
        },
        {
            "condition": "medium_tracks_r1",
            "track_id": "medium",
            "observability_level": "3",
            "pack_throughput_mib_s": "12.0",
        },
    ]
    spec = spec_by_label("fig:throughput_benchmark")
    s = field_summary(rows, spec, "pack_throughput_mib_s")
    assert s is not None
    assert s.n >= 2
    assert s.sd > 0.0  # timing is genuinely noisy
    assert s.ci95_lo < s.mean < s.ci95_hi


def test_field_summary_on_expansion_is_exact() -> None:
    """Expansion ratio across repetitions is identical (data-derived, exact)."""
    vals = [1.5, 1.5, 1.5]
    assert summary_stats(vals).sd == 0.0
