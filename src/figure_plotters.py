"""Plot functions for ENTO benchmark figures (called from ``figures.py``)."""

from __future__ import annotations

from collections import defaultdict
from math import ceil
from statistics import mean
from typing import TYPE_CHECKING

from matplotlib.axes import Axes
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from .benchmark_filters import is_tamper_detected
from .crypto import NONCE_SIZE, TAG_SIZE
from .figure_registry import (
    FigureSpec,
    filter_rows_for_spec,
    plot_title,
    spec_by_label,
)
from .viz_theme import (
    active_palette,
    annotate_bar_values,
    line_width,
    annotate_enabled,
    color_cycle,
    heatmap_cmap,
    markersize,
    open_figure,
    open_panel,
    save_figure,
    scatter_size,
    style_axes,
)

if TYPE_CHECKING:
    from pathlib import Path

_TRACK_HEADER_BYTES = NONCE_SIZE + TAG_SIZE


def _prune_edge_ticks(ax: Axes, *, x: bool = False, y: bool = False) -> None:
    """Drop auto ticks at the exact plot edge so labels do not clip in print."""
    if x:
        ax.xaxis.set_major_locator(MaxNLocator(nbins=6, prune="both"))
    if y:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6, prune="both"))


def _sparse_repetition_ticks(n: int, *, max_ticks: int = 8) -> list[int]:
    """Readable 1-based x ticks for dense repetition plots."""
    if n <= 0:
        return []
    if n <= max_ticks:
        return list(range(1, n + 1))
    step = ceil((n - 1) / float(max_ticks - 1))
    ticks = list(range(1, n + 1, step))
    if ticks[-1] != n:
        ticks.append(n)
    return ticks


def _empty_title(ax: Axes, spec: FigureSpec, headline: str) -> None:
    ax.set_title(plot_title(headline, spec))
    ax.text(
        0.5,
        0.5,
        "No matching benchmark rows",
        ha="center",
        va="center",
        transform=ax.transAxes,
    )


def plot_throughput(rows: list[dict[str, str]], ax: Axes, spec: FigureSpec) -> None:
    medium_rows = filter_rows_for_spec(rows, spec)
    sizes = [int(row["plaintext_bytes"]) for row in medium_rows]
    rates = [float(row["pack_throughput_mib_s"]) for row in medium_rows]
    headline = "ENTO pack throughput (medium tracks)"
    if not sizes:
        _empty_title(ax, spec, headline)
        return
    sizes_kib = [size / 1024.0 for size in sizes]
    jitter = [0.02 * (i % 3 - 1) * size for i, size in enumerate(sizes_kib)]
    x = [size + j for size, j in zip(sizes_kib, jitter, strict=True)]
    ax.scatter(
        x,
        rates,
        color=active_palette()[0],
        s=scatter_size(),
        alpha=0.8,
        edgecolors="white",
        linewidths=0.8,
        label="Repetitions",
    )
    avg_rate = mean(rates)
    ax.axhline(
        avg_rate,
        color=active_palette()[1],
        linestyle="--",
        linewidth=line_width(),
        label=f"Mean ({avg_rate:.2f} MiB/s)",
    )
    ax.margins(x=0.12, y=0.12)
    ax.set_xticks([round(mean(sizes_kib), 1)])
    _prune_edge_ticks(ax, y=True)
    ax.set_xlabel("Plaintext size (KiB)")
    ax.set_ylabel("Pack throughput (MiB/s)")
    ax.set_title(plot_title(headline, spec))
    ax.legend(loc="best", framealpha=0.95)


def plot_expansion(rows: list[dict[str, str]], ax: Axes, spec: FigureSpec) -> None:
    subset = filter_rows_for_spec(rows, spec)
    ordered = sorted(subset, key=lambda row: row["track_id"])
    labels = [row["track_id"] for row in ordered]
    ratios = [float(row["expansion_ratio"]) for row in ordered]
    headline = "ENTO expansion ratio by track"
    if not labels:
        _empty_title(ax, spec, headline)
        return
    bars = ax.bar(labels, ratios, color=color_cycle(len(labels)))
    annotate_bar_values(ax, bars, ratios, fmt="{:.3f}")
    ax.set_xlabel("Fixture track")
    ax.set_ylabel("Ciphertext / plaintext")
    ax.set_title(plot_title(headline, spec))


def plot_observability(rows: list[dict[str, str]], ax: Axes, spec: FigureSpec) -> None:
    subset = filter_rows_for_spec(rows, spec)
    ordered = sorted(subset, key=lambda row: int(row["observability_level"]))
    levels = [int(row["observability_level"]) for row in ordered]
    sizes = [int(row["manifest_bytes"]) for row in ordered]
    headline = "Manifest size vs observability"
    if not levels:
        _empty_title(ax, spec, headline)
        return
    ax.plot(
        levels,
        sizes,
        marker="o",
        color=active_palette()[2],
        linewidth=line_width(),
        markersize=markersize(),
    )
    if annotate_enabled():
        for level, size in zip(levels, sizes, strict=True):
            ax.annotate(
                f"{size} B",
                (level, size),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=9,
            )
    ax.set_xticks(levels)
    ax.margins(x=0.08, y=0.12)
    ax.set_yticks(sorted(set(sizes)))
    ax.set_xlabel("Observability level")
    ax.set_ylabel("Manifest size (bytes)")
    ax.set_title(plot_title(headline, spec))


def plot_tamper(rows: list[dict[str, str]], ax: Axes, _spec: FigureSpec) -> None:
    detected = sum(1 for row in rows if is_tamper_detected(row))
    total = len(rows)
    missed = total - detected
    headline = "Tamper rejection"
    if total == 0:
        _empty_title(ax, _spec, headline)
        return
    # Single 100%-stacked bar: detected (bottom) + missed (top) sum to 100% of rows.
    segments = [
        ("Detected", detected, active_palette()[2]),
        ("Missed", missed, active_palette()[3]),
    ]
    bottom = 0.0
    for label, count, color in segments:
        if count == 0:
            continue
        pct = count / total * 100.0
        ax.bar(
            "All benchmark rows",
            pct,
            bottom=bottom,
            color=color,
            label=label,
            width=0.5,
        )
        if annotate_enabled():
            ax.text(
                0,
                bottom + pct / 2.0,
                f"{label}\n{count}/{total} ({pct:.0f}%)",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )
        bottom += pct
    ax.set_ylim(0, 100)
    ax.set_ylabel("Share of benchmark rows (%)")
    rate_pct = 100.0 * detected / total
    ax.set_title(
        plot_title(f"{headline} ({detected}/{total} detected, {rate_pct:.0f}%)", _spec)
    )
    ax.legend(loc="lower right", framealpha=0.95)


def plot_format_ladder(
    _rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Show the supported ENTO format ladder and what each step hardens."""
    from .crypto import FORMAT_VERSION, FORMAT_VERSION_LATEST

    rows = [
        ("0.2.0", "compat", "16 B nonce\nno AAD\nno padding"),
        ("0.3.0", "compat", "12 B nonce\nformat+track AAD\nno padding"),
        ("0.3.1", "compat", "12 B nonce\nformat+track AAD\nPADME padding"),
        ("0.4.0", "default", "12 B nonce\nformat+track AAD\nPADME padding"),
    ]
    colors = color_cycle(len(rows))
    y = list(range(len(rows)))
    ax.barh(y, [1.0] * len(rows), color=colors, alpha=0.86)
    ax.set_yticks(y, labels=[item[0] for item in rows])
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_xlabel("")
    ax.set_title(plot_title("ENTO format ladder", spec))
    for idx, (version, role, detail) in enumerate(rows):
        marker = "latest" if version == FORMAT_VERSION_LATEST else role
        if version == FORMAT_VERSION:
            marker = "default"
        ax.text(
            0.03,
            idx,
            f"{marker}",
            va="center",
            ha="left",
            color="white",
            fontweight="bold",
        )
        ax.text(
            0.28,
            idx,
            detail,
            va="center",
            ha="left",
            color="white",
            fontsize=8,
        )
    ax.invert_yaxis()
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)


def plot_format_compatibility_matrix(
    _rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Matrix of read/write and hardening properties for supported formats."""
    from . import crypto

    formats = list(crypto.SUPPORTED_FORMAT_VERSIONS)
    columns = ["Read", "Write", "Default", "12 B nonce", "AAD", "PADME"]
    matrix: list[list[int]] = []
    for version in formats:
        matrix.append(
            [
                1,
                1,
                1 if version == crypto.FORMAT_VERSION else 0,
                1 if crypto.nonce_size_for(version) == 12 else 0,
                1 if crypto.track_aad(version, "alpha") is not None else 0,
                1 if crypto.pads_payload(version) else 0,
            ]
        )
    cmap = ListedColormap(["#D8D8D8", active_palette()[2]])
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(columns)), labels=columns, rotation=25, ha="right")
    ax.set_yticks(range(len(formats)), labels=formats)
    ax.set_title(plot_title("Format compatibility matrix", spec))
    for row_idx, row in enumerate(matrix):
        for col_idx, value in enumerate(row):
            ax.text(
                col_idx,
                row_idx,
                "yes" if value else "no",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if value else "black",
                fontweight="bold" if value else "normal",
            )
    ax.grid(False)


def plot_length_leakage_profile(
    _rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Compare exact-length leakage with PADME bucketed member sizes."""
    from . import crypto
    from .padding import padme

    sizes = list(range(1, 257))
    legacy = [crypto.nonce_size_for("0.2.0") + TAG_SIZE + n for n in sizes]
    default = [
        crypto.nonce_size_for(crypto.FORMAT_VERSION) + TAG_SIZE + padme(n + 8)
        for n in sizes
    ]
    ax.plot(
        sizes,
        legacy,
        color=active_palette()[3],
        linewidth=line_width(),
        label="0.2.0 exact length",
    )
    ax.step(
        sizes,
        default,
        where="post",
        color=active_palette()[2],
        linewidth=line_width(),
        label="0.4.0 PADME bucket",
    )
    ax.set_xlabel("Plaintext bytes")
    ax.set_ylabel("Track member bytes")
    ax.set_title(plot_title("Length leakage profile", spec))
    ax.legend(loc="upper left", framealpha=0.95)
    _prune_edge_ticks(ax, x=True, y=True)


def plot_conformance_outcomes(
    _rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Known-good and known-bad conformance cases with expected outcomes."""
    from .conformance import BAD_CASES, GOOD_CASES

    cases = list(GOOD_CASES + BAD_CASES)
    checks = ["verify+key", "verify no key", "unpack"]
    matrix = [
        [
            int(case.expected_verify_with_key),
            int(case.expected_verify_without_key),
            int(case.expected_unpack),
        ]
        for case in cases
    ]
    cmap = ListedColormap([active_palette()[3], active_palette()[2]])
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(checks)), labels=checks, rotation=20, ha="right")
    ax.set_yticks(range(len(cases)), labels=[case.case_id for case in cases])
    ax.set_title(plot_title("Conformance fixture outcomes", spec))
    for row_idx, row in enumerate(matrix):
        for col_idx, value in enumerate(row):
            ax.text(
                col_idx,
                row_idx,
                "accept" if value else "reject",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
                fontweight="bold",
            )
    ax.grid(False)


def plot_observability_redaction_matrix(
    _rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Field-presence matrix for manifest observability levels."""
    levels = ["0 sealed", "1 typed", "2 resolved", "3 auditable"]
    fields = [
        "type URI",
        "resolution",
        "byte length",
        "cipher digest",
        "plain digest",
        "proof chain",
    ]
    matrix = [
        [0, 0, 0, 0, 0, 0],
        [1, 0, 1, 1, 0, 1],
        [1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 1],
    ]
    cmap = ListedColormap(["#D8D8D8", active_palette()[2]])
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(fields)), labels=fields, rotation=25, ha="right")
    ax.set_yticks(range(len(levels)), labels=levels)
    ax.set_title(plot_title("Observability redaction matrix", spec))
    for row_idx, row in enumerate(matrix):
        for col_idx, value in enumerate(row):
            ax.text(
                col_idx,
                row_idx,
                "kept" if value else "redacted",
                ha="center",
                va="center",
                fontsize=7,
                color="white" if value else "black",
                fontweight="bold" if value else "normal",
            )
    ax.grid(False)


def plot_release_evidence_map(
    _rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Release-candidate evidence surface tied to generated artifacts."""
    evidence = [
        ("Benchmark CSV", "metrics"),
        ("Figure registry", "visuals"),
        ("Conformance manifest", "formats"),
        ("SBOM", "supply chain"),
        ("Release manifest", "checksums"),
        ("PDF / HTML", "reader artifacts"),
    ]
    y = list(range(len(evidence)))
    colors = color_cycle(len(evidence))
    ax.barh(y, [1] * len(evidence), color=colors, alpha=0.88)
    ax.set_yticks(y, labels=[item[0] for item in evidence])
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title(plot_title("0.4 release evidence map", spec))
    for idx, (_name, role) in enumerate(evidence):
        ax.text(
            0.04,
            idx,
            role,
            va="center",
            ha="left",
            color="white",
            fontweight="bold",
            fontsize=9,
        )
    ax.invert_yaxis()
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)


def plot_security_control_matrix(
    _rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Threat-control coverage matrix used by the 0.4 security section."""
    threats = [
        "TM-001 path escape",
        "TM-002 ciphertext tamper",
        "TM-003 proof/manifest swap",
        "TM-004 ZIP DoS",
        "TM-005 crypto module risk",
        "TM-006 supply-chain swap",
        "TM-007 key mishandling",
        "TM-008 length disclosure",
    ]
    controls = ["Repo control", "Keyed verify", "Docs/gates", "External control"]
    # 2 = implemented, 1 = partial/documented, 0 = external/residual.
    matrix = [
        [2, 0, 2, 0],
        [2, 2, 2, 0],
        [1, 2, 2, 2],
        [2, 0, 2, 1],
        [1, 2, 2, 2],
        [1, 0, 2, 2],
        [1, 0, 2, 2],
        [1, 0, 2, 1],
    ]
    cmap_colors = ["#8A8A8A", active_palette()[1], active_palette()[2]]
    image = ax.imshow(
        matrix, cmap=ListedColormap(cmap_colors), vmin=0, vmax=2, aspect="auto"
    )
    del image
    ax.set_xticks(range(len(controls)), labels=controls, rotation=20, ha="right")
    ax.set_yticks(range(len(threats)), labels=threats)
    ax.set_title(plot_title("Security control coverage", spec))
    labels = {0: "external", 1: "partial", 2: "implemented"}
    for row_idx, row in enumerate(matrix):
        for col_idx, value in enumerate(row):
            ax.text(
                col_idx,
                row_idx,
                labels[value],
                ha="center",
                va="center",
                color="white" if value != 1 else "black",
                fontsize=8,
                fontweight="bold" if value == 2 else "normal",
            )
    ax.legend(
        handles=[
            Patch(color=cmap_colors[2], label="Implemented in repo"),
            Patch(color=cmap_colors[1], label="Partial / documented"),
            Patch(color=cmap_colors[0], label="External / residual"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=3,
        framealpha=0.95,
        fontsize=8,
    )
    ax.grid(False)


def plot_unpack_latency(rows: list[dict[str, str]], ax: Axes, spec: FigureSpec) -> None:
    subset = filter_rows_for_spec(rows, spec)
    headline = "Mean pack vs unpack latency (medium tracks)"
    if not subset:
        _empty_title(ax, spec, headline)
        return
    pack_mean = mean(float(r["pack_seconds"]) for r in subset)
    unpack_mean = mean(float(r["unpack_seconds"]) for r in subset)
    labels = ["Pack", "Unpack"]
    values = [pack_mean, unpack_mean]
    bars = ax.bar(
        labels, values, color=[active_palette()[0], active_palette()[1]], width=0.5
    )
    ymax = max(values) if values else 0.0
    # The three-repetition test fixture can produce tight bar maxima, and
    # renderer QA checks the post-tight-layout label boxes. Reserve explicit
    # label headroom instead of depending on Matplotlib's automatic margins.
    ax.set_ylim(0, ymax * 1.6 if ymax > 0 else 1.0)
    _prune_edge_ticks(ax, y=True)
    annotate_bar_values(ax, bars, values, fmt="{:.4f}")
    ax.set_ylabel("Wall time (seconds)")
    ax.set_title(plot_title(headline, spec))


def plot_throughput_by_observability(
    rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    subset = filter_rows_for_spec(rows, spec)
    by_level: dict[int, list[float]] = defaultdict(list)
    for row in subset:
        by_level[int(row["observability_level"])].append(
            float(row["pack_throughput_mib_s"])
        )
    headline = "Medium-track pack throughput by observability level"
    if not by_level:
        _empty_title(ax, spec, headline)
        return
    levels = sorted(by_level)
    means = [mean(by_level[level]) for level in levels]
    mins = [min(by_level[level]) for level in levels]
    maxs = [max(by_level[level]) for level in levels]
    ax.plot(
        levels,
        means,
        marker="o",
        color=active_palette()[0],
        linewidth=line_width(),
        label="Mean",
    )
    ax.fill_between(
        levels,
        mins,
        maxs,
        color=active_palette()[0],
        alpha=0.2,
        label="Min–max repetitions",
    )
    ax.set_xticks(levels)
    _prune_edge_ticks(ax, y=True)
    ax.set_xlabel("Observability level")
    ax.set_ylabel("Pack throughput (MiB/s)")
    ax.set_title(plot_title(headline, spec))
    ax.legend(loc="best", framealpha=0.95)


def plot_expansion_heatmap(
    rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    from .benchmark_stats import base_condition

    subset = filter_rows_for_spec(rows, spec)
    headline = "Mean expansion ratio heatmap"
    if not subset:
        _empty_title(ax, spec, headline)
        return
    conditions = sorted({base_condition(r["condition"]) for r in subset})
    tracks = sorted({r["track_id"] for r in subset})
    matrix: list[list[float]] = []
    for condition in conditions:
        row_vals: list[float] = []
        for track in tracks:
            matches = [
                r
                for r in subset
                if base_condition(r["condition"]) == condition and r["track_id"] == track
            ]
            row_vals.append(
                mean(float(m["expansion_ratio"]) for m in matches) if matches else 0.0
            )
        matrix.append(row_vals)
    im = ax.imshow(matrix, aspect="auto", cmap=heatmap_cmap())
    ax.set_xticks(range(len(tracks)), labels=tracks)
    ax.set_yticks(range(len(conditions)), labels=conditions)
    # Annotate each cell with its value; pick text colour by cell luminance so labels
    # stay legible against both the dark (low) and bright (high) ends of cividis.
    finite = [value for row in matrix for value in row if value > 0.0]
    vmin = min(finite) if finite else 0.0
    vmax = max(finite) if finite else 1.0
    span = (vmax - vmin) or 1.0
    if annotate_enabled():
        for r_idx, row_vals in enumerate(matrix):
            for c_idx, value in enumerate(row_vals):
                if value <= 0.0:
                    continue
                text_color = "white" if (value - vmin) / span < 0.55 else "black"
                ax.text(
                    c_idx,
                    r_idx,
                    f"{value:.3f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=text_color,
                )
    ax.set_xlabel("Track id")
    ax.set_ylabel("Condition")
    ax.set_title(plot_title(headline, spec))
    fig = ax.figure
    fig.colorbar(
        im, ax=ax, fraction=0.046, pad=0.04, label="Expansion ratio (bright = higher)"
    )


def plot_manifest_multitrack(
    rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    subset = filter_rows_for_spec(rows, spec)
    tracks = sorted({r["track_id"] for r in subset})
    headline = "Manifest footprint across fixture tracks"
    if not tracks:
        _empty_title(ax, spec, headline)
        return
    colors = color_cycle(len(tracks))
    for track, color in zip(tracks, colors, strict=True):
        track_rows = sorted(
            [r for r in subset if r["track_id"] == track],
            key=lambda r: int(r["observability_level"]),
        )
        levels = [int(r["observability_level"]) for r in track_rows]
        sizes = [int(r["manifest_bytes"]) for r in track_rows]
        if levels:
            ax.plot(
                levels,
                sizes,
                marker="o",
                color=color,
                linewidth=line_width(),
                label=track,
            )
    ax.set_xticks(sorted({int(r["observability_level"]) for r in subset}))
    ax.margins(x=0.08, y=0.12)
    _prune_edge_ticks(ax, y=True)
    ax.set_xlabel("Observability level")
    ax.set_ylabel("Manifest size (bytes)")
    ax.set_title(plot_title(headline, spec))
    ax.legend(loc="best", framealpha=0.95, fontsize=8)


def plot_crypto_overhead(
    rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    subset = filter_rows_for_spec(rows, spec)
    ordered = sorted(subset, key=lambda row: row["track_id"])
    headline = "Ciphertext composition"
    if not ordered:
        _empty_title(ax, spec, headline)
        return
    labels = [row["track_id"] for row in ordered]
    header = [_TRACK_HEADER_BYTES] * len(ordered)
    payload = [
        max(int(row["ciphertext_bytes"]) - _TRACK_HEADER_BYTES, 0) for row in ordered
    ]
    x = list(range(len(labels)))
    ax.bar(
        x, header, label=f"Header ({_TRACK_HEADER_BYTES} B)", color=active_palette()[0]
    )
    ax.bar(
        x, payload, bottom=header, label="Ciphertext body", color=active_palette()[1]
    )
    if annotate_enabled():
        for xi, head, body in zip(x, header, payload, strict=True):
            total_bytes = head + body
            ax.text(
                xi,
                total_bytes,
                f"{total_bytes} B",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    ax.set_xticks(x, labels=labels)
    ax.set_ylabel("Bytes per track")
    # Headroom so the per-bar byte labels clear the top spine, and a left-side
    # legend so it never collides with the tallest bar's value label.
    ax.set_ylim(
        0, max(int(h) + int(p) for h, p in zip(header, payload, strict=True)) * 1.18
    )
    ax.set_title(plot_title(headline, spec))
    ax.legend(loc="upper left", framealpha=0.95)


def plot_observability_tradeoff(
    rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    subset = filter_rows_for_spec(rows, spec)
    headline = "Manifest size vs pack throughput (medium tracks)"
    if not subset:
        _empty_title(ax, spec, headline)
        return
    manifests = [int(r["manifest_bytes"]) for r in subset]
    throughputs = [float(r["pack_throughput_mib_s"]) for r in subset]
    ax.scatter(
        manifests,
        throughputs,
        color=active_palette()[4],
        s=scatter_size(),
        alpha=0.75,
        edgecolors="white",
        linewidths=0.8,
    )
    ax.margins(x=0.12, y=0.12)
    unique_manifests = sorted(set(manifests))
    if len(unique_manifests) <= 4:
        ax.set_xticks(unique_manifests)
    _prune_edge_ticks(ax, y=True)
    ax.set_xlabel("Manifest size (bytes)")
    ax.set_ylabel("Pack throughput (MiB/s)")
    ax.set_title(plot_title(headline, spec))


def plot_expansion_law(rows: list[dict[str, str]], ax: Axes, spec: FigureSpec) -> None:
    """Measured expansion ratio vs the version-aware expansion model.

    Overlays per-track measured ``expansion_ratio`` (markers) on the analytic
    ``expansion_ratio_model``. For default 0.4.0 the body is PADME bucketed, so
    the curve is a step profile rather than the old unpadded ``1 + H/n`` line.
    """
    from .benchmark_stats import (
        TRACK_HEADER_BYTES,
        expansion_ratio_model,
        max_expansion_ratio_residual,
    )

    subset = filter_rows_for_spec(rows, spec)
    ordered = sorted(subset, key=lambda row: int(row["plaintext_bytes"]))
    headline = "Expansion law: measured vs model"
    if not ordered:
        _empty_title(ax, spec, headline)
        return
    sizes = [int(row["plaintext_bytes"]) for row in ordered]
    measured = [float(row["expansion_ratio"]) for row in ordered]
    track_ids = [row["track_id"] for row in ordered]

    format_version = ordered[0].get("format_version", "0.4.0")
    # Integer model curve across the observed plaintext range.
    lo, hi = min(sizes), max(sizes)
    span = hi - lo or hi
    curve_x = sorted({max(1, int(round(lo + span * k / 100.0))) for k in range(101)})
    curve_y = [
        expansion_ratio_model(x, format_version=format_version) for x in curve_x
    ]
    ax.plot(
        curve_x,
        curve_y,
        color=active_palette()[0],
        linewidth=line_width(),
        label=f"{format_version} model (H={TRACK_HEADER_BYTES} B)",
    )
    ax.scatter(
        sizes,
        measured,
        color=active_palette()[1],
        s=scatter_size(),
        zorder=5,
        edgecolors="white",
        linewidths=0.8,
        label="Measured",
    )
    if annotate_enabled():
        for x, y, tid in zip(sizes, measured, track_ids, strict=True):
            ax.annotate(
                f"{tid} (n={x})",
                (x, y),
                textcoords="offset points",
                xytext=(6, 6),
                fontsize=8,
            )
    residual = max_expansion_ratio_residual(ordered)
    ax.set_xlabel("Plaintext size n (bytes)")
    ax.set_ylabel("Expansion ratio  r = ciphertext / plaintext")
    ax.margins(x=0.10, y=0.12)
    _prune_edge_ticks(ax, x=True, y=True)
    ax.set_title(plot_title(headline, spec))
    # Residual reported in-axes (not the title) so the long filter phrase fits.
    ax.text(
        0.97,
        0.97,
        f"max |measured − model| = {residual:.1e}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        bbox={
            "boxstyle": "round",
            "facecolor": "white",
            "alpha": 0.85,
            "edgecolor": "0.7",
        },
    )
    ax.legend(loc="lower left", framealpha=0.95)


def plot_throughput_dispersion(
    rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Per-repetition pack throughput with the mean and a 95% Student-t CI.

    Unlike the point-mean throughput figure, this surfaces measurement *dispersion*:
    each repetition is a marker, the mean is a horizontal line, and the shaded band
    is the two-sided 95% confidence interval (t critical value for n-1 df). Wide
    bands here are the honest counterpart to the exact expansion law — timing is
    noisy, byte counts are not.
    """
    from .benchmark_stats import summary_stats

    subset = filter_rows_for_spec(rows, spec)
    values = [float(r["pack_throughput_mib_s"]) for r in subset]
    headline = "Pack throughput dispersion"
    if not values:
        _empty_title(ax, spec, headline)
        return
    stats = summary_stats(values)
    xs = list(range(1, len(values) + 1))
    dense = len(values) > 50
    point_size = scatter_size() * (0.35 if dense else 1.0)
    point_alpha = 0.5 if dense else 0.85
    # CI band: clamp the *drawn* floor at 0 (throughput is non-negative) while the
    # legend reports the true computed interval — for small n with high CV the
    # symmetric t-CI lower bound can fall below zero, which the prose flags honestly.
    band_lo = max(stats.ci95_lo, 0.0)
    ax.axhspan(
        band_lo,
        stats.ci95_hi,
        color=active_palette()[0],
        alpha=0.15,
        label=f"95% CI [{stats.ci95_lo:.1f}, {stats.ci95_hi:.1f}]",
    )
    ax.axhline(
        stats.mean,
        color=active_palette()[1],
        linestyle="--",
        linewidth=line_width(),
        label=f"Mean {stats.mean:.2f} MiB/s",
    )
    ax.scatter(
        xs,
        values,
        color=active_palette()[2],
        s=point_size,
        alpha=point_alpha,
        zorder=5,
        edgecolors="white",
        linewidths=0.35 if dense else 0.8,
        label="Repetitions",
    )
    ax.set_xticks(_sparse_repetition_ticks(len(values)))
    _prune_edge_ticks(ax, y=True)
    ax.set_xlabel("Repetition")
    ax.set_ylabel("Pack throughput (MiB/s)")
    ax.set_title(plot_title(headline, spec))
    if annotate_enabled():
        ax.text(
            0.97,
            0.97,
            f"n = {stats.n}, SD = {stats.sd:.2f}, CV = {stats.cv * 100:.0f}%",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=8,
            bbox={
                "boxstyle": "round",
                "facecolor": "white",
                "alpha": 0.85,
                "edgecolor": "0.7",
            },
        )
    ax.legend(loc="lower left", framealpha=0.95)


# (csv column, display label). The determinism CLASS is NOT stored here — it is derived
# at plot time from the fingerprint's canonical split (DETERMINISTIC_BENCHMARK_COLUMNS), so
# the figure can never paint a metric in a class that contradicts the data fingerprint.
# RedTeam 2026-05-30 Q3(b): a hardcoded per-metric bool could silently flip and the figure
# (data_derived=False, exempt from byte-identity) would render the wrong split undetected.
_DETERMINISM_METRICS: tuple[tuple[str, str], ...] = (
    ("expansion_ratio", "expansion ratio"),
    ("ciphertext_bytes", "ciphertext bytes"),
    ("manifest_bytes", "manifest bytes"),
    ("pack_throughput_mib_s", "pack throughput"),
    ("pack_seconds", "pack time"),
    ("unpack_seconds", "unpack time"),
)


def plot_determinism_cv(
    rows: list[dict[str, str]], ax: Axes, spec: FigureSpec
) -> None:
    """Coefficient of variation per metric across repetitions, split by determinism.

    The visual proof behind the data fingerprint: the data-derived columns (expansion
    ratio, ciphertext bytes, manifest bytes) have CV exactly 0 — they are fixed by the
    format and manifest schema — while the wall-clock columns carry real dispersion.
    The fingerprint hashes only the zero-CV columns; the timing columns are reported
    with their spread instead ([@fig:throughput_dispersion]).
    """
    from .benchmark_stats import (
        DETERMINISTIC_BENCHMARK_COLUMNS,
        VOLATILE_BENCHMARK_COLUMNS,
        summary_stats,
    )

    subset = filter_rows_for_spec(rows, spec)
    headline = "Run-to-run variation by metric"
    if len(subset) < 2:
        _empty_title(ax, spec, headline)
        return

    labels: list[str] = []
    cvs: list[float] = []
    colors: list[str] = []
    deterministic_color = active_palette()[2]
    volatile_color = active_palette()[3]
    # Deterministic metrics first (bottom of the barh), then volatile.
    for column, label in _DETERMINISM_METRICS:
        values = [float(row[column]) for row in subset if row.get(column) not in (None, "")]
        if not values:
            continue
        # Class DERIVED from the fingerprint's canonical split — never hardcoded.
        if column in DETERMINISTIC_BENCHMARK_COLUMNS:
            color = deterministic_color
        elif column in VOLATILE_BENCHMARK_COLUMNS:
            color = volatile_color
        else:  # pragma: no cover - guarded by tests/test_determinism_cv_content.py
            raise KeyError(
                f"{column!r} is neither deterministic nor volatile — classify it in "
                f"src/benchmark_stats.py before plotting it"
            )
        labels.append(label)
        cvs.append(summary_stats(values).cv * 100.0)
        colors.append(color)

    y = list(range(len(labels)))
    bars = ax.barh(y, cvs, color=colors)
    ax.set_yticks(y, labels=labels)
    if annotate_enabled():
        span = max(cvs) or 1.0
        for rect, cv in zip(bars, cvs, strict=True):
            ax.text(
                rect.get_width() + span * 0.01,
                rect.get_y() + rect.get_height() / 2.0,
                "0 (exact)" if cv == 0.0 else f"{cv:.1f}%",
                va="center",
                ha="left",
                fontsize=8,
            )
    ax.set_xlabel("Coefficient of variation across repetitions (%)")
    ax.set_xlim(0, (max(cvs) or 1.0) * 1.40)
    _prune_edge_ticks(ax, x=True)
    # Legend by determinism class (proxy handles, not per-bar).
    ax.legend(
        handles=[
            Patch(color=deterministic_color, label="Deterministic (fingerprint-anchored)"),
            Patch(color=volatile_color, label="Wall-clock (reported with dispersion)"),
        ],
        loc="lower right",
        framealpha=0.95,
        fontsize=8,
    )
    ax.set_title(plot_title(headline, spec))


def plot_benchmark_overview(
    rows: list[dict[str, str]], fig: Figure, axes: list[Axes]
) -> None:
    specs = [
        spec_by_label("fig:throughput_benchmark"),
        spec_by_label("fig:expansion_ratio"),
        spec_by_label("fig:observability_manifest_size"),
        spec_by_label("fig:tamper_detection"),
    ]
    plotters = [plot_throughput, plot_expansion, plot_observability, plot_tamper]
    for ax, spec, plotter in zip(axes, specs, plotters, strict=True):
        style_axes(ax)
        plotter(rows, ax, spec)
        ax.set_title(ax.get_title(), fontsize=9)


def render_to_path(
    rows: list[dict[str, str]],
    output_path: Path,
    spec: FigureSpec,
    plotter,
    *,
    panel: bool = False,
) -> Path:
    if panel:
        fig, axes = open_panel()
        plot_benchmark_overview(rows, fig, axes)
        fig.suptitle("ENTO benchmark overview", fontsize=14, fontweight="bold")
        return save_figure(fig, output_path, reserve_top=True)
    fig, ax = open_figure(spec.figsize_key)
    plotter(rows, ax, spec)
    return save_figure(fig, output_path)
