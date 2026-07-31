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

- Keep figure captions compact after dense benchmark refreshes; prefer injected
  tokens for row counts, figure counts, SBOM status, and benchmark scale.
- Periodically re-run public/private wording checks before promotion using the
  metadata checker so the private working checkout is never described as already
  public.
- Rebuild generated artifacts after each significant change set and before any
  release-candidate render.

## Medium Improvements

- Add stricter visual diffing for figure changes, using a fixed CSV and per-pixel
  tolerance windows for intentional style changes.
- Fix `test_wheel_installs_and_imports` on Python 3.14 (venv ensurepip SIGABRT —
  environment issue, not code issue).

## Large Initiatives

- Design a formal key-management profile for deployment environments: KMS/HSM
  custody, rotation, access logging, and recovery policy remain external today.
- Promote the local release manifest/checksum builder into public CI with
  Sigstore signing and SLSA-compatible provenance emission.
- Extend the conformance suite for independent implementations with additional
  language bindings, malformed JSON edge cases, schema-version negotiation, and
  cross-version decrypt/verify behavior.
- Evaluate streaming pack/unpack for large multimodal tracks without weakening
  verify-before-release semantics.
- Finalize public end-to-end CI dry-run documentation and automated
  promotion-gate verification.

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

## Maintenance Rule

Before each release-candidate render, review this file and either close,
promote, rewrite, or explicitly defer each item that has become stale.