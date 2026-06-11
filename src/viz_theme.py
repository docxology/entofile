"""Publication-oriented matplotlib theme for ENTO benchmark figures."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from .experiment_config import VizConfig

# Default palette mirrors VizConfig's default ("wong"); the *active* palette,
# colormap, line/marker/scatter sizes, and annotation toggle are all sourced
# from the bound VizConfig so they are genuinely config-driven (no dead knobs).
PALETTE: tuple[str, ...] = (
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#56B4E9",
    "#F0E442",
    "#D55E00",
)

FIGSIZE_PRESETS: dict[str, tuple[float, float]] = {
    "single": (8.0, 5.0),
    "wide": (10.0, 5.0),
    "tall": (8.0, 6.0),
    "panel": (12.0, 10.0),
}

_active: VizConfig | None = None


def bind_viz(viz: VizConfig) -> None:
    """Set active visualization config for the current analysis run."""
    global _active
    _active = viz


def active_viz() -> VizConfig:
    if _active is None:
        from .experiment_config import VizConfig

        return VizConfig()
    return _active


def active_palette() -> tuple[str, ...]:
    """Resolved hex palette for the active config (config-driven, falls back to Wong)."""
    return active_viz().palette_colors


def heatmap_cmap() -> str:
    """Active sequential colormap name for heatmaps."""
    return active_viz().heatmap_cmap


def markersize() -> float:
    return active_viz().marker_size


def line_width() -> float:
    """Active line width. Used by explicit ``linewidth=`` kwargs in plotters so the
    knob takes effect even though an explicit kwarg overrides the rcParam default."""
    return active_viz().line_width


def scatter_size() -> float:
    return active_viz().scatter_size


def annotate_enabled() -> bool:
    """Whether per-value annotations should be drawn (config toggle)."""
    return active_viz().annotate_values


def figsize_for(key: str) -> tuple[float, float]:
    viz = active_viz()
    if key == "single":
        return viz.figsize
    return FIGSIZE_PRESETS.get(key, viz.figsize)


def color_cycle(n: int) -> list[str]:
    if n <= 0:
        return []
    palette = active_palette()
    return [palette[i % len(palette)] for i in range(n)]


def apply_rcparams() -> None:
    viz = active_viz()
    plt.rcParams.update(
        {
            "figure.dpi": viz.dpi,
            "savefig.dpi": viz.dpi,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "font.size": viz.font_size,
            "axes.titlesize": viz.font_size + 2,
            "axes.labelsize": viz.font_size + 1,
            "axes.titleweight": "bold",
            "axes.labelweight": "medium",
            "axes.grid": True,
            "grid.alpha": viz.grid_alpha,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "lines.linewidth": viz.line_width,
            "lines.markersize": viz.marker_size,
        }
    )


def style_axes(ax: Axes) -> None:
    ax.grid(True, alpha=active_viz().grid_alpha)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def save_figure(fig: Figure, output_path: Path, *, reserve_top: bool = False) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # ``reserve_top`` leaves headroom for a figure-level suptitle (e.g. the overview panel)
    # so tight_layout does not collide title text with the top row of axes.
    fig.tight_layout(
        pad=1.25,
        rect=(0.0, 0.0, 1.0, 0.95) if reserve_top else None,
    )
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def open_figure(figsize_key: str = "single") -> tuple[Figure, Axes]:
    apply_rcparams()
    fig, ax = plt.subplots(figsize=figsize_for(figsize_key))
    style_axes(ax)
    return fig, ax


def open_panel(nrows: int = 2, ncols: int = 2) -> tuple[Figure, list[Axes]]:
    apply_rcparams()
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize_for("panel"))
    flat = list(axes.flatten()) if hasattr(axes, "flatten") else [axes]
    for ax in flat:
        style_axes(ax)
    return fig, flat


def annotate_bar_values(ax: Axes, bars, values: Sequence[float], *, fmt: str) -> None:
    if not annotate_enabled():
        return
    label_size = max(active_viz().font_size - 1, 8)
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            fmt.format(value),
            ha="center",
            va="bottom",
            fontsize=label_size,
        )


def format_mib_s_axis(ax: Axes, axis: str = "y") -> None:
    target = ax.yaxis if axis == "y" else ax.xaxis
    target.set_label_text(
        target.get_label().get_text() + " (MiB/s)"
        if "MiB" not in target.get_label().get_text()
        else target.get_label().get_text()
    )
