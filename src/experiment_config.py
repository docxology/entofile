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
from math import isfinite
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigurationError

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
    # Okabe-Ito 8-colour qualitative set (adds black, reorders).
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


ConfigError = ConfigurationError


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
    unknown = sorted(
        (key for key in section if not isinstance(key, str) or key not in allowed),
        key=str,
    )
    if unknown:
        raise ConfigError(
            f"unknown {where} config key(s): {', '.join(map(str, unknown))}. "
            f"Valid keys: {', '.join(sorted(allowed))}."
        )


def _mapping(value: object, where: str) -> dict[str, Any]:
    """Return a config mapping or raise a useful error for malformed YAML."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{where} must be a mapping")
    return value


def _integer(value: object, default: int, where: str) -> int:
    candidate = default if value is None else value
    if isinstance(candidate, bool) or not isinstance(candidate, int):
        raise ConfigError(f"{where} must be an integer")
    return candidate


def _required_integer(value: object, where: str) -> int:
    """Validate an integer list item where ``null`` is never a default."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{where} must be an integer")
    return value


def _number(value: object, default: float, where: str) -> float:
    candidate = default if value is None else value
    if isinstance(candidate, bool) or not isinstance(candidate, (int, float)):
        raise ConfigError(f"{where} must be a finite number")
    result = float(candidate)
    if not isfinite(result):
        raise ConfigError(f"{where} must be a finite number")
    return result


def _boolean(value: object, default: bool, where: str) -> bool:
    candidate = default if value is None else value
    if not isinstance(candidate, bool):
        raise ConfigError(f"{where} must be true or false")
    return candidate


def _string(value: object, default: str, where: str) -> str:
    candidate = default if value is None else value
    if not isinstance(candidate, str):
        raise ConfigError(f"{where} must be a string")
    return candidate


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
    if not isinstance(raw, dict):
        raise ConfigError("top-level config must be a mapping")
    exp = _mapping(raw.get("experiment"), "experiment")
    _reject_unknown_keys(exp, _ALLOWED_EXPERIMENT_KEYS, "experiment")
    reps = _integer(
        exp.get("benchmark_repetitions"), _DEFAULT_REPETITIONS, "experiment.benchmark_repetitions"
    )
    if reps < 1:
        raise ConfigError("experiment.benchmark_repetitions must be at least 1")
    levels_raw = exp.get("observability_levels", list(_DEFAULT_OBS_LEVELS))
    if not isinstance(levels_raw, (list, tuple)) or not levels_raw:
        raise ConfigError("experiment.observability_levels must be a non-empty list")
    levels = tuple(
        _required_integer(value, "experiment.observability_levels[]") for value in levels_raw
    )
    if len(set(levels)) != len(levels) or any(level not in range(4) for level in levels):
        raise ConfigError("experiment.observability_levels must contain unique values from 0 to 3")
    medium = _integer(
        exp.get("medium_track_bytes"), _DEFAULT_MEDIUM_BYTES, "experiment.medium_track_bytes"
    )
    large = _integer(
        exp.get("large_track_bytes"), _DEFAULT_LARGE_BYTES, "experiment.large_track_bytes"
    )
    if medium < 1 or large < 0:
        raise ConfigError("experiment track sizes must be positive (large may be 0 to disable)")
    include_mixed = _boolean(
        exp.get("include_mixed_container"),
        _DEFAULT_INCLUDE_MIXED,
        "experiment.include_mixed_container",
    )
    creator = _string(exp.get("creator"), "entofile", "experiment.creator")
    viz_raw = _mapping(exp.get("viz"), "experiment.viz")
    _reject_unknown_keys(viz_raw, _ALLOWED_VIZ_KEYS, "experiment.viz")
    dpi = _integer(viz_raw.get("dpi"), _DEFAULT_DPI, "experiment.viz.dpi")
    if dpi < 1:
        raise ConfigError("experiment.viz.dpi must be at least 1")
    figsize_raw = viz_raw.get("figsize", list(_DEFAULT_FIGSIZE))
    if not isinstance(figsize_raw, (list, tuple)) or len(figsize_raw) != 2:
        raise ConfigError("experiment.viz.figsize must contain exactly two numbers")
    figsize_values = tuple(
        _number(value, 0.0, "experiment.viz.figsize[]") for value in figsize_raw
    )
    if any(value <= 0 for value in figsize_values):
        raise ConfigError("experiment.viz.figsize values must be positive")
    figsize = (figsize_values[0], figsize_values[1])
    figure_width_percent = _integer(
        viz_raw.get("figure_width_percent"),
        _DEFAULT_FIGURE_WIDTH_PERCENT,
        "experiment.viz.figure_width_percent",
    )
    if not 1 <= figure_width_percent <= 100:
        raise ConfigError("experiment.viz.figure_width_percent must be between 1 and 100")
    font_size = _number(viz_raw.get("font_size"), _DEFAULT_FONT_SIZE, "experiment.viz.font_size")
    grid_alpha = _number(viz_raw.get("grid_alpha"), _DEFAULT_GRID_ALPHA, "experiment.viz.grid_alpha")
    if not 0 <= grid_alpha <= 1:
        raise ConfigError("experiment.viz.grid_alpha must be between 0 and 1")
    palette = _string(viz_raw.get("palette"), _DEFAULT_PALETTE, "experiment.viz.palette")
    if palette not in NAMED_PALETTES:
        raise ConfigError(
            f"unknown viz.palette {palette!r}. Valid palettes: {', '.join(sorted(NAMED_PALETTES))}."
        )
    heatmap_cmap = _string(
        viz_raw.get("heatmap_cmap"), _DEFAULT_HEATMAP_CMAP, "experiment.viz.heatmap_cmap"
    )
    if heatmap_cmap not in ALLOWED_HEATMAP_CMAPS:
        raise ConfigError(
            f"unknown viz.heatmap_cmap {heatmap_cmap!r}. Valid colormaps: {', '.join(sorted(ALLOWED_HEATMAP_CMAPS))}."
        )
    annotate_values = _boolean(
        viz_raw.get("annotate_values"),
        _DEFAULT_ANNOTATE_VALUES,
        "experiment.viz.annotate_values",
    )
    line_width = _number(viz_raw.get("line_width"), _DEFAULT_LINE_WIDTH, "experiment.viz.line_width")
    marker_size = _number(viz_raw.get("marker_size"), _DEFAULT_MARKER_SIZE, "experiment.viz.marker_size")
    scatter_size = _number(
        viz_raw.get("scatter_size"), _DEFAULT_SCATTER_SIZE, "experiment.viz.scatter_size"
    )
    if line_width <= 0 or marker_size <= 0 or scatter_size <= 0 or font_size <= 0:
        raise ConfigError("experiment.viz sizes must be positive")
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
