# REVIEW LOG — 2026-08-31 (agent-ergonomics fleet pass, agent: entofile)

## PHASE 0 — PREFLIGHT
- Branch `main`, remote `origin` (github.com/docxology/entofile), ahead 2 at start.
- Pre-existing dirty state: 45 entries — a mid-flight `manuscript/` -> `docs/manuscript/`
  migration (16 `manuscript/` deletions, `docs/manuscript/` untracked, plus modified
  docs/ISA/REVIEW/SECURITY/config/data files). None of these were touched or reverted;
  the migration was completed forward (see Phase 1/3), which the dirty state was clearly
  mid-way through.

## PHASE 1 — COLD-START AUDIT
Entry doc: README.md. Orientation tasks attempted as a cold agent:
- (a) current status: PASS — README states format 0.5.0 with DOI; REVIEW.md has a
  superseded-marker pointing at the 0.5 ledger.
- (b) what next: PASS — README links TODO.md, which has clear Minor/Medium/Major lists.
- (c) primary verification: PASS — README quick start gives `uv run python scripts/run_tests.py`.

Sweep findings (link checker: 164 relative links across README/AGENTS/TODO/entofile.md/docs/**):
1. MAJOR->fixed: 37 broken relative links from the incomplete manuscript migration.
2. MAJOR->fixed: tests + src still read deleted `manuscript/` — FileNotFoundError on
   documentation/sbom/manuscript-variable suites.
3. MINOR->fixed: MANUSCRIPT_STATUS.md misdescribed the legacy location as `docs/manuscript/`.
4. Confirmed NON-issues: docs/figure_registry.md `name.png` is an intentional syntax
   example; `docs/reviews/` is local-only per its own README; REVIEW.md is a properly
   superseded historical ledger (kept by accretion doctrine).

## PHASE 2 — SCOPE
All findings scoped into TODO.md new "Agent-ergonomics pass (2026-08-31)" section,
Minor/Medium/Major, with Major items deferred with reasons.

## PHASE 3 — IMPLEMENT (all Minor + Medium)
- Fixed 37 broken relative links (docs/*.md `../manuscript/` -> `manuscript/`;
  docs/manuscript/*.md depth fixes `../docs/`->`../`, `../output/`->`../../output/`).
- Updated manuscript-dir paths to `docs/manuscript/` in:
  src/{analysis,manuscript_variables,publication,release_bundle,sbom,public_promotion,
  paths,experiment_config}.py and tests/{conftest,documentation_consistency,
  evidence_provenance,manuscript_variables,sbom,citation_scholarship,figure_captions,
  figure_crossrefs,manuscript_no_literal_metrics,manuscript_statistics_honesty,
  public_promotion,test_equation_crossrefs}.py.
- Corrected docs/manuscript/MANUSCRIPT_STATUS.md legacy-location wording.
- Re-ran link checker: 0 broken of 164.

## PHASE 4 — VERIFY & CLOSE
- Affected test suites re-run (see result line appended below).
- Link checker re-run: clean.
- Fast gate: no <2min declared gate; repo gate is `scripts/run_tests.py` (full suite,
  drive-bound) — not run in full; affected suites only. Recorded honestly.
