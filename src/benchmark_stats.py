"""Shared benchmark CSV metrics for figures and manuscript variables."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from statistics import StatisticsError, mean, stdev

from .benchmark_filters import is_tamper_detected
from .crypto import FORMAT_VERSION, TAG_SIZE, nonce_size_for, pads_payload
from .figure_registry import FigureSpec, filter_rows_for_spec
from .padding import padme

#: Benchmark columns that are exact functions of byte counts (the ciphertext-expansion
#: law) and the manifest schema — identical on every regeneration regardless of host
#: load. These are the bytes a reproducibility claim can honestly anchor to.
DETERMINISTIC_BENCHMARK_COLUMNS: tuple[str, ...] = (
    "format_version",
    "condition",
    "track_id",
    "track_type",
    "plaintext_bytes",
    "ciphertext_bytes",
    "expansion_ratio",
    "tamper_detected",
    "observability_level",
    "manifest_bytes",
)

#: Wall-clock columns re-measured on every run (host-load dependent); deliberately
#: EXCLUDED from the data fingerprint. Averaging or hashing across this boundary is
#: exactly the mistake the fingerprint exists to prevent.
VOLATILE_BENCHMARK_COLUMNS: tuple[str, ...] = (
    "pack_seconds",
    "unpack_seconds",
    "pack_throughput_mib_s",
)

#: Fingerprint of an empty benchmark set — a deliberately NON-hex sentinel so a zero-row
#: run can never be mistaken for a legitimate 64-char SHA-256 (a hex sentinel like
#: ``"0"*64`` would be indistinguishable from a real result).
EMPTY_DATA_FINGERPRINT = "EMPTY-NO-BENCHMARK-ROWS"

_FIELD_SEP = "\x1f"  # ASCII unit separator — cannot occur in numeric/label CSV cells
_ROW_SEP = "\x1e"  # ASCII record separator


def _canonical_cell(value: str) -> str:
    """Representation-independent hashable form of a CSV cell.

    A reproducibility anchor must not depend on how a number happens to be spelled in
    the CSV — ``"1.50"``, ``"1.5"`` and ``" 1.5 "`` are the same value and must hash
    identically on any host, while genuinely different values must still differ. Numeric
    cells are normalized through a float round-trip (integers keep their exact integer
    form; non-integers use the shortest round-trip ``repr``, which is platform-stable in
    CPython); non-numeric cells (labels, booleans, URIs) hash as their stripped string.
    This is what makes the "byte-for-byte on any host" claim true rather than an
    unstated assumption about the writer's float formatting (RedTeam 2026-05-30 Q3a).
    """
    stripped = value.strip()
    try:
        number = float(stripped)
    except ValueError:
        return stripped
    if number.is_integer():
        return str(int(number))
    return repr(number)


def benchmark_data_fingerprint(
    rows: list[dict[str, str]],
    columns: tuple[str, ...] = DETERMINISTIC_BENCHMARK_COLUMNS,
) -> str:
    """SHA-256 over only the deterministic benchmark columns, row-order-independent.

    The SHA-256 of the whole benchmark CSV changes on every run because the file
    embeds re-measured wall-clock timings (``pack_seconds``, ``unpack_seconds``,
    ``pack_throughput_mib_s``) — so it can never be reproduced by a reader and is at
    best a one-run provenance stamp. This fingerprint covers ONLY the run-invariant
    columns (:data:`DETERMINISTIC_BENCHMARK_COLUMNS`): ciphertext expansion follows the
    version-aware expansion model, manifest sizes are fixed by the export schema, and
    tamper outcomes are deterministic. It is therefore a genuine reproducibility anchor
    — a reader who regenerates the pipeline obtains the identical value, and a mismatch
    signals real corruption of the deterministic data rather than timing noise.

    Rows are projected onto ``columns`` in fixed order and sorted before hashing, so the
    fingerprint is independent of CSV row order. Missing columns serialize as empty for
    forward-compatibility. Returns :data:`EMPTY_DATA_FINGERPRINT` for an empty input.
    """
    if not rows:
        return EMPTY_DATA_FINGERPRINT
    projected = [
        _FIELD_SEP.join(_canonical_cell(str(row.get(col, ""))) for col in columns)
        for row in rows
    ]
    projected.sort()
    canonical = _ROW_SEP.join(projected).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

# Two-sided Student-t critical values t(df, 0.975) for small-df 95% CIs. The
# release benchmark now uses many repetitions, but tests and local smoke runs can
# still use small n; these exact values keep that regime honest without scipy.
_T_CRIT_95: dict[int, float] = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
}
_NORMAL_975 = 1.959963984540054


def _large_df_t_critical_95(df: int) -> float:
    """Approximate ``t(df, 0.975)`` for df > 10 without a scipy dependency.

    Uses the standard inverse-t expansion around the normal quantile through
    O(df^-3). At the release benchmark's df=149 this is about 1.976, preserving
    the Student-t framing while avoiding a runtime statistics dependency.
    """
    v = float(df)
    z = _NORMAL_975
    return (
        z
        + (z**3 + z) / (4.0 * v)
        + (5.0 * z**5 + 16.0 * z**3 + 3.0 * z) / (96.0 * v**2)
        + (3.0 * z**7 + 19.0 * z**5 + 17.0 * z**3 - 15.0 * z)
        / (384.0 * v**3)
    )


def _t_critical_95(df: int) -> float:
    """Two-sided 95% Student-t critical value for ``df`` degrees of freedom."""
    if df <= 0:
        return float("nan")
    if df in _T_CRIT_95:
        return _T_CRIT_95[df]
    return _large_df_t_critical_95(df)


def ci_method_description(n: int) -> str:
    """Human-readable method for the throughput confidence interval token."""
    if n <= 1:
        return "single observation; no interval is estimable"
    df = n - 1
    if df in _T_CRIT_95:
        return f"two-sided 95% Student-t interval using the tabulated t({df}, 0.975) critical value"
    return f"two-sided 95% Student-t interval using a no-SciPy large-df expansion for t({df}, 0.975)"


@dataclass(frozen=True)
class SummaryStats:
    """Dispersion summary for a sample of repeated measurements.

    All fields are population-honest for small n: ``sd`` is the sample standard
    deviation (n-1), ``sem`` the standard error of the mean, and ``ci95_lo/hi`` a
    two-sided Student-t 95% confidence interval on the mean. For ``n == 1`` the
    dispersion fields are 0.0 / the point value (no spread is estimable); for an
    exact metric (all values identical, e.g. expansion ratio) sd/cv collapse to 0.0,
    which is the honest signal that the metric carries no measurement noise.
    """

    n: int
    mean: float
    sd: float
    cv: float  # coefficient of variation = sd / mean (dimensionless), 0 when mean == 0
    sem: float
    ci95_lo: float
    ci95_hi: float


def summary_stats(values: list[float]) -> SummaryStats:
    """Compute mean / sd / cv / sem / 95% t-CI for a sample.

    Raises ``ValueError`` on an empty sample — a dispersion summary of nothing is
    meaningless and must fail loudly rather than return a misleading zero.
    """
    if not values:
        raise ValueError("summary_stats requires at least one value")
    n = len(values)
    m = mean(values)
    if n == 1:
        return SummaryStats(n=1, mean=m, sd=0.0, cv=0.0, sem=0.0, ci95_lo=m, ci95_hi=m)
    try:
        sd = stdev(values)  # sample (n-1) standard deviation
    except StatisticsError:  # pragma: no cover - guarded by n==1 above
        sd = 0.0
    cv = (sd / m) if m != 0 else 0.0
    sem = sd / (n**0.5)
    half = _t_critical_95(n - 1) * sem
    return SummaryStats(
        n=n, mean=m, sd=sd, cv=cv, sem=sem, ci95_lo=m - half, ci95_hi=m + half
    )


def base_condition(condition: str) -> str:
    """Strip the repetition suffix (``_r0``/``_r1``/...) from a condition label.

    Repetitions are encoded in the condition name (``medium_tracks_r0``,
    ``medium_tracks_r1``, ...); grouping by base condition recovers the repeated
    sample for dispersion statistics.
    """
    return re.sub(r"_r\d+$", "", condition)


def repetition_values(
    rows: list[dict[str, str]], spec: FigureSpec, field: str
) -> list[float]:
    """All values of ``field`` across repetitions matching ``spec`` filters.

    Mirrors ``avg_field``'s filtering but returns the full sample (one value per
    repetition) so dispersion can be computed instead of only the mean.
    """
    return [float(row[field]) for row in filter_rows_for_spec(rows, spec)]


def field_summary(
    rows: list[dict[str, str]], spec: FigureSpec, field: str
) -> SummaryStats | None:
    """``SummaryStats`` for ``field`` over rows matching ``spec``; None if empty."""
    values = repetition_values(rows, spec, field)
    if not values:
        return None
    return summary_stats(values)


#: Fixed per-track AEAD header for the default format: ``nonce || tag``. Padded
#: formats add PADMÉ bucketed plaintext after this header.
TRACK_HEADER_BYTES = nonce_size_for(FORMAT_VERSION) + TAG_SIZE


def expansion_ratio_model(
    plaintext_bytes: float,
    *,
    format_version: str = FORMAT_VERSION,
    header_bytes: int | None = None,
) -> float:
    """Version-aware ciphertext-expansion ratio for one track.

    Unpadded formats store ``nonce || tag || ciphertext`` with AES-GCM preserving
    plaintext length, so ``r(n) = (H + n) / n``. Padded formats first serialize the
    plaintext as ``uint64_len || payload || zero padding`` to the PADMÉ bucket, so
    ``r(n) = (H + padme(n + 8)) / n``. This remains a spec identity, not a fit.
    """
    if plaintext_bytes <= 0:
        raise ValueError("plaintext_bytes must be positive")
    if int(plaintext_bytes) != plaintext_bytes:
        raise ValueError("plaintext_bytes must be an integer byte count")
    n = int(plaintext_bytes)
    header = header_bytes if header_bytes is not None else nonce_size_for(format_version) + TAG_SIZE
    body = padme(n + 8) if pads_payload(format_version) else n
    return (header + body) / n


def max_expansion_ratio_residual(rows: list[dict[str, str]]) -> float:
    """Largest absolute gap between measured ``expansion_ratio`` and the model."""
    residuals = [
        abs(
            float(row["expansion_ratio"])
            - expansion_ratio_model(
                int(row["plaintext_bytes"]),
                format_version=row.get("format_version", FORMAT_VERSION),
            )
        )
        for row in rows
        if int(row.get("plaintext_bytes", 0)) > 0
        and row.get("expansion_ratio") not in (None, "")
    ]
    return max(residuals) if residuals else 0.0


def avg_field(rows: list[dict[str, str]], spec: FigureSpec, field: str) -> float | None:
    """Mean of ``field`` over rows matching ``spec`` filters."""
    subset = filter_rows_for_spec(rows, spec)
    if not subset:
        return None
    return mean(float(row[field]) for row in subset)


def tamper_detected_count(rows: list[dict[str, str]]) -> int:
    """Count benchmark rows with successful tamper detection."""
    return sum(1 for row in rows if is_tamper_detected(row))


def result_table_rows(rows: list[dict[str, str]], spec: FigureSpec) -> str:
    """Markdown table body rows for rows matching ``spec``."""
    subset = sorted(filter_rows_for_spec(rows, spec), key=lambda row: row["track_id"])
    return "\n".join(
        f"| {row['track_id']} | {row['track_type']} | {row['plaintext_bytes']} | "
        f"{row['expansion_ratio']} | {row['pack_throughput_mib_s']} |"
        for row in subset
    )


def avg_pack_seconds(rows: list[dict[str, str]], spec: FigureSpec) -> float | None:
    """Mean pack wall time for rows matching ``spec`` filters."""
    return avg_field(rows, spec, "pack_seconds")


def avg_manifest_bytes(rows: list[dict[str, str]], track_id: str, level: int) -> str:
    """Average manifest bytes for a track at an observability level."""
    matching = [
        row
        for row in rows
        if row.get("track_id") == track_id
        and int(row.get("observability_level", -1)) == level
    ]
    if not matching:
        return "N/A"
    avg = sum(int(row["manifest_bytes"]) for row in matching) / len(matching)
    return str(round(avg))
