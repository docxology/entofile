# Publication validation — 2026-10-18

This continuation closes the historical three render-dependent promotion-test
exclusions; it does not assert an externally signed or published 0.5 release.
The [2026-10-16 maintenance review](maintenance_review_2026_10_16.md) describes
an earlier standalone run, not the current validation scope.

## Source and prerequisites

- Starting consumer main: `129807ac2e7248cea9d296cebb7eccdd5bcb9d48` (includes the earlier hardening work).
- Template SDK: `4670c48cc490636455f2eac09ba4396baed9ffd7`, the exact CI pin.
- Physical consumer clone under the pinned SDK; no changes to the separate active template checkout.
- SDK locked Python 3.14; consumer locked development tools on Python 3.13.
- Local Pandoc 3.12.1, pandoc-crossref 0.3.26, XeTeX/TeX Live 2026, BibTeX, and Poppler.
- SDK exported execution uses its real commit epoch, `SOURCE_DATE_EPOCH=1792325058`.
- CI converters are separately pinned; local converter versions do not establish identical CI parity.
- Concurrent GitVault bootstrap/repair was observed. Per-repository leases protected entofile work without interrupting other repositories.

## Findings and remediation

The initial real render produced a substantive 44-page PDF and HTML. All original
495 tests passed with 90.75% local coverage, including the three formerly excluded
promotion checks. Hosted CI for starting main also passed the complete 495-test
suite on Python 3.10, 3.12, and 3.14 (run `39128347203`).

Stricter SDK validation exposed incomplete final artifact inventory; analysis had
only attested its own intermediate outputs. A first render also had `N/A` coverage
because the canonical test report did not yet exist. Finally, placing the release
envelope inside `output/` made it hash the artifact manifest while that manifest
hashed the envelope, creating a cycle. The corrected pipeline:

1. Runs tests against actual rendered products, then hydrates/renders with measured coverage.
2. Certifies live tests and SDK evidence validation; forged green side files cannot certify.
3. Snapshots the complete inner output with the SDK's supported maintenance tool and validates it.
4. Writes the outer envelope under `release/`, preserving every inner output byte.

The release manifest reader retains fail-closed legacy compatibility. Current
envelopes take precedence even when malformed. Regression tests bind envelope
digests and verify rebuilding it does not modify inner output. Certifying `--check`
and diagnostic `--no-live-tests` are mutually exclusive; no gate was skipped.

## Validation record

The first updated-source canonical run passed **499 tests**, zero failures/errors,
with **90.82%** coverage. Ruff and mypy passed; the focused regression set passed
36 tests. These are executed results, not an assertion about a future hosted run.
The subsequent final-source candidate run passed **501 tests**, zero failures/errors,
with **90.77%** coverage. The live certifying audit in the locked SDK environment
returned `ok: true`, `tests_source: live`, all checks true, no blockers, and no warnings.
The SDK maintenance snapshot attested **105 stable artifacts**; SDK stage 04
passed all checks, including full artifact inventory and rendered-provenance inputs.
The final outer envelope's **36 checksums** verified against their actual files.

An archive-export-only SDK initially failed provenance with
`STAGE_SOURCE_MISSING: no cached stage implementation files found`. The exact SDK
commit was fetched and its genuine Git index restored in the isolated SDK copy;
`git diff --exit-code HEAD` confirmed all SDK source bytes matched. No SDK source
was modified and no provenance gate was relaxed. All subsequent validation used
this Git-backed pinned source. CI already checks out the actual pinned Git tree.

Stage 04 retains seven noncritical `MARKDOWN.LINK_BAD_TEXT` warnings for existing
source-document link labels. PDF bookends validate at pages 1 and 44. Visual
inspection of title/body and end-transmission pages found no page overflow;
the end page accurately displays pending pairing. The metadata gate passed while
correctly recording uncommitted candidate-source readiness blockers. Final
clean-source rebuilds use the committed revision recorded in
`release/release_manifest.json`; artifact digests are the generated envelope's
authority, not a self-referential hash embedded in this source document.

The workflow now preserves this same post-test hydration, live audit, supported
snapshot, SDK validation, and final outer-checksum order. Structural regression
tests bind that ordering. A read-only independent review found no actionable
correctness/regression/gate-weakening findings. No future hosted run is inferred
from these local results.

## External publication boundary

## Clean-source follow-through

The full clean rebuild of committed source
`c4445e46c8c10b18ac61afe735da80410e9c400e` completed on 2026-10-18:
501 tests passed at 90.77% coverage, the live publication audit passed, and
the complete inventory contained **106 stable artifacts** after explicit dashboard
generation. All 36 release checksums verified. Independent post-envelope checks
confirmed that both inner inventory and current rendered provenance remained valid.
The clean source and rebuilt envelope had no dirty-source flags; the live endpoint
gate returned `release_ready: true` with no metadata/readiness blockers.

Retained inventory, provenance, and outer digests were rechecked successfully on
2026-10-19 before further edits. Manuscript follow-through corrects stale abbreviated
regeneration advice, clarifies that the interpreter token describes hydration,
and replaces non-informative source-link labels. CI now explicitly generates the
dashboard, API documentation, and SBOM before rendering, matching the documented
independent-evidence preparation. These are additional source changes, not a claim
that the earlier build already included them.

## External publication boundary

On 2026-10-18, live checks reached GitHub, Zenodo record `20396329`, and DOI
`10.5281/zenodo.20396329` with HTTP 200 (the DOI resolves to that record).
The observed GitHub release list contained `v0.4`, published 2026-06-11, not a 0.5
release. The generated transmission manifest explicitly remains `published: false`
with null release URL and PDF SHA-256/SHA-512 pairing. This is pending publication,
not a broken local renderer. A reachable DOI does not prove it contains the new PDF.

Actual 0.5 upload/deposit, externally authorized signing/key custody, transmission
pairing, and external provenance are outstanding. No release tag, uploaded asset,
signature, or attestation is fabricated by this work. Metadata/endpoint
`release_ready` is a narrower state than completion of those external steps.
