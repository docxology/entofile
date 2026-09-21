"""Registry markdown helpers and caption token parity."""

from __future__ import annotations

import json
from pathlib import Path
from src.figure_registry import (
    FIGURE_SPECS,
    caption_token,
    figure_block_markdown,
    figure_index_markdown,
    manuscript_image_markdown,
    visual_contract_for_spec,
    visual_evidence_contract_markdown,
    write_figure_registry,
)


def test_manuscript_image_markdown_uses_caption_token() -> None:
    spec = FIGURE_SPECS[1]
    line = manuscript_image_markdown(spec, default_width="90")
    token = caption_token(spec.label)
    assert f"{{{{{token}}}}}" in line
    assert spec.filename in line
    assert f"#{spec.label}" in line


def test_figure_blocks_include_all_section_figures() -> None:
    results_block = figure_block_markdown("results", default_width="90")
    assert results_block.count("../output/figures/") == 5
    assert "benchmark_overview.png" in results_block


def test_figure_index_lists_all_specs() -> None:
    index = figure_index_markdown()
    for spec in FIGURE_SPECS:
        assert spec.label in index
        assert spec.filename in index
        assert spec.kind in index
        assert visual_contract_for_spec(spec)["takeaway"] in index


def test_visual_contracts_cover_every_registered_figure() -> None:
    for spec in FIGURE_SPECS:
        contract = visual_contract_for_spec(spec)
        assert set(contract) == {"takeaway", "evidence", "caution"}
        assert all(contract.values())
        assert spec.label.removeprefix("fig:") not in contract["takeaway"].lower()
        assert "universal" not in contract["caution"].lower()


def test_visual_evidence_contract_markdown_lists_every_figure() -> None:
    table = visual_evidence_contract_markdown()
    assert "| Figure | Takeaway | Evidence | Caution |" in table
    for spec in FIGURE_SPECS:
        contract = visual_contract_for_spec(spec)
        assert spec.label in table
        assert contract["takeaway"] in table
        assert contract["evidence"] in table
        assert contract["caution"] in table


def test_write_figure_registry_emits_relative_filenames_and_alt_text(
    tmp_path: Path,
) -> None:
    """Registry JSON must publish safe relative paths plus caption alt text."""
    figures_dir = tmp_path / "output" / "figures"
    outputs = {
        spec.label: figures_dir / spec.filename
        for spec in FIGURE_SPECS
    }
    registry_path = write_figure_registry(tmp_path, outputs)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert set(registry) == {spec.label for spec in FIGURE_SPECS}
    for spec in FIGURE_SPECS:
        entry = registry[spec.label]
        filename = entry["filename"]
        assert not filename.startswith("/")
        assert "\\" not in filename
        assert (figures_dir / filename).resolve() == (figures_dir / spec.filename).resolve()
        alt_text = entry["alt_text"]
        assert alt_text
        assert alt_text == spec.caption[: len(alt_text)]
        assert alt_text[-1] in ".!?"
