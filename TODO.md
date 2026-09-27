# TODO — ENTO Upcoming Improvements

This roadmap tracks remaining research and engineering work for the 0.5.0
release line. It is intentionally scoped as a backlog, not a promise: each
item should become a test-backed issue or PR before implementation. Preserve
the current interface unless an item explicitly calls for a breaking release.

- Default write format is `0.5.0`, with authenticated exported-manifest context.
- Compatibility formats `0.2.0`, `0.3.0`, `0.3.1`, and `0.4.0` remain readable/writable.
- Paper/manuscript release label `0.5` is distinct from ENTO wire-format string `0.5.0`.

## Live-tree artifact state (2026-07-31)

The `output/` directory is gitignored. Generated artifacts (container
verification, benchmark reports, release manifest, conformance fixtures,
figure QA report, transmission manifest) are recreated locally by running:

```bash
uv run python scripts/ento_analysis.py
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
uv run python scripts/check_figure_layout.py
uv run python scripts/build_release_bundle.py
uv run python scripts/check_public_promotion_metadata.py --check
```

The manuscript PDF and HTML render outputs (`output/pdf/`, `output/web/`)
require a template repository checkout (see `docs/rendering_pipeline.md`).

Live-tree promotion tests (`test_public_promotion_metadata_current_tree`,
`test_public_promotion_script_check`,
`test_public_promotion_script_release_mode_blocks_unpublished_endpoints`)
and the container-verification claim binding
(`test_container_verification_report_claim`) depend on these artifacts being
present. Run the pipeline above before executing the full test suite to
ensure these pass.

## Minor Updates

- [x] CLI output formatting: ensure human-readable pretty-printing, tabulations, and clear JSON sidecar telemetry format flags across commands.
- [x] Typing annotations: audit and complete strict type annotations across public API functions, container models, and CLI arguments.
- [x] Docstring coverage: expand docstrings with clear parameter definitions, return values, and security contract caveats across core modules.
- [x] Keep figure captions compact after dense benchmark refreshes; prefer injected tokens for row counts, figure counts, SBOM status, and benchmark scale.

## Medium Improvements

- [x] Enhanced conformance fixtures: expand deterministic test cases for malformed manifest JSON, duplicate track headers, uncanonical padding, and cross-version key derivation.
- [x] Container verification report generation: enrich structured verification diagnostics, negative control assertions, and timing telemetry in container verification reports.
- [x] Legacy format compatibility tests: comprehensive multi-format (0.2.0, 0.3.0, 0.3.1, 0.4.0, 0.5.0) matrix testing covering cross-format decrypt, downgrade resistance, and format conversions.
- [x] Visual diffing: refine figure pixel digest comparisons with configurable tolerance windows for intentional theme updates.

## Major Initiatives

- [x] High-throughput chunk streaming: implement bounded-memory chunk-based pack and unpack streams (`pack_container_stream`, `unpack_container_stream`) preserving strict verify-before-release semantics.
- [x] Hardware-accelerated encryption pipeline: add runtime detection and benchmarking hooks for hardware-accelerated AES-NI / GCM cipher pipelines.
- [x] Complete public promotion metadata verification: expand promotion pre-flight checker to validate repository topics, license integrity, clean branch state, and signed release tags.

## Major Initiatives (Owner scoping required)

- [ ] **KMS/HSM custody integration hooks:** Design formal interfaces for external key custody and secure envelope encryption.
  - **Acceptance criteria:** Formal API specification document with custody model, rotation protocol, audit trail requirements, and threat model boundaries. Implementation follows specification.
  - **Dependencies:** Security review of custody delegation patterns, HSM vendor compatibility research.
  - **Scope:** API design and specification only; full HSM integration requires deployment infrastructure and external vendor coordination.

## Research agenda

The benchmark design overlay remains machine-readable in `experiment_plan.yaml`;
the preregistered backlog is machine-readable in `docs/research/agenda.yaml` and
explained in `docs/research/agenda.md`. Its current questions are:

- RQ-1: independent-language vectors and schema negotiation.
- RQ-2: bounded-memory streaming pack/unpack with verify-before-release.
- RQ-3: observability and metadata leakage across formats and levels.
- RQ-4: cryptographic interoperability, nonce discipline, and canonical padding.
- RQ-5: KMS/HSM custody, rotation, recovery, and audit boundaries.
- RQ-6: signed release manifests, SBOMs, provenance, and reproducible builds.
- RQ-7: exports to related research-container ecosystems without equivalence claims.
- RQ-8: default-migration validation for the `0.5.0` authenticated context profile.

Every question requires three competing hypotheses, a control or baseline, exact
metrics, a repetition rationale, falsification criteria, and a stopping rule.
Results remain bounded by the protocol and cannot certify an external ecosystem,
public endpoint, or origin signature without independent evidence.

## Agent-ergonomics pass (2026-08-31)

Findings from the 2026-08-31 doc-fleet deep pass. Completed items are checked
with their fix; each claim was verified in-session (link checker over README,
AGENTS.md, TODO.md, entofile.md, and every docs/**.md).

### Minor
- [x] 37 broken relative links left behind by the `manuscript/` -> `docs/manuscript/`
      migration (docs/*.md pointing at `../manuscript/`, docs/manuscript/*.md with
      stale `../docs/` and `../output/` depths). Fixed in-session; link checker
      now reports 0 broken of 164 checked.

### Medium
- [x] Mid-migration incoherence: `src/` modules (`analysis.py`, `manuscript_variables.py`,
      `publication.py`, `release_bundle.py`, `sbom.py`, `public_promotion.py`,
      `paths.py`, `experiment_config.py`) and 11 test files still read the deleted
      `manuscript/` dir; tests failed with FileNotFoundError. Paths updated to
      `docs/manuscript/`; affected suites re-run (results recorded in git history).
- [x] `docs/manuscript/MANUSCRIPT_STATUS.md` misdescribes itself ("legacy
      `docs/manuscript/` fallback") — corrected to name `manuscript/` as the
      legacy location.

### Major
- [x] Complete the release-evidence state after migration: regenerate
      `output/reports/*` via the pipeline (see TODO.md artifact-state section above)
      so promotion/verification tests bind against fresh artifacts. Completed 2026-08-31
      via scripts/ento_analysis.py + generate_conformance_fixtures.py + verify_conformance_fixtures.py
      + check_figure_layout.py + build_release_bundle.py. Artifact refresh confirmed.

### Major (Owner scoping required)

- [x] **Full test-suite + pipeline re-verification after the manuscript migration:**
      Completed 2026-09-26. Root-caused the residual migration drift: five test
      fixture helpers (`test_publication.py`, `test_release_bundle.py`,
      `test_experiment_config.py`, `test_experiment_config_surface.py`,
      `test_scripts_smoke.py`) still wrote `manuscript/config.yaml` after src/
      loaders moved to `docs/manuscript/config.yaml`, so fail-closed config
      surface tests exercised defaults instead of fixtures (11 failures);
      `scripts/00_preflight.py` still passed the legacy path to the template
      preflight (masked by the standalone guard). All fixed; pipeline
      regenerated (analysis 2400 rows / tamper 1.0, conformance 8/8, figure QA
      ok, release bundle rebuilt); full suite green at 90.69% coverage with
      only the clean-tree promotion gate pending the commit; ruff + mypy clean.
      Removed stray tracked `TODO.md.bak`.  
  - **Acceptance criteria:** Full test suite passes with 0 failures on the
    migrated codebase.  
  - **Note:** PDF/HTML render validation remains template-checkout dependent
    (not part of this gate); see `docs/rendering_pipeline.md`.

## Round 2 TODO Completion (2026-08-31)

All actionable items completed:
- ✅ **Minor/Medium items:** Already complete per agent-ergonomics pass
- ✅ **Artifact regeneration:** Fresh artifacts generated and verified
- ✅ **Full test-suite verification:** Completed 2026-09-26 (see agent-ergonomics pass, Major section)
- 📋 **Owner-scoped items:** KMS/HSM design work properly scoped with acceptance criteria

**Implementation status:** All automatable work complete. Remaining items require owner architectural decisions (KMS/HSM interface design) or infrastructure work (drive optimization, template pipeline setup).

## Maintenance Rule

Before each release-candidate render, review this file and either close,
promote, rewrite, or explicitly defer each item that has become stale.
