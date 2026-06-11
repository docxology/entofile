"""Documentation consistency gates for the 0.4 manuscript RC.

These tests pin RedTeam documentation failures that can otherwise render cleanly:
stale figure counts, stale manifest enum prose, future-public wording drift, and
format-support omissions in operator-facing help.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from src import crypto
from src.cli import build_parser
from src.figure_registry import FIGURE_SPECS


ROOT = Path(__file__).resolve().parent.parent


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _pack_help() -> str:
    parser = build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices["pack"].format_help()
    raise AssertionError("pack subparser not found")


def test_pdf_margin_is_project_local_config_not_preamble() -> None:
    config = _read("manuscript/config.yaml")
    preamble = _read("manuscript/preamble.md")
    assert 'geometry: "margin=0.5in"' in config
    assert "\\geometry" not in preamble
    assert "\\usepackage[margin=" not in preamble


def test_template_transmission_bookends_are_release_configured() -> None:
    config = yaml.safe_load(_read("manuscript/config.yaml"))
    publication = config["publication"]
    bookends = publication["transmission_bookends"]
    assert bookends["enabled"] is True
    assert bookends["show_steganography"] is False
    assert publication["github_repository"] == "planned public home: docxology/entofile"

    rendering_pipeline = _read("docs/rendering_pipeline.md")
    assert "BEGINNING OF TRANSMISSION" in rendering_pipeline
    assert "END OF TRANSMISSION" in rendering_pipeline


def test_registered_figure_docs_do_not_pin_stale_count() -> None:
    methods = _read("docs/methods.md")
    registry = _read("docs/figure_registry.md")
    assert "14 registered figures" not in methods
    assert f"Registered figures ({len(FIGURE_SPECS)})" in registry


def test_visual_evidence_contract_is_documented() -> None:
    registry = _read("docs/figure_registry.md")
    methods = _read("docs/methods.md")
    inventory = _read("docs/output_inventory.md")
    research = _read("docs/research/reproducible_figures_crypto_vectors.md")
    assert "Visual evidence contract" in registry
    assert "takeaway" in registry.lower()
    assert "evidence" in registry.lower()
    assert "caution" in registry.lower()
    for spec in FIGURE_SPECS:
        assert spec.label in registry
    assert "takeaway, evidence, and caution" in methods
    assert "figure_registry.json" in inventory
    assert "takeaway" in research


def test_architecture_manifest_enum_matches_supported_formats() -> None:
    schema = json.loads(_read("data/ento_manifest_schema.json"))
    assert (
        tuple(schema["properties"]["format_version"]["enum"])
        == crypto.SUPPORTED_FORMAT_VERSIONS
    )

    architecture = _read("docs/architecture.md")
    for version in crypto.SUPPORTED_FORMAT_VERSIONS:
        assert f"`{version}`" in architecture
    assert "`format_version` enum: `0.2.0`." not in architecture


def test_threat_model_inventory_includes_length_disclosure_id() -> None:
    threat_model = _read("docs/entofile-threat-model.md")
    agents = _read("docs/AGENTS.md")
    assert "| TM-008 | Sealed plaintext-length disclosure |" in threat_model
    assert "TM-001–008" in agents
    assert "TM-001–007" not in agents


def test_public_repository_language_is_published() -> None:
    """Post-publication (2026-06-11): the repo is live at
    github.com/docxology/entofile with a resolving DOI. Consumer-facing surfaces
    must describe it in the present tense and must NOT carry the pre-publication
    'planned/not-yet-public' framing that would now mislead a reader."""
    expected = "https://github.com/docxology/entofile"
    surfaces = {
        "README.md": _read("README.md"),
        "docs/README.md": _read("docs/README.md"),
        "docs/faq.md": _read("docs/faq.md"),
        "docs/agent_instructions.md": _read("docs/agent_instructions.md"),
    }
    stale = (
        "planned public",
        "public later",
        "until promotion",
        "not the current build source",
    )
    for path, text in surfaces.items():
        assert expected in text, path
        lowered = text.lower()
        for phrase in stale:
            assert phrase not in lowered, (
                f"{path}: stale pre-publication phrase {phrase!r}"
            )

    # The README states the live public home and the development source.
    assert "Public home:" in surfaces["README.md"]
    assert "projects/working/entofile" in surfaces["README.md"]


def test_public_docs_do_not_describe_0_2_0_as_current_default() -> None:
    surfaces = {
        "SECURITY.md": _read("SECURITY.md"),
        "CONTRIBUTING.md": _read("CONTRIBUTING.md"),
        ".github/ISSUE_TEMPLATE/bug_report.yml": _read(
            ".github/ISSUE_TEMPLATE/bug_report.yml"
        ),
        "ISA.md": _read("ISA.md"),
        "docs/operator_checklist.md": _read("docs/operator_checklist.md"),
        "docs/entofile-threat-model.md": _read("docs/entofile-threat-model.md"),
        "tests/test_format_0_3_0.py": _read("tests/test_format_0_3_0.py"),
    }
    forbidden = (
        "`0.2.0` as the default",
        "default writes remain format `0.2.0`",
        "default writes remain format 0.2.0",
        "default writes remain `0.2.0`",
        "0.2.0 stays default",
        "0.2.0 stays the default",
        "0.2.0 still default",
        "format stays 0.2.0",
        "default published wire format",
    )
    for path, text in surfaces.items():
        normalised = " ".join(text.lower().split())
        for phrase in forbidden:
            assert " ".join(phrase.lower().split()) not in normalised, path

    for path in (
        "SECURITY.md",
        "docs/operator_checklist.md",
        "docs/entofile-threat-model.md",
    ):
        assert crypto.FORMAT_VERSION in surfaces[path], path


def test_todo_batch_docs_are_indexed_and_todo_updated() -> None:
    docs_readme = _read("docs/README.md")
    readme = _read("README.md")
    todo = _read("TODO.md")
    for rel in (
        "operator_checklist.md",
        "glossary.md",
        "format_migration.md",
        "provenance_signing.md",
        "release_notes_template.md",
        "public_release_checklist.md",
        "public_ci_dry_run.md",
        "benchmark_profiles.md",
        "evidence_provenance.md",
        "kms_hsm_profile.md",
        "pq_transition_note.md",
        "streaming_design.md",
        "manifest_extension_policy.md",
    ):
        assert rel in docs_readme
    assert "operator_checklist.md" in readme
    assert "Completed in TODO pass" in todo
    assert "--json-output" in todo
    assert "--telemetry-jsonl" in todo
    assert "benchmark_expanded.yaml" in todo
    assert "figure_layout_report.json" in todo
    assert "public-promotion metadata checker" in todo


def test_public_cutover_scaffolding_is_indexed() -> None:
    docs_readme = _read("docs/README.md")
    readme = _read("README.md")
    todo = _read("TODO.md")
    for rel in ("SECURITY.md", "CITATION.cff", "CONTRIBUTING.md", "LICENSE"):
        assert (ROOT / rel).is_file(), rel
        assert rel in docs_readme
    assert "SECURITY.md" in readme
    assert "CITATION.cff" in readme
    assert "public-cutover scaffolding" in todo


def test_public_repo_settings_scaffold_exists() -> None:
    codeowners = _read(".github/CODEOWNERS")
    # Owner must be the real GitHub handle for the planned public repo
    # (docxology/entofile) — a local machine username like "@4d" would make
    # GitHub silently skip every ownership rule after cutover.
    assert "/src/crypto.py @docxology" in codeowners
    assert "/src/container.py @docxology" in codeowners
    assert "/src/release_bundle.py @docxology" in codeowners
    assert "/SECURITY.md @docxology" in codeowners
    assert "@4d" not in codeowners


def test_public_release_docs_include_live_endpoint_gate() -> None:
    live_gate = "--require-public-endpoints --live-public-endpoints"
    for rel in (
        "docs/public_release_checklist.md",
        "docs/public_ci_dry_run.md",
        "docs/publication_checklist.md",
        "docs/provenance_signing.md",
        "docs/output_conventions.md",
    ):
        text = _read(rel)
        assert "check_public_promotion_metadata.py --check" in text, rel
        assert live_gate in text, rel


def test_publication_docs_mark_test_results_as_non_certifying() -> None:
    publication = _read("docs/publication_checklist.md")
    conventions = _read("docs/output_conventions.md")
    for text in (publication, conventions):
        assert "test_results.json" in text
        assert "audit_publication_readiness.py --check" in text
    assert "contextual only" in conventions
    assert "not use it to certify" in publication


def test_public_metadata_matches_manuscript_config() -> None:
    config = yaml.safe_load(_read("manuscript/config.yaml"))
    cff = _read("CITATION.cff")
    pyproject = _read("pyproject.toml")
    assert f'version: "{config["paper"]["version"]}"' in cff
    assert f'doi: "{config["publication"]["doi"]}"' in cff
    assert config["authors"][0]["name"] in pyproject
    assert config["authors"][0]["email"] in pyproject
    assert 'license = { file = "LICENSE" }' in pyproject


def test_pack_help_mentions_every_supported_format() -> None:
    help_text = _pack_help()
    for version in crypto.SUPPORTED_FORMAT_VERSIONS:
        assert version in help_text
    assert "0.3.1" in help_text
    assert "length" in help_text
    assert "padding" in help_text
