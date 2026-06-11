"""Experiment configuration for entofile benchmarks.

The configurable surface is deliberately explicit and *closed*: every key the
loader honours is enumerated in ``_ALLOWED_EXPERIMENT_KEYS`` / ``_ALLOWED_VIZ_KEYS``
and every enumerated key is consumed by a field below (no dead knobs). An unknown
or mistyped key is rejected loudly with :class:`ConfigError` rather than silently
ignored — a silently-dropped knob is indistinguishable from a broken one, so the
loader fails closed and names the offending key plus the valid set.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_REPETITIONS = 3
_DEFAULT_OBS_LEVELS = (0, 1, 2, 3)
_DEFAULT_MEDIUM_BYTES = 65536
_DEFAULT_LARGE_BYTES = 0
_DEFAULT_INCLUDE_MIXED = False
_DEFAULT_DPI = 300
_DEFAULT_FIGSIZE = (8, 5)
_DEFAULT_FIGURE_WIDTH_PERCENT = 90
_DEFAULT_FONT_SIZE = 10.0
_DEFAULT_GRID_ALPHA = 0.3
_DEFAULT_PALETTE = "wong"
_DEFAULT_HEATMAP_CMAP = "cividis"
_DEFAULT_ANNOTATE_VALUES = True
_DEFAULT_LINE_WIDTH = 2.0
_DEFAULT_MARKER_SIZE = 8.0
_DEFAULT_SCATTER_SIZE = 96.0

# Named colorblind-safe qualitative palettes. Selected by ``viz.palette``.
# Keys are the only legal palette names; an unknown name is rejected.
NAMED_PALETTES: dict[str, tuple[str, ...]] = {
    # Wong (Nature Methods 2011) / IBM Design — the project default.
    "wong": (
        "#0072B2",
        "#E69F00",
        "#009E73",
        "#CC79A7",
        "#56B4E9",
        "#F0E442",
        "#D55E00",
    ),
    # Okabe–Ito 8-colour qualitative set (adds black, reorders).
    "okabe_ito": (
        "#000000",
        "#E69F00",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
        "#D55E00",
        "#CC79A7",
    ),
    # Paul Tol "bright" qualitative set.
    "tol_bright": (
        "#4477AA",
        "#EE6677",
        "#228833",
        "#CCBB44",
        "#66CCEE",
        "#AA3377",
        "#BBBBBB",
    ),
}

# Matplotlib sequential colormaps that are perceptually uniform and colorblind-safe.
ALLOWED_HEATMAP_CMAPS: frozenset[str] = frozenset(
    {"cividis", "viridis", "magma", "plasma", "inferno"}
)


class ConfigError(ValueError):
    """Raised when ``config.yaml`` contains an unknown or invalid knob."""


@dataclass(frozen=True)
class VizConfig:
    dpi: int = _DEFAULT_DPI
    figsize: tuple[float, float] = _DEFAULT_FIGSIZE
    figure_width_percent: int = _DEFAULT_FIGURE_WIDTH_PERCENT
    font_size: float = _DEFAULT_FONT_SIZE
    grid_alpha: float = _DEFAULT_GRID_ALPHA
    palette: str = _DEFAULT_PALETTE
    heatmap_cmap: str = _DEFAULT_HEATMAP_CMAP
    annotate_values: bool = _DEFAULT_ANNOTATE_VALUES
    line_width: float = _DEFAULT_LINE_WIDTH
    marker_size: float = _DEFAULT_MARKER_SIZE
    scatter_size: float = _DEFAULT_SCATTER_SIZE

    @property
    def palette_colors(self) -> tuple[str, ...]:
        """Resolve the named palette to its hex tuple."""
        return NAMED_PALETTES[self.palette]


@dataclass(frozen=True)
class ExperimentConfig:
    benchmark_repetitions: int = _DEFAULT_REPETITIONS
    observability_levels: tuple[int, ...] = _DEFAULT_OBS_LEVELS
    medium_track_bytes: int = _DEFAULT_MEDIUM_BYTES
    large_track_bytes: int = _DEFAULT_LARGE_BYTES
    include_mixed_container: bool = _DEFAULT_INCLUDE_MIXED
    creator: str = "entofile"
    viz: VizConfig = VizConfig()


# Closed key sets — every entry maps to a consumed field above. Tests assert the
# round-trip (every allowed key is honoured, every field has an allowed key).
_ALLOWED_VIZ_KEYS: frozenset[str] = frozenset(
    {
        "dpi",
        "figsize",
        "figure_width_percent",
        "font_size",
        "grid_alpha",
        "palette",
        "heatmap_cmap",
        "annotate_values",
        "line_width",
        "marker_size",
        "scatter_size",
    }
)
_ALLOWED_EXPERIMENT_KEYS: frozenset[str] = frozenset(
    {
        "benchmark_repetitions",
        "observability_levels",
        "medium_track_bytes",
        "large_track_bytes",
        "include_mixed_container",
        "creator",
        "viz",
    }
)


def _reject_unknown_keys(
    section: dict[str, Any], allowed: frozenset[str], where: str
) -> None:
    """Fail closed on any key outside ``allowed``, naming the offenders."""
    unknown = sorted(set(section) - allowed)
    if unknown:
        raise ConfigError(
            f"unknown {where} config key(s): {', '.join(unknown)}. "
            f"Valid keys: {', '.join(sorted(allowed))}."
        )


def load_experiment_config(
    project_root: Path | None = None, *, config_path: Path | None = None
) -> ExperimentConfig:
    root = project_root or Path(__file__).resolve().parent.parent
    config_path = config_path or root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return ExperimentConfig()
    raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return experiment_config_from_mapping(raw)


def experiment_config_from_mapping(raw: dict[str, Any]) -> ExperimentConfig:
    """Build :class:`ExperimentConfig` from a parsed YAML mapping."""
    exp = raw.get("experiment") or {}
    _reject_unknown_keys(exp, _ALLOWED_EXPERIMENT_KEYS, "experiment")
    reps = int(exp.get("benchmark_repetitions", _DEFAULT_REPETITIONS))
    levels_raw = exp.get("observability_levels", list(_DEFAULT_OBS_LEVELS))
    levels = tuple(int(v) for v in levels_raw)
    medium = int(exp.get("medium_track_bytes", _DEFAULT_MEDIUM_BYTES))
    large = int(exp.get("large_track_bytes", _DEFAULT_LARGE_BYTES))
    include_mixed = bool(exp.get("include_mixed_container", _DEFAULT_INCLUDE_MIXED))
    creator = str(exp.get("creator", "entofile"))
    viz_raw = exp.get("viz") or {}
    _reject_unknown_keys(viz_raw, _ALLOWED_VIZ_KEYS, "experiment.viz")
    dpi = int(viz_raw.get("dpi", _DEFAULT_DPI))
    figsize_raw = viz_raw.get("figsize", list(_DEFAULT_FIGSIZE))
    figsize = (float(figsize_raw[0]), float(figsize_raw[1]))
    figure_width_percent = int(
        viz_raw.get("figure_width_percent", _DEFAULT_FIGURE_WIDTH_PERCENT)
    )
    font_size = float(viz_raw.get("font_size", _DEFAULT_FONT_SIZE))
    grid_alpha = float(viz_raw.get("grid_alpha", _DEFAULT_GRID_ALPHA))
    palette = str(viz_raw.get("palette", _DEFAULT_PALETTE))
    if palette not in NAMED_PALETTES:
        raise ConfigError(
            f"unknown viz.palette {palette!r}. Valid palettes: {', '.join(sorted(NAMED_PALETTES))}."
        )
    heatmap_cmap = str(viz_raw.get("heatmap_cmap", _DEFAULT_HEATMAP_CMAP))
    if heatmap_cmap not in ALLOWED_HEATMAP_CMAPS:
        raise ConfigError(
            f"unknown viz.heatmap_cmap {heatmap_cmap!r}. Valid colormaps: {', '.join(sorted(ALLOWED_HEATMAP_CMAPS))}."
        )
    annotate_values = bool(viz_raw.get("annotate_values", _DEFAULT_ANNOTATE_VALUES))
    line_width = float(viz_raw.get("line_width", _DEFAULT_LINE_WIDTH))
    marker_size = float(viz_raw.get("marker_size", _DEFAULT_MARKER_SIZE))
    scatter_size = float(viz_raw.get("scatter_size", _DEFAULT_SCATTER_SIZE))
    return ExperimentConfig(
        benchmark_repetitions=reps,
        observability_levels=levels,
        medium_track_bytes=medium,
        large_track_bytes=large,
        include_mixed_container=include_mixed,
        creator=creator,
        viz=VizConfig(
            dpi=dpi,
            figsize=figsize,
            figure_width_percent=figure_width_percent,
            font_size=font_size,
            grid_alpha=grid_alpha,
            palette=palette,
            heatmap_cmap=heatmap_cmap,
            annotate_values=annotate_values,
            line_width=line_width,
            marker_size=marker_size,
            scatter_size=scatter_size,
        ),
    )


def viz_config_field_names() -> frozenset[str]:
    """Field names on :class:`VizConfig` (used by the no-dead-knob inventory test)."""
    return frozenset(f.name for f in fields(VizConfig))
