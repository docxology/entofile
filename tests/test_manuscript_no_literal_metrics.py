"""Manuscript body sections must not embed bare metric literals."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_DOC_ONLY = frozenset(
    {"AGENTS.md", "README.md", "SYNTAX.md", "99_references.md", "preamble.md"}
)
_TOKEN_BLOCK = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")

# Bare literals that must appear only inside {{TOKEN}} blocks in body sections.
# Every crypto/format constant has a canonical source in src/crypto.py and a
# manuscript token; a bare literal here is unvalidated and can silently drift.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Generic semantic-version shape: forward-safe — catches ANY bare X.Y.Z
    # (a future 0.3.2 / 0.4.0), not just the enumerated current versions. Every
    # ENTO format version has a token (FORMAT_VERSION / FORMAT_VERSION_HARDENED_FIRST
    # / FORMAT_VERSION_LATEST), so a bare X.Y.Z in a body section is always a drift risk.
    ("bare X.Y.Z version", re.compile(r"(?<!\{\{)\b\d+\.\d+\.\d+\b(?!\}\})")),
    ("tamper rate 1.0", re.compile(r"(?<!\{\{)1\.0(?!\}\})")),
    ("observability level 3", re.compile(r"level\s+3\b", re.I)),
    ("16-byte header", re.compile(r"16-byte", re.I)),
    # Hardened nonce size: must come from NONCE_BYTES_HARDENED.
    ("12-byte nonce", re.compile(r"12-byte", re.I)),
)


def _strip_token_blocks(text: str) -> str:
    return _TOKEN_BLOCK.sub("", text)


@pytest.mark.parametrize("pattern_name,pattern", _PATTERNS)
def test_manuscript_sections_avoid_bare_metric_literals(
    pattern_name: str, pattern: re.Pattern[str]
) -> None:
    root = Path(__file__).resolve().parent.parent
    manuscript_dir = root / "manuscript"
    hits: list[str] = []
    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in _DOC_ONLY:
            continue
        if not md_file.name[:2].isdigit():
            continue
        text = _strip_token_blocks(md_file.read_text(encoding="utf-8"))
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "manifest.json" in line and pattern_name.startswith("format"):
                continue
            if pattern.search(line):
                hits.append(f"{md_file.name}:{line_no}: {line.strip()[:120]}")
    assert not hits, f"Bare {pattern_name} outside tokens:\n" + "\n".join(hits)


# Spelled-out cardinalities that must be injected (COUNT_* tokens), not literals,
# so adding a level / hardened format / integrity value can't leave prose stale.
# Maps a forbidden bare-count regex to the token that should replace it.
_COUNT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "COUNT_OBSERVABILITY_LEVELS",
        re.compile(
            r"\b(two|three|four|five|\d+)\s+graded\s+observability\s+levels?\b", re.I
        ),
    ),
    (
        "COUNT_HARDENED_FORMATS",
        re.compile(r"\b(one|two|three|four|\d+)\s+opt-in\s+hardened\b", re.I),
    ),
    (
        "COUNT_INTEGRITY_LEVELS",
        re.compile(r"\bone of\s+(two|three|four|\d+)\s+values\b", re.I),
    ),
)


@pytest.mark.parametrize("token_name,pattern", _COUNT_PATTERNS)
def test_manuscript_counts_are_injected_not_spelled_out(
    token_name: str, pattern: re.Pattern[str]
) -> None:
    """A spelled-out count in body prose (e.g. 'four graded observability levels')
    must be the {{token_name}} token, not a literal — otherwise it drifts silently
    when the underlying enum grows. The token-strip removes legitimate {{TOKEN}} use,
    so any remaining match is a bare literal."""
    root = Path(__file__).resolve().parent.parent
    manuscript_dir = root / "manuscript"
    hits: list[str] = []
    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in _DOC_ONLY or not md_file.name[:2].isdigit():
            continue
        text = _strip_token_blocks(md_file.read_text(encoding="utf-8"))
        for line_no, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append(f"{md_file.name}:{line_no}: {line.strip()[:120]}")
    assert not hits, f"Spelled-out count should be {{{{{token_name}}}}}:\n" + "\n".join(
        hits
    )
