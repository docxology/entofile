"""Guard against statistics prose drifting from run-variable data.

Timing metrics are re-measured every run, so the manuscript must not hardcode a
claim that depends on a particular run's variance regime (e.g. "the lower bound is
negative", a specific CV value, or "the interval extends below zero"). Such a
sentence is true for one draw and false for the next — the exact prose-vs-artifact
drift this test forbids. Numeric values must come through {{RESULT_*}} tokens.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_INTERP = (
    Path(__file__).resolve().parent.parent
    / "manuscript"
    / "03a_benchmark_interpretation.md"
)
_ABSTRACT = Path(__file__).resolve().parent.parent / "manuscript" / "00_abstract.md"

# Phrases that assert a run-specific outcome the next run could contradict. The
# class is "any qualitative verdict on dispersion magnitude or CI sign" — not just
# the literal phrasing of the first bug found. A bare sign/magnitude claim flips on
# the documented CV swing (single-digit to high-double-digit across runs), so it is
# banned regardless of synonym. (Numbers themselves are allowed via {{RESULT_*}}.)
_FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Sign claims about the CI lower bound (any verb): "is negative", "can fall below zero", ...
    (
        "asserts a lower-bound sign",
        re.compile(r"lower bound\b.{0,30}\b(negative|unphysical|below zero)", re.I),
    ),
    (
        "asserts the interval includes/excludes zero",
        re.compile(
            r"\b(interval|CI|band)\b.{0,30}\b(includes?|excludes?|contains?)\s+zero",
            re.I,
        ),
    ),
    # Magnitude verdicts: "high-variance", "low variance", "highly consistent" (any following word).
    ("high/low variance verdict", re.compile(r"\b(high|low)[\s-]variance\b", re.I)),
    (
        "consistency verdict",
        re.compile(r"\bhighly (consistent|stable|reproducible)\b", re.I),
    ),
    # Comparative CI-width adjectives asserting a run-specific shape.
    (
        "CI-width adjective",
        re.compile(
            r"\b(tight|narrow|wide)\b.{0,20}\b(CI|interval|band|confidence)\b", re.I
        ),
    ),
    (
        "CI-width adjective (reversed)",
        re.compile(
            r"\b(CI|interval|band|confidence interval)\b.{0,20}\b(is|are|was)\s+(tight|narrow|wide)\b",
            re.I,
        ),
    ),
    # Hardcoded CV / SD numerals outside {{TOKEN}} blocks.
    ("hardcoded CV percentage", re.compile(r"\bCV\s+\d+(\.\d+)?\s*%", re.I)),
)


@pytest.mark.parametrize("name,pattern", _FORBIDDEN_PATTERNS)
def test_statistics_prose_makes_no_run_specific_claim(
    name: str, pattern: re.Pattern[str]
) -> None:
    for path in (_INTERP, _ABSTRACT):
        # Strip {{TOKEN}} blocks: a token-sourced number is allowed, a hardcoded one is not.
        text = re.sub(r"\{\{[A-Z0-9_]+\}\}", "", path.read_text(encoding="utf-8"))
        hits = [ln.strip()[:100] for ln in text.splitlines() if pattern.search(ln)]
        assert not hits, (
            f"{path.name}: run-specific statistics claim ({name}):\n" + "\n".join(hits)
        )


@pytest.mark.parametrize(
    "synonym",
    [
        "the CI is narrow",
        "the confidence interval is wide",
        "throughput is high-variance at this n",
        "the lower bound can fall below zero",
        "the interval excludes zero",
        "reps are highly consistent",
        "observed CV 57%",
    ],
)
def test_guard_bites_on_run_specific_synonyms(synonym: str) -> None:
    """Meta-test: prove the guard red-flags the *next synonym*, not just the first
    bug's literal wording. Each phrase must match at least one forbidden pattern —
    otherwise the guard inherits the write-time blind spot it was meant to close."""
    matched = any(pattern.search(synonym) for _name, pattern in _FORBIDDEN_PATTERNS)
    assert matched, f"guard does not catch run-specific phrasing: {synonym!r}"


def test_dispersion_uses_tokens_for_numbers() -> None:
    """The dispersion subsection sources n / SD / CV / CI from tokens, not literals."""
    text = _INTERP.read_text(encoding="utf-8")
    assert "## Statistical dispersion and reliability" in text
    for token in (
        "{{CONFIG_BENCHMARK_REPETITIONS}}",
        "{{CONFIG_BENCHMARK_PILOT_REPETITIONS}}",
        "{{CONFIG_BENCHMARK_REPETITION_SCALE}}",
        "{{RESULT_ROWS_PER_REPETITION}}",
        "{{RESULT_EXPECTED_BENCHMARK_ROWS}}",
        "{{RESULT_THROUGHPUT_N}}",
        "{{RESULT_THROUGHPUT_DF}}",
        "{{RESULT_THROUGHPUT_CI_METHOD}}",
        "{{RESULT_THROUGHPUT_SD_MIB_S}}",
        "{{RESULT_THROUGHPUT_CV_PERCENT}}",
        "{{RESULT_THROUGHPUT_CI95_LO_MIB_S}}",
        "{{RESULT_THROUGHPUT_CI95_HI_MIB_S}}",
    ):
        assert token in text, f"dispersion subsection missing {token}"


def test_manuscript_has_no_stale_three_rep_sample_language() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            _INTERP,
            Path(__file__).resolve().parent.parent
            / "manuscript"
            / "05_experimental_setup.md",
        )
    ).lower()
    stale_phrases = (
        "small sample",
        "small repetition count",
        "cannot support a normality check",
        "many more repetitions",
        "only n =",
        "3 points",
    )
    for phrase in stale_phrases:
        assert phrase not in text
