"""Declarative figure registry for ENTO benchmark plots."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .benchmark_filters import (
    AUDITABLE_LEVEL,
    MEDIUM_TRACK_PREFIX,
    OBSERVABILITY_FIGURE_TRACK,
    SMALL_TRACKS_R0_PREFIX,
    filter_rows,
)
from .benchmark_io import benchmark_csv_path
from .crypto import NONCE_SIZE, TAG_SIZE

_TRACK_HEADER_BYTES = NONCE_SIZE + TAG_SIZE
_CSV_SOURCE = "`ento_benchmark_results.csv`"

_VISUAL_CONTRACTS: Final[dict[str, tuple[str, str, str]]] = {
    "fig:benchmark_overview": (
        "Orients readers to the four headline benchmark surfaces.",
        "Composite of registered throughput, expansion, observability, and tamper views.",
        "Summary panel only; use standalone figures for exact filters and labels.",
    ),
    "fig:throughput_benchmark": (
        "Shows local pack-throughput dispersion for the medium synthetic track.",
        "Wall-clock `pack_throughput_mib_s` rows filtered to auditable medium tracks.",
        "Host-state timing snapshot; not a cross-host performance superiority claim.",
    ),
    "fig:expansion_ratio": (
        "Shows per-fixture ciphertext expansion under the default profile.",
        "Data-derived plaintext and ciphertext byte counts from fixture tracks.",
        "Small-track overhead is expected; do not generalize the ratio to all payload sizes.",
    ),
    "fig:expansion_heatmap": (
        "Separates fixed-header overhead from payload size across benchmark conditions.",
        "Mean expansion ratios by base condition and track id.",
        "Color intensity encodes ratios, not security strength.",
    ),
    "fig:observability_manifest_size": (
        "Shows the manifest-size cost of each observability level for the EEG fixture.",
        "Manifest byte counts across exported levels for `track_id=eeg`.",
        "Manifest redaction does not hide ZIP names, member presence, or bucketed size.",
    ),
    "fig:unpack_latency": (
        "Compares local pack and verify-before-unpack wall-clock costs.",
        "Mean `pack_seconds` and `unpack_seconds` for auditable medium-track rows.",
        "Timing includes local host conditions and should be interpreted with dispersion figures.",
    ),
    "fig:throughput_by_observability": (
        "Checks whether manifest redaction changes medium-track pack throughput locally.",
        "Per-level throughput means with min-max repetition bands.",
        "Flatness is local-run evidence, not a portable performance law.",
    ),
    "fig:observability_throughput_tradeoff": (
        "Visualizes manifest-size versus throughput coupling in the generated matrix.",
        "Medium-track manifest bytes and pack throughput rows.",
        "Scatter shape is exploratory and does not establish causality.",
    ),
    "fig:manifest_multitrack": (
        "Compares observability redaction behavior across heterogeneous fixture tracks.",
        "Manifest byte counts by level for eeg, vcf, and spectrogram fixtures.",
        "Only manifest size is plotted; encrypted payload bytes are unchanged by export level.",
    ),
    "fig:crypto_overhead": (
        "Decomposes each track member into fixed AEAD header and encrypted body bytes.",
        "Ciphertext byte counts and the code-defined nonce/tag header size.",
        "The body includes padding; the stack is byte composition, not runtime cost.",
    ),
    "fig:expansion_law": (
        "Binds measured expansion ratios to the version-aware closed-form model.",
        "Fixture byte counts, format version, and `expansion_ratio_model` residuals.",
        "The law covers stored member bytes, not compression or transport overhead.",
    ),
    "fig:throughput_dispersion": (
        "Shows timing variability instead of hiding it behind one mean.",
        "Per-repetition medium-track throughput plus Student-t interval summary.",
        "The confidence interval describes this release run under local conditions.",
    ),
    "fig:determinism_cv": (
        "Explains why deterministic columns are fingerprinted and timing columns are not.",
        "Coefficient of variation by benchmark metric and fingerprint column class.",
        "Zero CV is a generated-matrix property, not proof that every future metric is deterministic.",
    ),
    "fig:format_ladder": (
        "Summarizes the supported wire-format ladder and default writer choice.",
        "Code-owned supported-format constants and hardening features.",
        "Compatibility support does not mean older formats are the current default.",
    ),
    "fig:format_compatibility_matrix": (
        "Makes read/write/default and hardening features explicit per format.",
        "Supported format dispatch, nonce policy, AAD policy, and padding policy.",
        "A yes/no cell is capability metadata, not an interoperability certification.",
    ),
    "fig:length_leakage_profile": (
        "Contrasts exact legacy length leakage with default PADME bucket disclosure.",
        "Version-aware member-size model over small plaintext lengths.",
        "PADME hides exact length only to buckets; ZIP metadata remains visible.",
    ),
    "fig:conformance_outcomes": (
        "Shows known-good and known-bad fixture expectations for all supported formats.",
        "Deterministic conformance cases generated and verified by `src/conformance.py`.",
        "Fixture coverage is a release gate, not independent implementation diversity.",
    ),
    "fig:observability_redaction_matrix": (
        "Shows which manifest fields survive each export level.",
        "Code-documented observability policy for manifest field classes.",
        "This matrix describes manifest exports, not cryptographic decryption policy.",
    ),
    "fig:release_evidence_map": (
        "Maps the release candidate to its generated evidence surfaces.",
        "Benchmark, figure, conformance, SBOM, checksum, PDF, and HTML artifacts.",
        "Evidence completeness is local until public endpoints and signatures exist.",
    ),
    "fig:security_control_matrix": (
        "Separates repository-enforced controls from deployment-residual controls.",
        "Threat IDs, code/tests/docs coverage, and external-control annotations.",
        "External cells require operator infrastructure outside `.ento.zip`.",
    ),
    "fig:tamper_detection": (
        "Reports generated tag-byte tamper rejection across the benchmark matrix.",
        "Tamper rows produced by benchmark corruptions and key-based unpack outcomes.",
        "This covers generated tag-byte corruption, not every possible misuse scenario.",
    ),
}


def visual_contract_for_label(label: str) -> dict[str, str]:
    """Return reader-facing takeaway/evidence/caution metadata for a figure."""
    takeaway, evidence, caution = _VISUAL_CONTRACTS[label]
    return {"takeaway": takeaway, "evidence": evidence, "caution": caution}


def visual_contract_for_spec(spec: FigureSpec) -> dict[str, str]:
    """Return visual contract metadata for a registered figure."""
    return visual_contract_for_label(spec.label)


def spec_filter_description(spec: FigureSpec) -> str:
    """Human-readable CSV filter phrase shared by plots, captions, and docs."""
    parts: list[str] = []
    if spec.condition_prefix:
        parts.append(f"condition `{spec.condition_prefix}*`")
    if spec.observability_level is not None:
        parts.append(f"observability level {spec.observability_level}")
    if spec.track_id:
        parts.append(f"track_id={spec.track_id}")
    return ", ".join(parts) if parts else "all benchmark rows"


def plot_title(headline: str, spec: FigureSpec) -> str:
    """Axis title aligned with ``FigureSpec`` filters."""
    desc = spec_filter_description(spec)
    if desc == "all benchmark rows":
        return headline
    return f"{headline}\n{desc}"


def figure_caption(
    summary: str,
    spec: FigureSpec,
    *,
    generator_name: str,
    extra: str = "",
) -> str:
    """Registry caption: summary, filters, CSV source, generator."""
    filters = spec_filter_description(spec)
    tail = f" {extra}" if extra else ""
    return (
        f"{summary} Filters: {filters}.{tail} Data from {_CSV_SOURCE}. "
        f"Generated by `{generator_name}` in `src/figures.py`."
    )


MANUSCRIPT_SECTION_FILES: Final[dict[str, str]] = {
    "results": "03_results.md",
    "benchmark_interp": "03a_benchmark_interpretation.md",
    "methodology": "02_methodology.md",
    "security": "02c_security_verification.md",
    "reproducibility": "06_reproducibility.md",
}


@dataclass(frozen=True)
class FigureSpec:
    """Single manuscript figure backed by a generator in ``figures.py``."""

    label: str
    filename: str
    caption: str
    generator_name: str
    kind: str
    manuscript_section: str
    figsize_key: str = "single"
    width_percent: int | None = None
    module: str = "src.figures"
    condition_prefix: str | None = None
    observability_level: str | None = None
    track_id: str | None = None
    # Determinism contract: ``data_derived`` figures plot only byte-count / ratio
    # columns of the CSV and MUST regenerate byte-identically from a fixed CSV.
    # Figures with ``data_derived=False`` plot wall-clock timing columns
    # (pack/unpack seconds, throughput), which legitimately vary run-to-run, so
    # they are byte-stable only for a *fixed* CSV, not across re-measurement.
    # ``tests/test_figure_determinism.py`` enforces this split.
    data_derived: bool = True

    @property
    def generated_by(self) -> str:
        return f"{self.module}::{self.generator_name}"


def _registered_spec(
    *,
    summary: str,
    label: str,
    filename: str,
    generator_name: str,
    kind: str,
    manuscript_section: str,
    extra: str = "",
    figsize_key: str = "single",
    width_percent: int | None = None,
    condition_prefix: str | None = None,
    observability_level: str | None = None,
    track_id: str | None = None,
    caption: str | None = None,
    data_derived: bool = True,
) -> FigureSpec:
    """Build a ``FigureSpec`` with registry caption from filter fields."""
    stub = FigureSpec(
        label=label,
        filename=filename,
        caption="",
        generator_name=generator_name,
        kind=kind,
        manuscript_section=manuscript_section,
        figsize_key=figsize_key,
        width_percent=width_percent,
        condition_prefix=condition_prefix,
        observability_level=observability_level,
        track_id=track_id,
        data_derived=data_derived,
    )
    resolved_caption = (
        caption
        if caption is not None
        else figure_caption(summary, stub, generator_name=generator_name, extra=extra)
    )
    return FigureSpec(
        label=label,
        filename=filename,
        caption=resolved_caption,
        generator_name=generator_name,
        kind=kind,
        manuscript_section=manuscript_section,
        figsize_key=figsize_key,
        width_percent=width_percent,
        condition_prefix=condition_prefix,
        observability_level=observability_level,
        track_id=track_id,
        data_derived=data_derived,
    )


def _build_figure_specs() -> tuple[FigureSpec, ...]:
    throughput = _registered_spec(
        summary=(
            "Pack throughput, in MiB/s, against plaintext size for the medium synthetic-track condition. "
            "Each marker is one repetition (jittered horizontally to separate coincident points); the dashed "
            "line marks the mean across repetitions. This is a local wall-clock snapshot: it reports measured "
            "dispersion for the configured release run and does not assert cross-host or cross-implementation "
            "throughput superiority."
        ),
        label="fig:throughput_benchmark",
        data_derived=False,
        filename="throughput_benchmark.png",
        generator_name="generate_throughput_figure",
        kind="scatter",
        manuscript_section="results",
        condition_prefix=MEDIUM_TRACK_PREFIX,
        observability_level=AUDITABLE_LEVEL,
    )
    expansion = _registered_spec(
        summary=(
            "Ciphertext-to-plaintext expansion ratio per fixture track, with the exact ratio printed above each bar. "
            f"Expansion combines the {_TRACK_HEADER_BYTES}-byte per-track AEAD header (nonce plus authentication tag) "
            "with the version-selected ciphertext body; the default 0.4.0 profile PADME-pads that body, so small "
            "tracks pay proportionally more overhead while larger tracks approach a ratio of one."
        ),
        label="fig:expansion_ratio",
        filename="expansion_ratio.png",
        generator_name="generate_expansion_figure",
        kind="bar",
        manuscript_section="results",
        condition_prefix=SMALL_TRACKS_R0_PREFIX,
        observability_level=AUDITABLE_LEVEL,
    )
    heatmap = _registered_spec(
        summary=(
            "Mean ciphertext expansion ratio for each base benchmark condition (rows, with repetition suffixes "
            "collapsed) crossed with every track id (columns), rendered on the colorblind-safe cividis map where "
            "brighter (yellow) cells mark higher overhead and darker (blue) cells mark lower overhead. The exact "
            "ratio is overlaid on each cell. "
            "Small fixture tracks light up; the large synthetic medium track stays dark, isolating fixed header "
            "cost from payload size at a glance."
        ),
        label="fig:expansion_heatmap",
        filename="expansion_heatmap.png",
        generator_name="generate_expansion_heatmap_figure",
        kind="heatmap",
        manuscript_section="results",
        observability_level=AUDITABLE_LEVEL,
        figsize_key="wide",
    )
    observability = _registered_spec(
        summary=(
            "Exported manifest size, in bytes, against observability level for the EEG fixture, with each point "
            "labelled by its byte count. Size falls monotonically as the export level drops from auditable to sealed: "
            "each step removes a field class (plaintext digests, then resolution descriptors, then type URIs) without "
            "re-encrypting the payload, making the confidentiality-versus-auditability trade-off directly measurable."
        ),
        label="fig:observability_manifest_size",
        filename="observability_manifest_size.png",
        generator_name="generate_observability_figure",
        kind="line",
        manuscript_section="results",
        condition_prefix=SMALL_TRACKS_R0_PREFIX,
        track_id=OBSERVABILITY_FIGURE_TRACK,
    )
    unpack_latency = _registered_spec(
        summary=(
            "Mean pack and unpack wall-clock time, in seconds, for the medium-track condition, with the exact time "
            "printed above each bar. In this local run, unpack carries the additional cost of authenticating the AEAD "
            "tag and checking plaintext digests before any bytes are released, so it is the more expensive half of "
            "the measured round trip — the price of verify-before-use."
        ),
        label="fig:unpack_latency",
        data_derived=False,
        filename="unpack_latency.png",
        generator_name="generate_unpack_latency_figure",
        kind="bar",
        manuscript_section="benchmark_interp",
        condition_prefix=MEDIUM_TRACK_PREFIX,
        observability_level=AUDITABLE_LEVEL,
    )
    throughput_obs = _registered_spec(
        summary=(
            "Pack throughput, in MiB/s, against observability level for the medium-track condition: the solid line "
            "is the per-level mean and the shaded band spans the min-max across repetitions. Throughput is largely "
            "flat across levels in this local run. Redaction trims manifest fields at export time and never touches the "
            "encrypted payload, consistent with observability being a metadata-only control."
        ),
        label="fig:throughput_by_observability",
        data_derived=False,
        filename="throughput_by_observability.png",
        generator_name="generate_throughput_by_observability_figure",
        kind="line",
        manuscript_section="benchmark_interp",
        condition_prefix=MEDIUM_TRACK_PREFIX,
        figsize_key="wide",
    )
    tradeoff = _registered_spec(
        summary=(
            "Exported manifest size, in bytes, against pack throughput, in MiB/s, for the medium-track condition — "
            "one point per benchmark row. In this local run, the panel does not show a visible downward trend, so the "
            "generated matrix treats manifest size and payload throughput as empirically decoupled rather than as a "
            "portable performance law."
        ),
        label="fig:observability_throughput_tradeoff",
        data_derived=False,
        filename="observability_tradeoff.png",
        generator_name="generate_observability_tradeoff_figure",
        kind="scatter",
        manuscript_section="benchmark_interp",
        condition_prefix=MEDIUM_TRACK_PREFIX,
        observability_level=AUDITABLE_LEVEL,
    )
    manifest_mt = _registered_spec(
        summary=(
            "Exported manifest size, in bytes, against observability level for all three fixture tracks "
            "(eeg, vcf, spectrogram) on one axis, one line per track. The curves shrink in parallel as the export "
            "level drops, showing that graded redaction behaves uniformly across heterogeneous modalities rather "
            "than favouring any one track type."
        ),
        label="fig:manifest_multitrack",
        filename="manifest_multitrack.png",
        generator_name="generate_manifest_multitrack_figure",
        kind="line",
        manuscript_section="methodology",
        condition_prefix=SMALL_TRACKS_R0_PREFIX,
        figsize_key="wide",
    )
    crypto = _registered_spec(
        summary=(
            f"Per-track ciphertext decomposed into its two parts: the fixed {_TRACK_HEADER_BYTES}-byte default 0.4.0 "
            "AEAD header (nonce plus authentication tag, bottom segment) and the variable ciphertext body (top "
            "segment), stacked per fixture track. The body includes PADME length padding under the default profile, "
            "so the bar shows both fixed authentication overhead and bucketed length-hiding overhead."
        ),
        label="fig:crypto_overhead",
        filename="crypto_overhead.png",
        generator_name="generate_crypto_overhead_figure",
        kind="bar",
        manuscript_section="methodology",
        condition_prefix=SMALL_TRACKS_R0_PREFIX,
        observability_level=AUDITABLE_LEVEL,
    )
    expansion_law = _registered_spec(
        summary=(
            "Measured ciphertext expansion ratio (markers, one per fixture track) overlaid on the version-aware "
            "model. For the default 0.4.0 profile, r(n) = (H + PADME(n + 8)) / n because the encrypted body carries "
            "an eight-byte original-length prefix before PADME bucketing; unpadded compatibility formats reduce to "
            "r(n) = (H + n) / n. The maximum absolute residual is reported as a fidelity badge, confirming a "
            "spec-fixed identity rather than a statistical fit."
        ),
        label="fig:expansion_law",
        filename="expansion_law.png",
        generator_name="generate_expansion_law_figure",
        kind="line",
        manuscript_section="benchmark_interp",
        figsize_key="wide",
        condition_prefix=SMALL_TRACKS_R0_PREFIX,
        observability_level=AUDITABLE_LEVEL,
    )
    throughput_dispersion = _registered_spec(
        summary=(
            "Per-repetition pack throughput for the medium-track condition with the mean (dashed) and a two-sided "
            "95% Student-t confidence interval (shaded band; t critical value for n-1 degrees of freedom, tabulated "
            "for small df and expanded for large df without scipy). Each marker is one repetition, drawn with sparse "
            "x-axis ticks for dense release runs; the inset reports token-derived n, sample standard deviation, and "
            "coefficient of variation. The band is the honest counterpart to the exact expansion law: wall-clock "
            "throughput carries host-specific measurement noise, so the mean alone would overstate precision."
        ),
        label="fig:throughput_dispersion",
        data_derived=False,
        filename="throughput_dispersion.png",
        generator_name="generate_throughput_dispersion_figure",
        kind="scatter",
        manuscript_section="benchmark_interp",
        condition_prefix=MEDIUM_TRACK_PREFIX,
        observability_level=AUDITABLE_LEVEL,
    )
    format_ladder = _registered_spec(
        summary=(
            "ENTO format ladder for the supported AES-256-GCM wire formats: compatibility 0.2.0, compatibility hardening "
            "formats 0.3.0 and 0.3.1, and the default 0.4.0 release-candidate wire profile with associated-data "
            "binding plus PADME length padding."
        ),
        label="fig:format_ladder",
        filename="format_ladder.png",
        generator_name="generate_format_ladder_figure",
        kind="ladder",
        manuscript_section="security",
        figsize_key="wide",
        caption=(
            "ENTO format ladder for supported AES-256-GCM wire formats. The default write format is 0.4.0; "
            "0.2.0, 0.3.0, and 0.3.1 remain version-dispatched compatibility formats. "
            "Filters: all benchmark rows. Data from `ento_benchmark_results.csv`. Generated by "
            "`generate_format_ladder_figure` in `src/figures.py`."
        ),
    )
    format_compatibility = _registered_spec(
        summary=(
            "Compatibility matrix for every supported ENTO wire format. It distinguishes read/write support from "
            "the default writer choice and shows which formats carry the 12-byte nonce, associated-data binding, "
            "and PADME length padding."
        ),
        label="fig:format_compatibility_matrix",
        filename="format_compatibility_matrix.png",
        generator_name="generate_format_compatibility_matrix_figure",
        kind="heatmap",
        manuscript_section="security",
        figsize_key="wide",
    )
    length_leakage = _registered_spec(
        summary=(
            "Track member bytes versus plaintext bytes for compatibility 0.2.0 and default 0.4.0. The 0.2.0 line rises "
            "one-for-one with plaintext length, while the 0.4.0 step profile reveals only PADME buckets plus the "
            "fixed AEAD header. The bucket size remains visible; this is mitigation of exact-length disclosure, "
            "not total traffic-analysis resistance."
        ),
        label="fig:length_leakage_profile",
        filename="length_leakage_profile.png",
        generator_name="generate_length_leakage_profile_figure",
        kind="line",
        manuscript_section="security",
        figsize_key="wide",
    )
    conformance_outcomes = _registered_spec(
        summary=(
            "Conformance fixture matrix for known-good and known-bad ENTO containers. Valid containers for every "
            "supported format must verify and unpack; tamper, duplicate-member, and path-escape fixtures must fail "
            "closed. The cases are generated deterministically by `src/conformance.py`."
        ),
        label="fig:conformance_outcomes",
        filename="conformance_outcomes.png",
        generator_name="generate_conformance_outcomes_figure",
        kind="heatmap",
        manuscript_section="security",
        figsize_key="wide",
    )
    observability_redaction = _registered_spec(
        summary=(
            "Manifest field-presence matrix for observability levels 0 through 3. The figure separates metadata "
            "redaction from cryptographic protection: lower levels remove type, resolution, digest, and declared "
            "length fields, while payload confidentiality and integrity are enforced by the encrypted track member."
        ),
        label="fig:observability_redaction_matrix",
        filename="observability_redaction_matrix.png",
        generator_name="generate_observability_redaction_matrix_figure",
        kind="heatmap",
        manuscript_section="methodology",
        figsize_key="wide",
    )
    release_evidence = _registered_spec(
        summary=(
            "Release evidence map for paper 0.4 and default format 0.4.0. The figure groups generated artifacts "
            "into benchmark metrics, registered visuals, conformance vectors, SBOM, checksums, and reader-facing "
            "PDF/HTML outputs so the release candidate is auditable as an artifact set rather than prose alone."
        ),
        label="fig:release_evidence_map",
        filename="release_evidence_map.png",
        generator_name="generate_release_evidence_map_figure",
        kind="bar",
        manuscript_section="reproducibility",
        figsize_key="wide",
    )
    security_control_matrix = _registered_spec(
        summary=(
            "Security-control matrix mapping the threat identifiers in docs/entofile-threat-model.md to implemented, "
            "partial, and external controls. It distinguishes repository-enforced checks from deployment controls such "
            "as signing, HSM/KMS custody, and SIEM ingestion that remain outside the reference implementation."
        ),
        label="fig:security_control_matrix",
        filename="security_control_matrix.png",
        generator_name="generate_security_control_matrix_figure",
        kind="heatmap",
        manuscript_section="security",
        figsize_key="wide",
        caption=(
            "Security-control matrix mapping ENTO threat IDs to repository-enforced, partial, and external controls. "
            "Implemented cells are backed by code/tests/docs in this repository; external cells require deployment "
            "environment controls such as artifact signing, HSM/KMS key custody, or SIEM routing. Filters: all "
            "benchmark rows. Data from `ento_benchmark_results.csv`. Generated by "
            "`generate_security_control_matrix_figure` in `src/figures.py`."
        ),
    )
    tamper = _registered_spec(
        summary=(
            "Tamper-injection outcomes across the full benchmark matrix as a 100%-stacked share of detected versus "
            "missed rejections. Each generated row flips one ciphertext tag byte and then attempts a key-based unpack, which "
            "must fail closed; the panel title reports the detected count and rate. A single solid 'detected' bar is "
            "the success condition for this generated matrix: keyed unpack rejected every injected tag-byte corruption."
        ),
        label="fig:tamper_detection",
        filename="tamper_detection.png",
        generator_name="generate_tamper_figure",
        kind="bar",
        manuscript_section="security",
        extra="Counts use is_tamper_detected in src/benchmark_filters.py.",
    )
    determinism_cv = _registered_spec(
        summary=(
            "Coefficient of variation (CV), in percent, of each benchmark metric across the repetitions of the "
            "medium-track condition, drawn as a horizontal bar per metric. The data-derived metrics — expansion "
            "ratio, ciphertext bytes, and manifest bytes — sit at exactly zero because they are fixed by the format "
            "and the manifest schema, while the wall-clock metrics — pack time, unpack time, and pack throughput — "
            "carry real run-to-run dispersion. This is the visual justification for the data fingerprint: it anchors "
            "only the zero-CV (deterministic) columns and reports the timing columns with their dispersion rather "
            "than hashing them."
        ),
        label="fig:determinism_cv",
        data_derived=False,
        filename="determinism_cv.png",
        generator_name="generate_determinism_cv_figure",
        kind="bar",
        manuscript_section="benchmark_interp",
        figsize_key="wide",
        condition_prefix=MEDIUM_TRACK_PREFIX,
        observability_level=AUDITABLE_LEVEL,
    )
    overview = FigureSpec(
        label="fig:benchmark_overview",
        filename="benchmark_overview.png",
        caption=figure_caption(
            "At-a-glance 2x2 summary of the four headline benchmark views, each reusing its standalone figure's "
            "filters: pack throughput against plaintext size (top-left), ciphertext expansion ratio by fixture track "
            "(top-right), EEG manifest size against observability level (bottom-left), and tamper-detection outcomes "
            "(bottom-right). Read together they show the local evidence for authenticated confidentiality, graded "
            "observability, format overhead, and timing dispersion. See the standalone figures for print-scale detail.",
            throughput,
            generator_name="generate_benchmark_overview_figure",
        ),
        generator_name="generate_benchmark_overview_figure",
        kind="panel",
        manuscript_section="results",
        figsize_key="panel",
        width_percent=95,
        data_derived=False,  # composite panel includes timing subplots
    )
    return (
        overview,
        throughput,
        expansion,
        heatmap,
        observability,
        unpack_latency,
        throughput_obs,
        tradeoff,
        manifest_mt,
        crypto,
        expansion_law,
        throughput_dispersion,
        determinism_cv,
        format_ladder,
        format_compatibility,
        length_leakage,
        conformance_outcomes,
        observability_redaction,
        release_evidence,
        security_control_matrix,
        tamper,
    )


FIGURE_SPECS: Final[tuple[FigureSpec, ...]] = _build_figure_specs()


def spec_by_label(label: str) -> FigureSpec:
    """Return the ``FigureSpec`` for a manuscript figure label."""
    for spec in FIGURE_SPECS:
        if spec.label == label:
            return spec
    raise KeyError(f"unknown figure label: {label!r}")


def filter_rows_for_spec(
    rows: list[dict[str, str]], spec: FigureSpec
) -> list[dict[str, str]]:
    """Apply ``FigureSpec`` CSV filter fields to benchmark rows."""
    return filter_rows(
        rows,
        condition_prefix=spec.condition_prefix,
        observability_level=spec.observability_level,
        track_id=spec.track_id,
    )


def caption_token(label: str) -> str:
    """Manuscript variable name for a figure's alt-text caption."""
    slug = label.removeprefix("fig:").upper().replace("-", "_")
    return f"FIG_CAPTION_{slug}"


def figure_caption_variables() -> dict[str, str]:
    """Export registry captions as ``{{FIG_CAPTION_*}}`` manuscript tokens."""
    return {caption_token(spec.label): spec.caption for spec in FIGURE_SPECS}


def figure_width_token(spec: FigureSpec, default_width: str) -> str:
    return str(spec.width_percent) if spec.width_percent is not None else default_width


def manuscript_image_markdown(spec: FigureSpec, *, default_width: str = "90") -> str:
    """Canonical Pandoc image line for a registered figure."""
    width = figure_width_token(spec, default_width)
    token = caption_token(spec.label)
    alt = "{{" + token + "}}"
    return (
        f"![{alt}](../output/figures/{spec.filename}){{#{spec.label} width={width}%}}"
    )


def specs_for_section(section: str) -> tuple[FigureSpec, ...]:
    """Return figures assigned to a manuscript section key."""
    return tuple(spec for spec in FIGURE_SPECS if spec.manuscript_section == section)


def figure_block_markdown(section: str, *, default_width: str = "90") -> str:
    """Concatenate image markdown lines for all figures in a section."""
    blocks = [
        manuscript_image_markdown(spec, default_width=default_width)
        for spec in specs_for_section(section)
    ]
    return "\n\n".join(blocks)


def figure_index_markdown() -> str:
    """Bullet list of registered figures for reproducibility sections."""
    lines = []
    for spec in FIGURE_SPECS:
        contract = visual_contract_for_spec(spec)
        determinism = "data-derived" if spec.data_derived else "timing-measured"
        lines.append(
            f"- `{spec.label}` -- `{spec.filename}` ({spec.kind}, "
            f"{spec.manuscript_section}, {determinism}): {contract['takeaway']}"
        )
    return "\n".join(lines)


def visual_evidence_contract_markdown() -> str:
    """Markdown table of figure takeaways, evidence classes, and cautions."""
    lines = [
        "| Figure | Takeaway | Evidence | Caution |",
        "| --- | --- | --- | --- |",
    ]
    for spec in FIGURE_SPECS:
        contract = visual_contract_for_spec(spec)
        lines.append(
            f"| `{spec.label}` | {contract['takeaway']} | "
            f"{contract['evidence']} | {contract['caution']} |"
        )
    return "\n".join(lines)


def _resolve_generator(name: str) -> Callable[[Path, Path], Path]:
    from . import figures

    allowed = {spec.generator_name for spec in FIGURE_SPECS}
    if name not in allowed:
        raise KeyError(f"unknown figure generator: {name}")
    return getattr(figures, name)


def generate_all_figures(csv_path: Path, figures_dir: Path) -> dict[str, Path]:
    """Run every registered generator; return label → PNG path."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    for spec in FIGURE_SPECS:
        generator = _resolve_generator(spec.generator_name)
        out = generator(csv_path, figures_dir / spec.filename)
        outputs[spec.label] = out
    return outputs


def _registry_entry(
    spec: FigureSpec, output_path: Path, csv_source: str
) -> dict[str, str]:
    contract = visual_contract_for_spec(spec)
    return {
        "label": spec.label,
        "filename": str(output_path),
        "caption": spec.caption,
        "caption_token": caption_token(spec.label),
        "takeaway": contract["takeaway"],
        "evidence": contract["evidence"],
        "caution": contract["caution"],
        "generated_by": spec.generated_by,
        "kind": spec.kind,
        "manuscript_section": spec.manuscript_section,
        "csv_source": csv_source,
        "condition_prefix": spec.condition_prefix or "",
        "observability_level": spec.observability_level or "",
        "track_id": spec.track_id or "",
        "data_derived": str(spec.data_derived).lower(),
    }


def write_figure_registry(project_root: Path, outputs: dict[str, Path]) -> Path:
    """Persist registry JSON consumed by validation and manuscript docs."""
    registry_path = project_root / "output" / "figures" / "figure_registry.json"
    csv_source = str(benchmark_csv_path(project_root))
    payload = {
        spec.label: _registry_entry(spec, outputs[spec.label], csv_source)
        for spec in FIGURE_SPECS
        if spec.label in outputs
    }
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return registry_path


def register_with_infrastructure(project_root: Path, outputs: dict[str, Path]) -> None:
    """Register figures with infrastructure FigureManager when available."""
    try:
        from infrastructure.documentation.figure_manager import (
            FigureManager,  # type: ignore[import-not-found]  # template infra, runtime-only
        )
    except ImportError:
        return
    registry_path = project_root / "output" / "figures" / "figure_registry.json"
    fm = FigureManager(registry_file=str(registry_path))
    csv_source = str(benchmark_csv_path(project_root))
    for spec in FIGURE_SPECS:
        path = outputs.get(spec.label)
        if path is not None:
            fm.register_figure(
                str(path),
                spec.caption,
                label=spec.label,
                section=spec.manuscript_section,
                generated_by=spec.generated_by,
                metadata={
                    "csv_source": csv_source,
                    "caption_token": caption_token(spec.label),
                    "kind": spec.kind,
                    **visual_contract_for_spec(spec),
                },
            )
