"""Documentation consistency gates for the 0.5 manuscript release.

These tests pin RedTeam documentation failures that can otherwise render cleanly:
stale figure counts, stale manifest enum prose, future-public wording drift, and
format-support omissions in operator-facing help.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from src import crypto
from src.cli import build_parser
from src.figure_registry import FIGURE_SPECS
from src.structured_data import read_toml_mapping

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
    config = _read("docs/manuscript/config.yaml")
    preamble = _read("docs/manuscript/preamble.md")
    assert 'geometry: "margin=0.5in"' in config
    assert "\\geometry" not in preamble
    assert "\\usepackage[margin=" not in preamble


def test_template_transmission_bookends_are_release_configured() -> None:
    config = yaml.safe_load(_read("docs/manuscript/config.yaml"))
    publication = config["publication"]
    bookends = publication["transmission_bookends"]
    assert bookends["enabled"] is True
    assert bookends["show_steganography"] is False
    assert publication["github_repository"] == "docxology/entofile"

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
    assert schema["properties"]["format_version"]["enum"] == ["0.5.0"]
    assert "manifest_binding" in schema["required"]
    assert "allOf" not in schema

    architecture = " ".join(_read("docs/architecture.md").split())
    assert "enum contains only `0.5.0`" in architecture
    assert "`manifest_binding` is a required top-level field" in architecture
    for version in ("0.2.0", "0.3.0", "0.3.1", "0.4.0"):
        assert f"`{version}`" not in architecture


def test_threat_model_inventory_includes_length_disclosure_id() -> None:
    threat_model = _read("docs/entofile-threat-model.md")
    agents = _read("docs/AGENTS.md")
    assert "| TM-008 | Sealed plaintext-length disclosure |" in threat_model
    assert "TM-001-008" in agents
    assert "TM-001-007" not in agents


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
        "SECURITY.md": _read("SECURITY.md"),
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


def test_public_docs_do_not_claim_legacy_support() -> None:
    surfaces = {
        "SECURITY.md": _read("SECURITY.md"),
        "CONTRIBUTING.md": _read("CONTRIBUTING.md"),
        ".github/ISSUE_TEMPLATE/bug_report.yml": _read(
            ".github/ISSUE_TEMPLATE/bug_report.yml"
        ),
        "ISA.md": _read("ISA.md"),
        "tasks.yaml": _read("tasks.yaml"),
        "docs/operator_checklist.md": _read("docs/operator_checklist.md"),
        "docs/entofile-threat-model.md": _read("docs/entofile-threat-model.md"),
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

    for path in ("SECURITY.md", "CONTRIBUTING.md", "docs/operator_checklist.md"):
        for phrase in ("remain compatibility", "remain readable", "remain supported", "pack --format"):
            assert phrase not in surfaces[path].lower(), (path, phrase)


def test_todo_batch_docs_are_indexed_and_todo_updated() -> None:
    docs_readme = _read("docs/README.md")
    readme = _read("README.md")
    todo = _read("TODO.md")
    for rel in (
        "operator_checklist.md",
        "glossary.md",
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
    # The 2026-07-31 TODO cleanup (948e2a9) intentionally stripped the completed-batch
    # ledger ("Completed in TODO pass", the --json-output/--telemetry-jsonl sidecars,
    # benchmark_expanded.yaml, figure_layout_report.json, the promotion-metadata
    # checker) as that work shipped. The durable contract is that the batch docs are
    # indexed above AND that TODO remains a live roadmap pointing operators at the
    # scripts that regenerate the artifacts those docs reference.
    assert "Live-tree artifact state" in todo
    assert "scripts/ento_analysis.py" in todo
    assert "scripts/check_public_promotion_metadata.py" in todo


def test_public_cutover_scaffolding_is_indexed() -> None:
    docs_readme = _read("docs/README.md")
    readme = _read("README.md")
    todo = _read("TODO.md")
    for rel in ("SECURITY.md", "CITATION.cff", "CONTRIBUTING.md", "LICENSE"):
        assert (ROOT / rel).is_file(), rel
        assert rel in docs_readme
    assert "SECURITY.md" in readme
    assert "CITATION.cff" in readme
    # The public-cutover scaffolding shipped (the repo is live, so there is no longer
    # a TODO "public-cutover scaffolding" item); require that TODO is the maintained
    # roadmap rather than pinning that removed backlog entry.
    assert "## Maintenance Rule" in todo


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


def test_ci_uses_declared_python_only() -> None:
    project = read_toml_mapping(ROOT / "pyproject.toml")
    lock = read_toml_mapping(ROOT / "uv.lock")
    python_version = _read(".python-version").strip()
    assert python_version == "3.15"
    requires_python = project["project"]["requires-python"]
    assert requires_python == ">=3.15,<3.16"
    assert lock["requires-python"] == "==3.15.*"

    workflow = yaml.safe_load(_read(".github/workflows/ci.yml"))
    assert workflow["env"]["PYTHON_VERSION"] == python_version
    gates = workflow["jobs"]["gates"]
    assert "strategy" not in gates
    setup_uv = next(
        step for step in gates["steps"] if step.get("uses", "").startswith("astral-sh/setup-uv@")
    )
    assert setup_uv["with"]["python-version"] == "${{ env.PYTHON_VERSION }}"

    for relative in ("README.md", "docs/quickstart.md", "docs/rendering_pipeline.md"):
        assert f"Python {python_version}" in _read(relative), relative
    ci_doc = _read("docs/public_ci_dry_run.md")
    assert f"single Python {python_version} consumer cell" in ci_doc
    assert "--python 3.14" not in _read(".github/workflows/ci.yml")


def test_ci_actions_are_commit_pinned() -> None:
    workflow_paths = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflow_paths
    for workflow_path in workflow_paths:
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses", "")
                if uses and not uses.startswith(("./", "docker://")):
                    assert re.search(r"@[0-9a-f]{40}$", uses), uses


def test_ci_finalizes_real_rendered_inventory_after_tests() -> None:
    workflow = yaml.safe_load(_read(".github/workflows/ci.yml"))
    steps = workflow["jobs"]["gates"]["steps"]
    names = [step.get("name", "") for step in steps]
    certification_name = "Certify hydrated reader artifacts and full output inventory"
    assert names.index("Render actual PDF HTML and transmission artifacts") < names.index("Test with coverage")
    assert names.index("Test with coverage") < names.index(certification_name)
    assert names.index("Dashboard API and SBOM evidence") < names.index("Render actual PDF HTML and transmission artifacts")
    certification = steps[names.index(certification_name)]["run"]
    commands = (
        "scripts/pipeline/stage_03_render.py --project working/entofile",
        "scripts/audit_publication_readiness.py\" --check",
        "scripts/maintenance/refresh_artifact_manifests.py --project working/entofile",
        "scripts/pipeline/stage_04_validate.py --project working/entofile",
        "scripts/build_release_bundle.py",
        "sha256sum --check release/SHA256SUMS",
        "scripts/check_public_promotion_metadata.py --check",
    )
    positions = [certification.index(command) for command in commands]
    assert positions == sorted(positions)
    assert "--skip-manuscript-hydration" not in certification
    assert "--no-live-tests" not in certification


def test_manuscript_reproduction_names_complete_publication_finalization() -> None:
    reproducibility = _read("docs/manuscript/06_reproducibility.md")
    for command in (
        "scripts/run_tests.py",
        "scripts/audit_publication_readiness.py --check",
        "scripts/maintenance/refresh_artifact_manifests.py",
        "scripts/pipeline/stage_04_validate.py",
    ):
        assert command in reproducibility
    assert "planned public home" not in reproducibility
    assert "--skip-manuscript-hydration" not in reproducibility


def test_public_metadata_matches_manuscript_config() -> None:
    config = yaml.safe_load(_read("docs/manuscript/config.yaml"))
    cff = _read("CITATION.cff")
    pyproject = _read("pyproject.toml")
    assert f'version: "{config["paper"]["version"]}"' in cff
    assert f'doi: "{config["publication"]["doi"]}"' in cff
    assert config["authors"][0]["name"] in pyproject
    assert config["authors"][0]["email"] in pyproject
    assert 'license = "MIT"' in pyproject


def test_pack_help_has_no_format_selector() -> None:
    help_text = _pack_help()
    assert "--format" not in help_text
    assert "0.5.0" in help_text
    for version in ("0.2.0", "0.3.0", "0.3.1", "0.4.0"):
        assert version not in help_text
