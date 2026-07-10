# TODO — ENTO Upcoming Improvements

This roadmap tracks post-0.4 release-candidate work. It is intentionally scoped
as a backlog, not a promise: each item should become a test-backed issue or PR
before implementation. Preserve the current interface unless an item explicitly
calls for a breaking release:

- Default write format is `0.4.0`.
- Compatibility formats `0.2.0`, `0.3.0`, and `0.3.1` remain readable/writable.
- Paper/manuscript release label `0.4` is distinct from ENTO wire-format string `0.4.0`.

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

## Maintenance Rule

Before each release-candidate render, review this file and either close,
promote, rewrite, or explicitly defer each item that has become stale.
