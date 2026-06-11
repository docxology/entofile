"""Tests for claim ledger alignment."""

from __future__ import annotations

from pathlib import Path

import yaml


def test_claim_ledger_format_version() -> None:
    root = Path(__file__).resolve().parent.parent
    ledger = yaml.safe_load(
        (root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8")
    )
    claims = {c["claim_id"]: c for c in ledger["claims"]}
    from src import crypto

    assert claims["format-version"]["value"] == crypto.FORMAT_VERSION
    assert "working/entofile" in claims["format-version"]["source"]


def test_claim_ledger_format_version_latest() -> None:
    root = Path(__file__).resolve().parent.parent
    ledger = yaml.safe_load(
        (root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8")
    )
    claims = {c["claim_id"]: c for c in ledger["claims"]}
    import json as _json

    from src import crypto

    latest = claims["format-version-latest"]["value"]
    assert latest == crypto.FORMAT_VERSION_LATEST
    assert latest in crypto.SUPPORTED_FORMAT_VERSIONS
    schema = _json.loads(
        (root / "data" / "ento_manifest_schema.json").read_text(encoding="utf-8")
    )
    assert latest in schema["properties"]["format_version"]["enum"]


def test_figure_dpi_matches_figures_module() -> None:
    root = Path(__file__).resolve().parent.parent
    ledger = yaml.safe_load(
        (root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8")
    )
    claims = {c["claim_id"]: c for c in ledger["claims"]}
    dpi_claim = claims["figure-export-dpi"]
    from src.figures import VIZ_CONFIG

    assert int(dpi_claim["value"]) == VIZ_CONFIG["dpi"]


def test_figure_width_matches_viz_config() -> None:
    root = Path(__file__).resolve().parent.parent
    ledger = yaml.safe_load(
        (root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8")
    )
    claims = {c["claim_id"]: c for c in ledger["claims"]}
    from src.experiment_config import load_experiment_config
    from src.figures import VIZ_CONFIG

    cfg = load_experiment_config(root)
    assert int(claims["figure-display-width"]["value"]) == cfg.viz.figure_width_percent
    assert VIZ_CONFIG["figure_width_percent"] == cfg.viz.figure_width_percent


def test_master_key_bytes_matches_crypto() -> None:
    root = Path(__file__).resolve().parent.parent
    ledger = yaml.safe_load(
        (root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8")
    )
    claims = {c["claim_id"]: c for c in ledger["claims"]}
    from src.crypto import MASTER_KEY_SIZE

    assert int(claims["master-key-bytes"]["value"]) == MASTER_KEY_SIZE


def test_figure_count_claim_matches_registry() -> None:
    """Bind the ledger's figure-count cell to FIGURE_SPECS so it cannot go stale."""
    root = Path(__file__).resolve().parent.parent
    ledger = yaml.safe_load(
        (root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8")
    )
    claims = {c["claim_id"]: c for c in ledger["claims"]}
    from src.figure_registry import FIGURE_SPECS

    assert int(claims["figure-count"]["value"]) == len(FIGURE_SPECS)
