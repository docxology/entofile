"""Tests that figure caption tokens stay aligned with the registry."""

from __future__ import annotations

import re
from pathlib import Path

from src.figure_registry import FIGURE_SPECS, caption_token, figure_caption_variables
from src.manuscript_variables import generate_variables

_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})
_IMAGE_ALT_RE = re.compile(r"!\[(.*?)\]\(\.\./output/figures/")


def test_figure_caption_variables_match_registry() -> None:
    exported = figure_caption_variables()
    assert len(exported) == len(FIGURE_SPECS)
    for spec in FIGURE_SPECS:
        token = caption_token(spec.label)
        assert exported[token] == spec.caption


def test_manuscript_figure_alt_text_uses_caption_tokens() -> None:
    project_root = Path(__file__).resolve().parent.parent
    produced = generate_variables(project_root)
    manuscript_dir = project_root / "manuscript"
    missing_tokens: list[str] = []
    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in _DOC_ONLY:
            continue
        for alt_text in _IMAGE_ALT_RE.findall(md_file.read_text(encoding="utf-8")):
            if alt_text.startswith("{{FIG_CAPTION_") and alt_text.endswith("}}"):
                token = alt_text[2:-2]
                if token not in produced:
                    missing_tokens.append(f"{md_file.name}: {token}")
            elif alt_text and not alt_text.startswith("{{FIG_CAPTION_"):
                missing_tokens.append(f"{md_file.name}: static alt text {alt_text!r}")
    assert not missing_tokens, (
        "Figure alt text must use {{FIG_CAPTION_*}} tokens:\n"
        + "\n".join(missing_tokens)
    )


def test_figure_captions_avoid_unbounded_local_evidence_claims() -> None:
    captions = "\n".join(spec.caption for spec in FIGURE_SPECS).lower()
    forbidden = (
        "near-constant",
        "does not measurably slow",
        "catches every corruption",
        "no measurable slowdown",
    )
    for phrase in forbidden:
        assert phrase not in captions
