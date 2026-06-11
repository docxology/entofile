"""Contract tests for code-derived benchmark figures."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg

from src.analysis import run_benchmark_pipeline
from src.experiment_config import load_experiment_config
from src.figure_registry import FIGURE_SPECS, caption_token, visual_contract_for_spec

EXPECTED_0_4_FIGURES = {
    "fig:format_compatibility_matrix",
    "fig:length_leakage_profile",
    "fig:conformance_outcomes",
    "fig:observability_redaction_matrix",
    "fig:release_evidence_map",
}


def _png_dpi(path: Path) -> int:
    """Read PNG pHYs chunk pixels-per-meter (approx DPI)."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    offset = 8
    while offset < len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        if chunk_type == b"pHYs" and length >= 9:
            ppm_x = int.from_bytes(chunk_data[0:4], "big")
            if chunk_data[8] == 1 and ppm_x:
                return round(ppm_x * 0.0254)
        offset += 12 + length
    return 0


def test_figure_registry_matches_generators(
    fast_benchmark_project: tuple[Path, object],
) -> None:
    root, cfg = fast_benchmark_project
    run_benchmark_pipeline(root, config=cfg)
    registry_path = root / "output" / "figures" / "figure_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry) == len(FIGURE_SPECS)
    labels = {spec.label for spec in FIGURE_SPECS}
    filenames = {spec.filename for spec in FIGURE_SPECS}
    assert EXPECTED_0_4_FIGURES <= labels
    assert len(labels) == len(filenames) == len(FIGURE_SPECS)
    cfg = load_experiment_config(root)
    for spec in FIGURE_SPECS:
        entry = registry[spec.label]
        png = root / "output" / "figures" / spec.filename
        assert png.is_file()
        assert entry["generated_by"] == spec.generated_by
        assert entry["caption"] == spec.caption
        assert entry["caption_token"] == caption_token(spec.label)
        contract = visual_contract_for_spec(spec)
        assert entry["takeaway"] == contract["takeaway"]
        assert entry["evidence"] == contract["evidence"]
        assert entry["caution"] == contract["caution"]
        dpi = _png_dpi(png)
        assert dpi == cfg.viz.dpi


def test_registered_figure_pngs_are_nonblank(
    fast_benchmark_project: tuple[Path, object],
) -> None:
    root, cfg = fast_benchmark_project
    run_benchmark_pipeline(root, config=cfg)
    for spec in FIGURE_SPECS:
        png = root / "output" / "figures" / spec.filename
        image = mpimg.imread(png)
        assert image.shape[0] >= 100
        assert image.shape[1] >= 100
        assert float(image.std()) > 0.001
