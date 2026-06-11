"""Every registered figure label must appear in manuscript cross-references."""

from __future__ import annotations

import re
from pathlib import Path

from src.figure_registry import FIGURE_SPECS

_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})
_CROSSREF_RE = re.compile(r"\[@fig:([a-z0-9_]+)\]")
# An image definition pandoc-crossref can number: ![...]{#fig:label ...}
_IMAGE_DEF_RE = re.compile(r"\{#fig:([a-z0-9_]+)[ }]")


def _combined_manuscript() -> str:
    manuscript_dir = Path(__file__).resolve().parent.parent / "manuscript"
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(manuscript_dir.glob("*.md")) if path.name not in _DOC_ONLY
    )


def test_each_figure_label_has_crossref_in_manuscript() -> None:
    referenced = set(_CROSSREF_RE.findall(_combined_manuscript()))
    missing = [
        spec.label.removeprefix("fig:") for spec in FIGURE_SPECS if spec.label.removeprefix("fig:") not in referenced
    ]
    assert not missing, f"Missing [@fig:...] cross-references for: {missing}"


def test_each_figure_label_has_image_definition() -> None:
    """Every registered figure needs an ``![...]{#fig:label}`` image line.

    A [@fig:label] reference without a matching image definition renders as a
    dangling 'fig. ??' (pandoc-crossref has nothing to number). This is the gate
    that catches a referenced-but-never-placed figure — a reference-only check
    passes while the PDF shows '??'.
    """
    defined = set(_IMAGE_DEF_RE.findall(_combined_manuscript()))
    missing = [
        spec.label.removeprefix("fig:") for spec in FIGURE_SPECS if spec.label.removeprefix("fig:") not in defined
    ]
    assert not missing, f"Registered figures with no ![...]{{#fig:...}} image definition (would render 'fig. ??'): {missing}"


def test_every_figure_reference_resolves_to_a_definition() -> None:
    """No [@fig:label] may reference a label that has no image definition."""
    text = _combined_manuscript()
    referenced = set(_CROSSREF_RE.findall(text))
    defined = set(_IMAGE_DEF_RE.findall(text))
    dangling = sorted(referenced - defined)
    assert not dangling, f"[@fig:...] references with no image definition (dangling 'fig. ??'): {dangling}"
