# Publication ledger — entofile 0.4 paper release candidate

**Date:** 2026-06-10 (initial ledger 2026-05-30)  
**Manuscript version:** 0.4  
**Default format version:** 0.4.0 (AES-256-GCM, 12-byte nonce, format+track AAD, PADMÉ padding)  
**Supported compatibility formats:** 0.2.0, 0.3.0, and 0.3.1

## DOI status

| Field | Value |
| --- | --- |
| `publication.doi` | [10.5281/zenodo.20396329](https://doi.org/10.5281/zenodo.20396329) |

## Release scope

The 0.4 release candidate is a manuscript/paper release that ALSO promotes the
default `.ento` wire format to `0.4.0` (paper label `0.4` and wire format string
`0.4.0` are distinct identifiers). Formats `0.2.0`, `0.3.0`, and `0.3.1` remain
readable and writable compatibility profiles. The RC further improves the paper,
security documentation, figure set, release gates, and standalone
working-project render path.

The planned public repository is `https://github.com/docxology/entofile`; this
ledger still treats the private `projects/working/entofile` working tree as the
current source and render tree until promotion.

## Required gate results

| Gate | Evidence |
| --- | --- |
| Project tests | `uv run pytest tests/ --cov=src --cov-fail-under=90 -q` |
| No mocks | `grep -r "unittest.mock\\|MagicMock\\|@patch" tests/` |
| Analysis outputs | `uv run python scripts/ento_analysis.py` |
| Dashboard/API/SBOM | `build_dashboard.py`, `generate_api_docs.py`, `export_sbom.py` |
| Manuscript variables | `z_generate_manuscript_variables.py` and no unresolved tokens in `output/manuscript/` |
| Render | template `scripts/03_render_pdf.py --project working/entofile` |
| Output validation | template `scripts/04_validate_output.py --project working/entofile` |
| Publication audit | `uv run python scripts/audit_publication_readiness.py --check` |

## 0.4 RC hardening highlights

- 2026-06-11 (Round 20, PUBLICATION): the 0.4 release is published. Reserve-DOI-first
  on Zenodo — the existing draft (a leftover with the wrong artifact attached and bare
  metadata) was cleaned up (correct manuscript PDF + source archive, full title,
  version 0.4, MIT, keywords, abstract), its blocking community review request was
  cancelled, and it was published. Version DOI `10.5281/zenodo.20396329` and concept
  DOI `10.5281/zenodo.20396328` now resolve. Consumer docs flipped from
  pre-publication "planned public home" framing to the live present tense (README +
  docs/README + docs/faq + docs/agent_instructions), and the promotion checker +
  documentation-consistency test now enforce the published state. Public repository
  created and pushed.

- 2026-06-10 (Round 19, Forge re-verify of R17/R18 fixes): Forge (GPT-5.4)
  re-reproduced all three fixes and confirmed them VERIFIED (F1 leak-scanner,
  F2 conformance oracle, the standalone-clone guards), and validated the scope
  decision to leave portable home references unflagged. It found two LOW residual
  bypasses in the F1 scanner, both now closed: RESIDUAL-1 — the self-allowlist
  test only checked filenames, so a real leak hiding inside an allowlisted
  scanner file would pass; now pinned by a SHA-256 signature of the exact regex
  matches in those two files (a hex digest carries no path literal, so it does
  not perturb the matched set the way a literal allowlist would). RESIDUAL-2 —
  a path carried as literal ASCII in a mostly-binary tracked file was swallowed
  by the utf-8 decode skip; the scan now falls back to latin-1 so embedded ASCII
  paths are still caught, with a binary-fixture negative control. 397 tests /
  92.5%+, ruff + mypy clean.

- 2026-06-10 (Round 18, breadth RedTeam — docs/CLI/repo first-impression):
  DOC-1 — `scripts/z_generate_manuscript_variables.py` (listed in the README and
  quickstart quick-start) hard-imported template infrastructure, so a fresh
  public cloner running the documented command crashed; guarded like
  `00_preflight.py` (clear message + exit 2) and the quick-start now separates
  standalone commands from the template-integrated step. Added a README `uv`
  prerequisite line; the CLI `prog` is now `python -m src.cli` to match the
  documented invocation. Made the README DOI line honest: `10.5281/zenodo.20396329`
  is reserved and does not resolve until the deposit is published (the live
  endpoint check confirms the GitHub repo, Zenodo record, and DOI all 404 today —
  minting/publishing is the top release-gate action, tracked by the promotion
  checker's `public_endpoint_state`). CLI robustness, figure provenance, and
  standard-file coverage reviewed clean (SECURITY/LICENSE/CITATION/CONTRIBUTING/
  CODEOWNERS present; CHANGELOG/CI/CoC are optional follow-ups). 396 tests /
  92.56%, ruff + mypy clean.

- 2026-06-10 (Round 17, cross-vendor Forge + FirstPrinciples): Forge (GPT-5.4)
  re-audited the security core and the R16 machine-path oracle. Crypto core,
  container, verification_report (R15 negative-control fix), security, padding,
  and proof reproduced CLEAN cross-vendor. Forge caught ENTO-XV-F1 (HIGH): the
  R16 leak scanner globbed only `*.md`/`docs/*.md`/`manuscript/*.md` and was
  blind to CITATION.cff, pyproject.toml, configs, .github, scripts, and depth-2
  docs — a planted home path in CITATION.cff passed the gate. Fixed by driving
  the scan off the full tracked set (`git ls-files`, output/ + self-referential
  scanner files excluded, binaries skipped) with an anti-laundering test proving
  the two allowlisted files are the only tracked matches. ENTO-XV-F2 (LOW):
  conformance `_ok_or_error` treated any non-dict as success; made strict per
  operation (dict-with-`ok` required for the verify axes, tuple still valid for
  unpack). FirstPrinciples flagged PUB-3: `scripts/00_preflight.py` hard-imported
  template infrastructure at module level, so a standalone public clone died
  with a raw ModuleNotFoundError; now guarded like its sibling render scripts and
  exits 2 with a clear message. 395 tests / 92.56%, ruff + mypy clean.

- 2026-06-10 (Round 16, publication-readiness RedTeam): removed all 16
  machine-specific absolute home-directory paths from tracked docs — they would
  have leaked the maintainer's filesystem layout and given public cloners
  unrunnable commands. Render/build commands now use a `<template-checkout>`
  placeholder and the working tree is referenced relatively. The promotion
  metadata checker previously passed `ok:true` with all 16 present, so the gap
  is closed at the oracle: `public_promotion.py` now scans `*.md`, `docs/*.md`,
  and `manuscript/*.md` for home-directory prefixes
  (`public_docs_no_machine_paths` check + `machine_path_hits`), with a
  negative-control test that injects one and asserts it fails. Untracked the
  generated `coverage_project.json` (231 KB) and gitignored it plus `htmlcov/`.
  391 tests / 92.54%, ruff + mypy clean.

- 2026-06-10 (Round 15): negative-control crafting now fails closed — a failure
  while building the tampered container can no longer be counted as a fired
  control (single-vendor-reviewed; cross-vendor GPT-5.4 retry staged, quota-blocked
  at review time). Reproducible mypy gate, SBOM version-of-record from manuscript
  config, CODEOWNERS handle fix, and stale 0.2.0-default wording closed at the
  promotion checker.

- Release readiness reports the manuscript version from `manuscript/config.yaml`
  instead of a hard-coded release label.
- RedTeam 0.4 ledger closes stale release labels, stale active paths, missing local
  pipeline command references, citation-key drift, artifact-manifest drift, duplicate
  ZIP setup warnings, and paper-vs-wire-format ambiguity.
- Nation-state roadmap now separates in-repo controls from external release/deployment
  controls such as Sigstore signing, HSM/KMS, SLSA provenance, and SIEM forwarding.
- Figure registry includes security-specific visuals for the format ladder and control
  matrix, plus the determinism-CV view that separates reproducible data columns from
  volatile timing columns.

## Commands

```bash
cd <entofile-checkout>
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run python scripts/ento_analysis.py
uv run python scripts/build_dashboard.py
uv run python scripts/generate_api_docs.py
uv run python scripts/export_sbom.py
uv run python scripts/z_generate_manuscript_variables.py

cd <template-checkout>
uv run python scripts/03_render_pdf.py --project working/entofile
uv run python scripts/04_validate_output.py --project working/entofile
```
