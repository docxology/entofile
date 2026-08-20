"""Matplotlib figure generators for ENTO benchmarks (thin dispatch to plotters)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .benchmark_io import load_benchmark_csv
from .experiment_config import VizConfig
from .figure_plotters import (
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
    render_to_path,
)
from .figure_registry import spec_by_label
from .viz_theme import bind_viz

_DEFAULT_VIZ = VizConfig()

VIZ_CONFIG: dict[str, object] = {
    "dpi": _DEFAULT_VIZ.dpi,
    "figsize": _DEFAULT_VIZ.figsize,
    "figure_width_percent": _DEFAULT_VIZ.figure_width_percent,
    "font_size": _DEFAULT_VIZ.font_size,
    "grid_alpha": _DEFAULT_VIZ.grid_alpha,
    "palette": list(_DEFAULT_VIZ.__dict__.get("palette", ())),
}


def configure_viz(viz: VizConfig) -> None:
    """Apply experiment config visualization settings for this run."""
    bind_viz(viz)
    VIZ_CONFIG.update(
        {
            "dpi": viz.dpi,
            "figsize": viz.figsize,
            "figure_width_percent": viz.figure_width_percent,
            "font_size": viz.font_size,
            "grid_alpha": viz.grid_alpha,
        }
    )


def _generate(
    csv_path: Path,
    output_path: Path,
    label: str,
    plotter: Any,
    *,
    panel: bool = False,
) -> Path:
    """Load benchmark data and render a registered figure specification."""
    rows = load_benchmark_csv(csv_path)
    spec = spec_by_label(label)
    return render_to_path(rows, output_path, spec, plotter, panel=panel)


def generate_benchmark_overview_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate 4-panel benchmark overview figure."""
    return _generate(
        csv_path, output_path, "fig:benchmark_overview", plot_throughput, panel=True
    )


def generate_throughput_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate throughput benchmark figure."""
    return _generate(csv_path, output_path, "fig:throughput_benchmark", plot_throughput)


def generate_expansion_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate expansion ratio figure."""
    return _generate(csv_path, output_path, "fig:expansion_ratio", plot_expansion)


def generate_expansion_heatmap_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate expansion heatmap figure across sizes and observability levels."""
    return _generate(
        csv_path, output_path, "fig:expansion_heatmap", plot_expansion_heatmap
    )


def generate_observability_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate observability manifest size figure."""
    return _generate(
        csv_path, output_path, "fig:observability_manifest_size", plot_observability
    )


def generate_unpack_latency_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate unpack latency figure."""
    return _generate(csv_path, output_path, "fig:unpack_latency", plot_unpack_latency)


def generate_throughput_by_observability_figure(
    csv_path: Path, output_path: Path
) -> Path:
    """Generate throughput by observability level figure."""
    return _generate(
        csv_path,
        output_path,
        "fig:throughput_by_observability",
        plot_throughput_by_observability,
    )


def generate_observability_tradeoff_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate observability vs throughput tradeoff figure."""
    return _generate(
        csv_path,
        output_path,
        "fig:observability_throughput_tradeoff",
        plot_observability_tradeoff,
    )


def generate_manifest_multitrack_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate manifest multitrack scaling figure."""
    return _generate(
        csv_path, output_path, "fig:manifest_multitrack", plot_manifest_multitrack
    )


def generate_crypto_overhead_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate cryptographic overhead breakdown figure."""
    return _generate(csv_path, output_path, "fig:crypto_overhead", plot_crypto_overhead)


def generate_expansion_law_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate expansion law verification figure."""
    return _generate(csv_path, output_path, "fig:expansion_law", plot_expansion_law)


def generate_throughput_dispersion_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate throughput dispersion across repetitions figure."""
    return _generate(
        csv_path, output_path, "fig:throughput_dispersion", plot_throughput_dispersion
    )


def generate_determinism_cv_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate coefficient of variation determinism classification figure."""
    return _generate(
        csv_path, output_path, "fig:determinism_cv", plot_determinism_cv
    )


def generate_format_ladder_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate format security ladder figure."""
    return _generate(csv_path, output_path, "fig:format_ladder", plot_format_ladder)


def generate_format_compatibility_matrix_figure(
    csv_path: Path, output_path: Path
) -> Path:
    """Generate format compatibility matrix figure."""
    return _generate(
        csv_path,
        output_path,
        "fig:format_compatibility_matrix",
        plot_format_compatibility_matrix,
    )


def generate_length_leakage_profile_figure(
    csv_path: Path, output_path: Path
) -> Path:
    """Generate PADME length leakage profile figure."""
    return _generate(
        csv_path,
        output_path,
        "fig:length_leakage_profile",
        plot_length_leakage_profile,
    )


def generate_conformance_outcomes_figure(
    csv_path: Path, output_path: Path
) -> Path:
    """Generate conformance test outcomes figure."""
    return _generate(
        csv_path,
        output_path,
        "fig:conformance_outcomes",
        plot_conformance_outcomes,
    )


def generate_observability_redaction_matrix_figure(
    csv_path: Path, output_path: Path
) -> Path:
    """Generate observability redaction field matrix figure."""
    return _generate(
        csv_path,
        output_path,
        "fig:observability_redaction_matrix",
        plot_observability_redaction_matrix,
    )


def generate_release_evidence_map_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate release evidence artifact provenance figure."""
    return _generate(
        csv_path,
        output_path,
        "fig:release_evidence_map",
        plot_release_evidence_map,
    )


def generate_security_control_matrix_figure(
    csv_path: Path, output_path: Path
) -> Path:
    """Generate security control matrix figure."""
    return _generate(
        csv_path,
        output_path,
        "fig:security_control_matrix",
        plot_security_control_matrix,
    )


def generate_tamper_figure(csv_path: Path, output_path: Path) -> Path:
    """Generate tamper detection rate figure."""
    return _generate(csv_path, output_path, "fig:tamper_detection", plot_tamper)
