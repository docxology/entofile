"""Tests for the machine-readable research preregistration contract."""

from __future__ import annotations

from pathlib import Path

import yaml


def test_research_agenda_has_falsifiable_questions_and_stopping_rules() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = yaml.safe_load(
        (root / "docs" / "research" / "agenda.yaml").read_text(encoding="utf-8")
    )
    assert payload["protocol_version"] == 1
    assert payload["pre_registration"]["minimum_competing_hypotheses"] >= 3
    questions = payload["research_questions"]
    assert len(questions) == 8
    for question in questions:
        assert question["owner"]
        assert question["control"]
        assert len(question["hypotheses"]) >= 3
        assert question["metrics"]
        assert question["sample_size_or_repetition"]
        assert question["falsification"]
        assert question["stopping_rule"]
        assert question["limits"]
