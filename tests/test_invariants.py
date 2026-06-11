"""Tests for format invariants."""

from __future__ import annotations

from pathlib import Path

from src.invariants import all_invariants


def test_all_invariants_pass() -> None:
    root = Path(__file__).resolve().parent.parent
    results = all_invariants(root)
    assert results
    for inv in results:
        if inv.kind == "equal":
            assert inv.actual == inv.expected


def test_invariant_result_passed_evaluates_per_kind() -> None:
    """The passed property must evaluate every kind, not default non-equal to True."""
    from src.invariants import InvariantResult

    assert InvariantResult("a", "equal", 5, 5).passed is True
    assert InvariantResult("b", "equal", 5, 6).passed is False
    assert InvariantResult("c", "close", 1.0, 1.0 + 1e-12).passed is True
    assert InvariantResult("d", "close", 1.0, 2.0).passed is False


def test_invariant_result_unknown_kind_raises() -> None:
    """An unrecognized kind must raise, never silently report passed=True."""
    import pytest

    from src.invariants import InvariantResult

    with pytest.raises(ValueError, match="unknown invariant kind"):
        _ = InvariantResult("x", "bogus", 1, 1).passed
