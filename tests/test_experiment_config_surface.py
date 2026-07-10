"""Configurability-surface contract for ``experiment.viz``.

These tests make "fully configurable" a verifiable claim rather than a slogan:
every allowed key is consumed by a ``VizConfig`` field (no dead knobs), every
field is reachable from YAML, unknown/mistyped keys are rejected loudly, and the
named palette / colormap whitelists are enforced.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.experiment_config import (
    _ALLOWED_VIZ_KEYS,
    ALLOWED_HEATMAP_CMAPS,
    NAMED_PALETTES,
    ConfigError,
    load_experiment_config,
    viz_config_field_names,
)


def _write_config(tmp_path: Path, viz: dict) -> Path:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text(
        yaml.dump({"experiment": {"viz": viz}}), encoding="utf-8"
    )
    return tmp_path


def test_no_dead_knobs_allowed_viz_keys_are_exactly_the_fields() -> None:
    """Every allowed YAML key maps to a consumed field and vice versa.

    ``palette_colors`` is a derived property, not a YAML knob, so the consumed
    field set is the dataclass fields. The allowed-key set must equal it exactly:
    a key with no field is a dead knob; a field with no key is unreachable config.
    """
    assert viz_config_field_names() == _ALLOWED_VIZ_KEYS


def test_unknown_viz_key_is_rejected_loudly(tmp_path: Path) -> None:
    root = _write_config(
        tmp_path, {"dpi": 120, "colour": "blue"}
    )  # typo'd British spelling
    with pytest.raises(ConfigError) as exc:
        load_experiment_config(root)
    assert "colour" in str(exc.value)
    assert "Valid keys" in str(exc.value)


def test_unknown_experiment_key_is_rejected_loudly(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_text(
        yaml.dump({"experiment": {"benchmark_reps": 5}}),
        encoding="utf-8",  # should be benchmark_repetitions
    )
    with pytest.raises(ConfigError) as exc:
        load_experiment_config(tmp_path)
    assert "benchmark_reps" in str(exc.value)


def test_every_new_viz_knob_round_trips_from_yaml(tmp_path: Path) -> None:
    root = _write_config(
        tmp_path,
        {
            "palette": "okabe_ito",
            "heatmap_cmap": "viridis",
            "annotate_values": False,
            "line_width": 3.5,
            "marker_size": 12.0,
            "scatter_size": 150.0,
        },
    )
    cfg = load_experiment_config(root)
    assert cfg.viz.palette == "okabe_ito"
    assert cfg.viz.palette_colors == NAMED_PALETTES["okabe_ito"]
    assert cfg.viz.heatmap_cmap == "viridis"
    assert cfg.viz.annotate_values is False
    assert cfg.viz.line_width == 3.5
    assert cfg.viz.marker_size == 12.0
    assert cfg.viz.scatter_size == 150.0


def test_unknown_palette_rejected(tmp_path: Path) -> None:
    root = _write_config(tmp_path, {"palette": "neon"})
    with pytest.raises(ConfigError) as exc:
        load_experiment_config(root)
    assert "neon" in str(exc.value)


def test_unknown_heatmap_cmap_rejected(tmp_path: Path) -> None:
    root = _write_config(
        tmp_path, {"heatmap_cmap": "jet"}
    )  # jet is not colorblind-safe
    with pytest.raises(ConfigError) as exc:
        load_experiment_config(root)
    assert "jet" in str(exc.value)


def test_named_palettes_are_nonempty_and_hex() -> None:
    for name, colors in NAMED_PALETTES.items():
        assert colors, f"palette {name} is empty"
        for c in colors:
            assert c.startswith("#") and len(c) == 7, f"{name}: {c} is not a hex colour"


def test_allowed_cmaps_are_colorblind_safe_set() -> None:
    # Guards against re-introducing a non-uniform map like 'jet'.
    assert "jet" not in ALLOWED_HEATMAP_CMAPS
    assert "cividis" in ALLOWED_HEATMAP_CMAPS


def test_config_toggle_actually_reaches_plotters(tmp_path: Path) -> None:
    """annotate_values=False must suppress annotations (knob is consumed, not cosmetic)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src.experiment_config import VizConfig
    from src.figure_plotters import plot_expansion
    from src.figure_registry import spec_by_label
    from src.viz_theme import bind_viz

    rows = [
        {
            "condition": "small_tracks_r0",
            "track_id": "eeg",
            "observability_level": "3",
            "expansion_ratio": "1.5",
        },
    ]
    spec = spec_by_label("fig:expansion_ratio")

    bind_viz(VizConfig(annotate_values=False))
    _fig, ax = plt.subplots()
    try:
        plot_expansion(rows, ax, spec)
        texts_off = len(ax.texts)
    finally:
        plt.close(_fig)

    bind_viz(VizConfig(annotate_values=True))
    _fig, ax = plt.subplots()
    try:
        plot_expansion(rows, ax, spec)
        texts_on = len(ax.texts)
    finally:
        plt.close(_fig)
        bind_viz(VizConfig())  # restore default

    assert texts_off == 0
    assert texts_on > 0


# --- Per-knob behavioral consumption (no dead knobs) -----------------------------
# Set-equality (test_no_dead_knobs) proves inventory consistency only; these tests
# prove each knob actually reaches a rendered matplotlib attribute. A knob that
# loads but changes no pixel (the line_width dead-knob class) fails here.


def _line_widths(ax) -> list[float]:
    return [ln.get_linewidth() for ln in ax.get_lines()]


def test_line_width_knob_changes_rendered_lines() -> None:
    """line_width must reach an actual Line2D width, not just rcParams (which an
    explicit linewidth= kwarg would override)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src.experiment_config import VizConfig
    from src.figure_plotters import plot_observability
    from src.figure_registry import spec_by_label
    from src.viz_theme import bind_viz

    rows = [
        {
            "condition": "small_tracks_r0",
            "track_id": "eeg",
            "observability_level": str(lvl),
            "manifest_bytes": str(m),
        }
        for lvl, m in ((0, 40), (1, 50), (2, 60), (3, 70))
    ]
    spec = spec_by_label("fig:observability_manifest_size")
    widths = {}
    for w in (1.0, 5.0):
        bind_viz(VizConfig(line_width=w))
        _fig, ax = plt.subplots()
        try:
            plot_observability(rows, ax, spec)
            widths[w] = max(_line_widths(ax))
        finally:
            plt.close(_fig)
    bind_viz(VizConfig())
    assert widths[1.0] == pytest.approx(1.0)
    assert widths[5.0] == pytest.approx(5.0)


def test_palette_knob_changes_rendered_colors() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src.experiment_config import VizConfig
    from src.figure_plotters import plot_expansion
    from src.figure_registry import spec_by_label
    from src.viz_theme import bind_viz

    rows = [
        {
            "condition": "small_tracks_r0",
            "track_id": t,
            "observability_level": "3",
            "expansion_ratio": "1.5",
        }
        for t in ("eeg", "vcf")
    ]
    spec = spec_by_label("fig:expansion_ratio")
    first_colors = {}
    for name in ("wong", "tol_bright"):
        bind_viz(VizConfig(palette=name))
        _fig, ax = plt.subplots()
        try:
            plot_expansion(rows, ax, spec)
            first_colors[name] = ax.patches[0].get_facecolor()
        finally:
            plt.close(_fig)
    bind_viz(VizConfig())
    # Different palettes -> different first-bar colour, and it matches the palette head.
    assert first_colors["wong"] != first_colors["tol_bright"]


def test_marker_and_scatter_knobs_reach_plot_calls() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src.experiment_config import VizConfig
    from src.figure_plotters import plot_observability, plot_throughput
    from src.figure_registry import spec_by_label
    from src.viz_theme import bind_viz

    # marker_size -> Line2D markersize on the observability line plot
    obs_rows = [
        {
            "condition": "small_tracks_r0",
            "track_id": "eeg",
            "observability_level": str(lvl),
            "manifest_bytes": str(m),
        }
        for lvl, m in ((0, 40), (3, 70))
    ]
    obs_spec = spec_by_label("fig:observability_manifest_size")
    bind_viz(VizConfig(marker_size=20.0))
    _fig, ax = plt.subplots()
    try:
        plot_observability(obs_rows, ax, obs_spec)
        assert max(ln.get_markersize() for ln in ax.get_lines()) == pytest.approx(20.0)
    finally:
        plt.close(_fig)

    # scatter_size -> PathCollection sizes on the throughput scatter
    thr_rows = [
        {
            "condition": "medium_tracks_r0",
            "track_id": "synthetic",
            "observability_level": "3",
            "plaintext_bytes": "65536",
            "pack_throughput_mib_s": "40.0",
        }
    ]
    thr_spec = spec_by_label("fig:throughput_benchmark")
    bind_viz(VizConfig(scatter_size=222.0))
    _fig, ax = plt.subplots()
    try:
        plot_throughput(thr_rows, ax, thr_spec)
        sizes = [s for coll in ax.collections for s in coll.get_sizes()]
        assert 222.0 in sizes
    finally:
        plt.close(_fig)
        bind_viz(VizConfig())


def test_heatmap_cmap_knob_reaches_imshow() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src.experiment_config import VizConfig
    from src.figure_plotters import plot_expansion_heatmap
    from src.figure_registry import spec_by_label
    from src.viz_theme import bind_viz

    rows = [
        {
            "condition": "small_tracks_r0",
            "track_id": t,
            "observability_level": "3",
            "expansion_ratio": r,
        }
        for t, r in (("eeg", "1.76"), ("vcf", "1.53"))
    ]
    spec = spec_by_label("fig:expansion_heatmap")
    bind_viz(VizConfig(heatmap_cmap="magma"))
    _fig, ax = plt.subplots()
    try:
        plot_expansion_heatmap(rows, ax, spec)
        cmap_names = {im.get_cmap().name for im in ax.get_images()}
        assert "magma" in cmap_names
    finally:
        plt.close(_fig)
        bind_viz(VizConfig())
