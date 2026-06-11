"""Every defined equation label is referenced and every reference is defined.

pandoc-crossref resolves ``[@eq:label]`` against ``$$ ... $$ {#eq:label}``. A
defined-but-unreferenced equation renders without a number anchor in use; a
referenced-but-undefined label renders as a dangling ``[@eq:?]``. This test makes
the autoreference contract a gate so formal content cannot silently rot.
"""

from __future__ import annotations

import re
from pathlib import Path

_MANUSCRIPT = Path(__file__).resolve().parent.parent / "manuscript"
_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})
_DEF_RE = re.compile(r"\{#eq:([a-z0-9_]+)\}")
_REF_RE = re.compile(r"\[@eq:([a-z0-9_]+)\]")


def _combined_text() -> str:
    return "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(_MANUSCRIPT.glob("*.md"))
        if p.name not in _DOC_ONLY
    )


def test_every_equation_definition_is_referenced() -> None:
    text = _combined_text()
    defined = set(_DEF_RE.findall(text))
    referenced = set(_REF_RE.findall(text))
    assert defined, "no equation definitions found — formal section missing?"
    unreferenced = sorted(defined - referenced)
    assert not unreferenced, (
        f"equation labels defined but never [@eq:...]-referenced: {unreferenced}"
    )


def test_every_equation_reference_is_defined() -> None:
    text = _combined_text()
    defined = set(_DEF_RE.findall(text))
    referenced = set(_REF_RE.findall(text))
    dangling = sorted(referenced - defined)
    assert not dangling, (
        f"[@eq:...] references with no {{#eq:...}} definition (would render dangling): {dangling}"
    )


def test_equation_labels_are_unique() -> None:
    text = _combined_text()
    all_defs = _DEF_RE.findall(text)
    dupes = sorted({label for label in all_defs if all_defs.count(label) > 1})
    assert not dupes, (
        f"duplicate {{#eq:...}} labels (pandoc-crossref needs unique anchors): {dupes}"
    )


def test_formal_section_defines_the_expansion_law() -> None:
    # Keystone: the expansion law equation must exist and be referenced.
    text = _combined_text()
    assert "{#eq:expansion_law}" in text
    assert "[@eq:expansion_law]" in text


# The complete set of manuscript equations, each bound to code in
# tests/test_equation_code_fidelity.py. A 7th equation cannot appear unbound:
# adding one fails this count-guard until it is both fidelity-tested and listed here.
_BOUND_EQUATIONS = frozenset(
    {
        "container_map",
        "track_key",
        "track_member",
        "expansion_law",
        "integrity_levels",
        "observability_monotone",
    }
)


def test_equation_set_is_exactly_the_bound_set() -> None:
    """Every equation rendered in the manuscript is in the fidelity-bound set, and
    vice versa — so no equation can ship without an executable code-fidelity test."""
    defined = set(_DEF_RE.findall(_combined_text()))
    assert defined == _BOUND_EQUATIONS, (
        f"equation set drifted from the fidelity-bound set: "
        f"unbound={sorted(defined - _BOUND_EQUATIONS)}, missing={sorted(_BOUND_EQUATIONS - defined)}. "
        f"Add a binding test in test_equation_code_fidelity.py and update _BOUND_EQUATIONS."
    )
