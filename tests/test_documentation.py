"""Tests for documentation generator."""

from __future__ import annotations

from pathlib import Path

from src.documentation import build_api_reference_markdown, run_api_doc_generation


def test_api_docs() -> None:
    root = Path(__file__).resolve().parent.parent
    text = build_api_reference_markdown(root)
    assert "crypto" in text
    assert "GCM" in text
    assert "CTR" not in text
    assert "HMAC-SHA256" not in text
    path = run_api_doc_generation(root)
    assert path.exists()
