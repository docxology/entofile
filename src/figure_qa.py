"""Renderer-aware QA for ENTO figure text layout."""

from __future__ import annotations

import hashlib
from itertools import combinations
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.transforms import Bbox

from .benchmark_io import load_benchmark_csv
from .figure_plotters import (
    plot_benchmark_overview,
    plot_conformance_outcomes,
    plot_crypto_overhead,
    plot_determinism_cv,
    plot_expansion,
    plot_expansion_heatmap,
    plot_expansion_law,
    plot_format_compatibility_matrix,
    plot_format_ladder,
    plot_length_leakage_profile,
    plot_manifest_multitrack,
    plot_observability,
    plot_observability_redaction_matrix,
    plot_observability_tradeoff,
    plot_release_evidence_map,
    plot_security_control_matrix,
    plot_tamper,
    plot_throughput,
    plot_throughput_by_observability,
    plot_throughput_dispersion,
    plot_unpack_latency,
)
from .figure_registry import FIGURE_SPECS, FigureSpec
from .viz_theme import open_figure, open_panel

_PLOTTERS = {
    "fig:throughput_benchmark": plot_throughput,
    "fig:expansion_ratio": plot_expansion,
    "fig:expansion_heatmap": plot_expansion_heatmap,
    "fig:observability_manifest_size": plot_observability,
    "fig:unpack_latency": plot_unpack_latency,
    "fig:throughput_by_observability": plot_throughput_by_observability,
    "fig:observability_throughput_tradeoff": plot_observability_tradeoff,
    "fig:manifest_multitrack": plot_manifest_multitrack,
    "fig:crypto_overhead": plot_crypto_overhead,
    "fig:expansion_law": plot_expansion_law,
    "fig:throughput_dispersion": plot_throughput_dispersion,
    "fig:determinism_cv": plot_determinism_cv,
    "fig:format_ladder": plot_format_ladder,
    "fig:format_compatibility_matrix": plot_format_compatibility_matrix,
    "fig:length_leakage_profile": plot_length_leakage_profile,
    "fig:conformance_outcomes": plot_conformance_outcomes,
    "fig:observability_redaction_matrix": plot_observability_redaction_matrix,
    "fig:release_evidence_map": plot_release_evidence_map,
    "fig:security_control_matrix": plot_security_control_matrix,
    "fig:tamper_detection": plot_tamper,
}


def validate_registered_figure_layout(csv_path: Path) -> dict[str, Any]:
    """Render registered figures in memory and report text clipping/overlap issues."""
    rows = load_benchmark_csv(csv_path)
    reports = []
    for spec in FIGURE_SPECS:
        reports.append(_validate_one(rows, spec))
    failed = [report for report in reports if not report["ok"]]
    return {
        "ok": not failed,
        "figure_count": len(reports),
        "failed": [report["label"] for report in failed],
        "figures": reports,
    }


def text_layout_issues(fig: Any) -> list[dict[str, Any]]:
    """Return renderer-derived text clipping and overlap issues for a figure."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_box = fig.bbox
    text_boxes: list[tuple[str, Bbox]] = []
    issues: list[dict[str, Any]] = []
    for text in fig.findobj(Text):
        if not text.get_visible():
            continue
        value = text.get_text().strip()
        if not value:
            continue
        bbox = text.get_window_extent(renderer=renderer)
        if bbox.width < 1 or bbox.height < 1:
            continue
        padded = bbox.expanded(1.02, 1.06)
        if _outside_figure(padded, fig_box):
            issues.append(
                {
                    "type": "clipped_text",
                    "text": _shorten(value),
                    "bbox": _bbox_tuple(padded),
                }
            )
        text_boxes.append((value, padded))

    for (a_text, a_box), (b_text, b_box) in combinations(text_boxes, 2):
        overlap = _intersection_area(a_box, b_box)
        if overlap < 36.0:
            continue
        min_area = min(a_box.width * a_box.height, b_box.width * b_box.height)
        if min_area <= 0 or overlap / min_area < 0.32:
            continue
        issues.append(
            {
                "type": "overlapping_text",
                "text_a": _shorten(a_text),
                "text_b": _shorten(b_text),
                "overlap_area": round(overlap, 2),
                "overlap_fraction": round(overlap / min_area, 3),
            }
        )
    return issues


def _validate_one(rows: list[dict[str, str]], spec: FigureSpec) -> dict[str, Any]:
    """Validate layout and bounding boxes for one registered figure."""
    if spec.label == "fig:benchmark_overview":
        fig, axes = open_panel()
        try:
            plot_benchmark_overview(rows, fig, axes)
            fig.suptitle("ENTO benchmark overview", fontsize=14, fontweight="bold")
            fig.tight_layout(pad=1.25, rect=(0.0, 0.0, 1.0, 0.95))
            issues = text_layout_issues(fig)
        finally:
            plt.close(fig)
    else:
        fig, ax = open_figure(spec.figsize_key)
        try:
            _PLOTTERS[spec.label](rows, ax, spec)
            fig.tight_layout(pad=1.25)
            issues = text_layout_issues(fig)
        finally:
            plt.close(fig)
    return {
        "label": spec.label,
        "filename": spec.filename,
        "ok": not issues,
        "issues": issues,
    }


def _outside_figure(box: Bbox, fig_box: Bbox, *, tolerance_px: float = 2.0) -> bool:
    """Return True if bounding box extends outside figure frame boundaries."""
    return (
        box.x0 < fig_box.x0 - tolerance_px
        or box.y0 < fig_box.y0 - tolerance_px
        or box.x1 > fig_box.x1 + tolerance_px
        or box.y1 > fig_box.y1 + tolerance_px
    )


def _intersection_area(a: Bbox, b: Bbox) -> float:
    """Compute overlapping area between two bounding boxes."""
    width = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
    height = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
    return width * height


def _bbox_tuple(box: Bbox) -> tuple[float, float, float, float]:
    """Convert Bbox to (x0, y0, x1, y1) tuple."""
    return (round(box.x0, 2), round(box.y0, 2), round(box.x1, 2), round(box.y1, 2))


def _shorten(text: str, *, limit: int = 80) -> str:
    """Truncate text to limit chars with ellipsis."""
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 3] + "..."


def pixel_digest(path: Path, *, downsample: int = 1) -> dict[str, Any]:
    """Compute a structured pixel summary for a rendered figure PNG.

    Returns dimension, mean-per-channel, and a short content hash for
    drift-detection against a reference. When *downsample* > 1 the image
    is decimated before hashing (drift-tolerant mode).
    """
    from PIL import Image

    img = Image.open(path).convert("RGB")
    w, h = img.size
    if downsample > 1:
        img = img.resize((max(1, w // downsample), max(1, h // downsample)))
    if hasattr(img, "get_flattened_data"):
        pixels = [tuple(p) if isinstance(p, (tuple, list)) else (p,) for p in img.get_flattened_data()]
    else:
        pixels = list(img.getdata())  # type: ignore[attr-defined]
    channels = len(pixels[0]) if pixels else 3
    means = tuple(
        round(sum(p[c] for p in pixels) / len(pixels), 1) if pixels else 0.0
        for c in range(channels)
    )
    content_hash = hashlib.sha256(
        img.tobytes() if downsample == 1 else path.read_bytes()
    ).hexdigest()[:16]
    return {
        "path": str(path),
        "width": w,
        "height": h,
        "channels": channels,
        "mean_per_channel": means,
        "digest": content_hash,
        "downsample": downsample,
    }


def compare_figure_pixels(
    path: Path,
    reference: dict[str, Any],
    *,
    max_dimension_drift_px: int = 0,
    max_mean_drift: float = 5.0,
) -> dict[str, Any]:
    """Compare a rendered figure against a reference pixel digest.

    Returns ``ok``, ``drifts``, and ``digest``.  Drift fields are
    ``None`` when the check passes.  Default tolerance values permit
    minor style/anti-aliasing changes while flagging obvious breakage.
    """
    digest = pixel_digest(path)
    drifts: dict[str, Any] = {}
    dim_drift = max(
        abs(digest["width"] - reference["width"]),
        abs(digest["height"] - reference["height"]),
    )
    if dim_drift > max_dimension_drift_px:
        drifts["dimensions"] = {
            "expected": (reference["width"], reference["height"]),
            "actual": (digest["width"], digest["height"]),
            "drift_px": dim_drift,
        }
    mean_drifts = {}
    for c in range(min(len(digest["mean_per_channel"]), len(reference["mean_per_channel"]))):
        drift = abs(digest["mean_per_channel"][c] - reference["mean_per_channel"][c])
        if drift > max_mean_drift:
            mean_drifts[f"channel_{c}"] = {
                "expected": reference["mean_per_channel"][c],
                "actual": digest["mean_per_channel"][c],
                "drift": drift,
            }
    if mean_drifts:
        drifts["mean_per_channel"] = mean_drifts
    return {
        "ok": not drifts,
        "drifts": drifts,
        "digest": digest["digest"],
        "reference_digest": reference.get("digest"),
    }
