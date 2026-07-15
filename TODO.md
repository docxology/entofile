# TODO — ENTO Upcoming Improvements

This roadmap tracks post-0.4 release-candidate work. It is intentionally scoped
as a backlog, not a promise: each item should become a test-backed issue or PR
before implementation. Preserve the current interface unless an item explicitly
calls for a breaking release:

- Default write format is `0.4.0`.
- Compatibility formats `0.2.0`, `0.3.0`, and `0.3.1` remain readable/writable.
- Paper/manuscript release label `0.4` is distinct from ENTO wire-format string `0.4.0`.

## Current cycle — 2026-07-15

- Finish the current shared-boundary hardening batch, review every local hunk, and
  land implementation/tests separately from ledger updates on main.
- Regenerate every certifying artifact from the final head. A local readiness pass
  is not an external public-promotion pass.
- Keep the canonical gate sequence and evidence rules in
  [ISA.md](ISA.md#current-cycle--2026-07-15) and the pipeline instructions.
- Execute research only through the preregistered protocol in
  [experiment_plan.yaml](experiment_plan.yaml) and
  [docs/research/agenda.md](docs/research/agenda.md).

## Minor Updates

- Keep figure captions compact after dense benchmark refreshes; prefer injected
  tokens for row counts, figure counts, SBOM status, and benchmark scale.
- Periodically re-run public/private wording checks before promotion using the
  metadata checker so the private working checkout is never described as already
  public.

## Completed in TODO pass

- Added operator, glossary, format-migration, provenance/signing, release-note,
  and public-release checklist documentation.
- Added design notes for KMS/HSM custody, post-quantum signing/key wrapping,
  streaming pack/unpack constraints, and manifest extension policy.
- Added `--json-output` result sidecars and `--telemetry-jsonl` local telemetry
  events for all CLI subcommands without changing default human output.
- Added deterministic conformance fixture generation for `0.2.0`, `0.3.0`,
  `0.3.1`, `0.4.0`, ciphertext tamper, duplicate ZIP member, and path escape cases.
- Added optional benchmark knobs for a larger synthetic track and mixed
  multi-track container while keeping the default 0.4 row count unchanged.
- Added figure artifact QA for registered PNG presence, dimensions, and
  nonblank rendering.
- Added a conformance verifier that checks generated vectors and writes
  `output/reports/conformance_report.json`.
- Added a release manifest/checksum builder for `output/release/` so the PDF,
  HTML, SBOM, artifact manifest, conformance report, manuscript variables, and
  root release metadata can be signed externally.
- Added public-cutover scaffolding: `LICENSE`, `CITATION.cff`, `SECURITY.md`,
  `CONTRIBUTING.md`, and GitHub issue templates.
- Added renderer-aware figure layout QA for registered figures and a script that
  writes `output/reports/figure_layout_report.json`.
- Added `configs/benchmark_expanded.yaml` plus an isolated benchmark-profile
  runner for large-track and mixed-container stress evidence.
- Added a machine-readable public-promotion metadata checker comparing
  manuscript config, `pyproject.toml`, `CITATION.cff`, README, and release
  manifest fields.
- Promoted default `.ento` wire format to `0.4.0` and added compatibility,
  length-leakage, conformance, observability-redaction, and release-evidence
  figures.
- Added `docs/public_ci_dry_run.md` mapping each local release command to its
  future non-publishing GitHub Actions job, plus `.github/CODEOWNERS`.
- 2026-06-10 deep-review pass: fail-closed negative-control crafting (craft
  failures no longer count as a fired control), schema-rejection handling in
  the verification report, SBOM version-of-record from manuscript config via
  tested `src/sbom.py`, Python 3.10 `tomllib` compatibility, reproducible mypy
  gate (`[tool.mypy]` + stub deps), tightened exception-message test oracles,
  and stale 0.2.0-default wording fixes in `REVIEW.md`/`entofile.md`.
- 2026-07-10 lint cleanup pass: 120 ruff errors fixed (import sorting, ambiguous
  unicode, raw string patterns, iterable unpacking), mypy Python 3.10 compat
  (`datetime.UTC` -> `timezone.utc`), `[tool.ruff]` config added, `run.sh`
  convenience script, GitHub Actions CI workflow, `.pre-commit-config.yaml`,
  `.github/dependabot.yml`, pyproject.toml version promoted to `0.4.0`.
- 2026-07-10 standalone pipeline pass: SBOM, manuscript variables, figure layout
  report, and validation report now generated as part of `ento_analysis.py`
  (no template checkout required). Added `generate_manuscript_variables_standalone.py`.
  Added package build smoke tests. Documented template rendering integration in
  `docs/rendering_pipeline.md`. All 13 public-promotion tests pass. Release
  manifest `ok: true` with zero missing required files.
- 2026-07-14 deep red-team pass: export-level confidentiality escalation rejected;
  PADMÉ decoding canonicalized; project-root schema cache and public manifest parsing
  hardened; malformed config/report inputs fail closed; conformance verifier binds its
  complete case matrix plus fixture hashes; CI now covers scripts, figure QA, release
  bundling, package installation, and has a timeout. Template discovery now supports
  the documented public sibling checkout layout and the full render/validation path
  passes with 43-page transmission bookends.
- 2026-07-15 current-cycle pass: shared ProjectPaths, structured-data boundaries,
  fail-closed test-result parsing, exported domain errors with ConfigError
  compatibility, and the preregistered research agenda were added and covered by
  focused tests. Final full-gate and main parity evidence belongs in ISA.md after
  the landing commit.

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
- Prepare the final public `docxology/entofile` repository cutover by reviewing
  license ownership, citation metadata, release artifacts, conformance fixtures,
  security disclosure, and repository settings immediately before promotion.

## Research agenda

The backlog is machine-readable in `experiment_plan.yaml` and explained in
`docs/research/agenda.md`. Its current questions are:

- RQ-1: independent-language vectors and schema negotiation.
- RQ-2: bounded-memory streaming pack/unpack with verify-before-release.
- RQ-3: observability and metadata leakage across formats and levels.
- RQ-4: cryptographic interoperability, nonce discipline, and canonical padding.
- RQ-5: KMS/HSM custody, rotation, recovery, and audit boundaries.
- RQ-6: signed release manifests, SBOMs, provenance, and reproducible builds.
- RQ-7: exports to related research-container ecosystems without equivalence claims.

Every question requires three competing hypotheses, a control or baseline, exact
metrics, a repetition rationale, falsification criteria, and a stopping rule.
Results remain bounded by the protocol and cannot certify an external ecosystem
or public endpoint without independent evidence.

## Maintenance Rule

Before each release-candidate render, review this file and either close,
promote, rewrite, or explicitly defer each item that has become stale.
