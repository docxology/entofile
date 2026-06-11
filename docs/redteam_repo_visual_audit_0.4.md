# RedTeam repo-wide and visualization audit -- ENTO 0.4 RC

Date: 2026-06-01. Target: `projects/working/entofile` paper release `0.4`
and default ENTO wire format `0.4.0`.

## Target classification

Structured artifact review:

- Q1: yes -- target resides in source files, docs, generated reports, rendered
  PDF/HTML, and figure images.
- Q2: yes -- defects can be cited as file paths, report fields, figure labels,
  PDF pages, or manuscript sections.
- Q3: yes -- tests, figure QA, template validation, citation prerender,
  conformance verification, release manifest, and publication readiness are
  oracles.

Execution mode: internal RedTeam VectorSpecialists panel. No external subagents
were used. The first target is the verifier layer; green reports are evidence,
not proof by themselves.

## Oracle status

| Oracle | Evidence inspected | False-certification attack | Verdict |
| --- | --- | --- | --- |
| Full tests and coverage | Final closeout uses live `audit_publication_readiness.py --check`, which re-runs project pytest and coverage rather than trusting `output/reports/test_results.json`; the latest live gate reports all tests passed and coverage above 90% | A broad suite can miss visual semantics and rendered-PDF readability | ORACLE-TRUSTWORTHY for code/regression behavior; paired with visual and render checks |
| No-mock hygiene | `grep -r "unittest.mock\\|MagicMock\\|@patch" tests/ || echo "Clean"` returned `Clean` | A suite could still use deterministic fixtures or generated vectors while claiming all-real-world inputs | ORACLE-TRUSTWORTHY for no mocks; bounded by `docs/evidence_provenance.md` |
| Figure layout QA | `output/reports/figure_layout_report.json` reports `ok: true`, `figure_count: 21`, `failed: []` | A nonblank, non-overlapping figure can still be uninformative or redundant | ORACLE-TRUSTWORTHY for clipping/overlap; manual informativeness review still required |
| Template validation | `output/reports/validation_report.json` and template `04_validate_output.py` passed PDF, bookends, markdown, structure, figure registry, evidence registry, overlays, and artifact manifest | Validation can pass if captions are technically valid but semantically weak | ORACLE-TRUSTWORTHY for render integrity; paired with per-figure rubric |
| Citation prerender | `infrastructure.validation.cli prerender ... --bib ...` found no undefined citations or render-blocking pitfalls | Citation resolution does not prove a citation is the strongest source | ORACLE-TRUSTWORTHY for undefined-citation prevention; scholarship quality remains manuscript-test and claim-audit guarded |
| Conformance verifier | `output/reports/conformance_report.json` reports 7 cases, 7 passed, 0 failed | Reference implementation could accept its own mistaken vectors | ORACLE-TRUSTWORTHY for current known-good/bad behavior; independent implementations remain future work |
| Release manifest | `output/release/release_manifest.json` reports `ok: true` | A checksum inventory can be correct while dirty-state semantics are polluted by unrelated sibling projects | REOPENED in 2026-06-02 follow-up; project-scoped and repository-scoped dirty fields are now required |
| Publication audit | `audit_publication_readiness.py --check` reports release `0.4`, format `0.4.0`, live tests, coverage, analysis outputs, combined PDF, evidence registry, manuscript variables, no blockers, and no warnings | Readiness can miss public endpoint state and release signing | ORACLE-TRUSTWORTHY for private/local RC readiness; public release still requires live endpoint and signing gates |

## Repo-wide vectors

| Vector | Materials reviewed | RedTeam verdict |
| --- | --- | --- |
| Crypto and security claims | `src/crypto.py`, `src/crypto_gcm.py`, `src/padding.py`, `docs/security.md`, `docs/entofile-threat-model.md`, manuscript security sections | Clean: default `0.4.0` is consistently described as 12-byte nonce, AAD binding, and PADME padding; compatibility formats are bounded |
| Data provenance | `docs/evidence_provenance.md`, `manuscript/05_experimental_setup.md`, `manuscript/06_reproducibility.md`, `tests/test_evidence_provenance.py` | Clean: no-mock execution is separated from fixture, synthetic stress, and conformance-vector inputs |
| Manuscript claims and citations | `manuscript/*.md`, `manuscript/references.bib`, citation scholarship tests, `docs/redteam_claim_scholarship_audit_0.4.md` | Clean: load-bearing crypto, ZIP/path, JSON digest, reproducibility, key custody, supply-chain, RO-Crate/PROV, and COSE claims have direct citation coverage |
| Docs and indexes | `README.md`, `docs/README.md`, `docs/claim_ledger.md`, `docs/output_inventory.md`, `docs/publication_checklist.md`, `SECURITY.md`, `ISA.md` | Reopened: follow-up found stale 0.2.0 default-language in public and historical surfaces; fixed with exact phrase gates |
| Generated outputs | `output/data/ento_benchmark_results.csv`, `output/reports/*.json`, `output/figures/*.png`, `output/pdf/entofile_combined.pdf`, `output/web/index.html` | Clean for private/local RC after regenerated validation; transmission PDF hashes remain pending while unpublished |
| Public promotion | `CITATION.cff`, `SECURITY.md`, `CONTRIBUTING.md`, `LICENSE`, `src/public_promotion.py`, `docs/public_release_checklist.md` | Local metadata is gateable, but public release is blocked until source is clean, endpoints resolve, and release provenance is externalized |

## 2026-06-02 follow-up findings

| ID | Finding | Risk | Fix |
| --- | --- | --- | --- |
| RT-VIS-001 | `SECURITY.md`, `ISA.md`, and a 0.3.0 test docstring retained present-tense 0.2.0 default-language | Public readers could infer 0.2.0 is still the current default format | Updated public wording and added exact stale-phrase tests |
| RT-VIS-002 | Draft transmission manifest carried a prior PDF hash | A regenerated PDF could certify a stale digest | Template bookends now keep draft hashes pending unless a publication ledger supplies them |
| RT-VIS-003 | Release manifest dirty state was repository-wide | Unrelated sibling projects could block or confuse ENTO release assessment | Release manifest now distinguishes project-scoped and repository-scoped dirty state |

## 2026-06-03 closeout findings

| ID | Finding | Risk | Fix |
| --- | --- | --- | --- |
| RT-VIS-004 | `output/reports/test_results.json` can describe a broader template run rather than the project-scoped certifying run | A stale or red side file could be mistaken for publication evidence | Publication certification now depends on live `audit_publication_readiness.py --check`; docs label `test_results.json` as non-certifying context |
| RT-VIS-005 | Public-promotion metadata can be locally correct while public endpoints still return 404 | A private RC could be described as publicly available too early | Public release gate requires `--require-public-endpoints --live-public-endpoints`; current public verdict remains blocked until GitHub, Zenodo, and DOI resolve |

## Figure informativeness rubric

Each figure must:

1. support a manuscript or release-evidence claim;
2. name source data, filter, and generator in its caption or registry metadata;
3. render readably in the PDF, not only as a standalone PNG;
4. pass nonblankness, minimum-size, clipping, and overlap checks;
5. avoid redundant low-value panels unless it is an overview figure pointing to
   higher-detail standalone figures;
6. distinguish implemented, partial, and external security controls where
   applicable.

## Visualization verdicts

| PDF figure | Registry label or file | Page | Role | Verdict |
| --- | --- | --- | --- | --- |
| 1 | `transmission_integrity_strip.png` | 1 | transmission evidence | Informative: binds QR/barcode strip to release metadata and artifact checks |
| 2 | `transmission_pairing.png` | 1 | transmission pairing | Informative: shows publication pairing flow without adding manuscript claims |
| 3 | `fig:manifest_multitrack` | 9 | methodology | Informative: compares manifest size across fixture tracks and observability levels |
| 4 | `fig:observability_redaction_matrix` | 9 | methodology | Informative: clarifies field-level redaction versus encrypted payload integrity |
| 5 | `fig:crypto_overhead` | 10 | methodology | Informative: separates fixed AEAD header from PADME-padded ciphertext body |
| 6 | `fig:tamper_detection` | 15 | security | Informative: directly supports the 2400/2400 tamper-detection claim |
| 7 | `fig:format_ladder` | 15 | security | Informative: makes the 0.4.0 default and compatibility ladder visible |
| 8 | `fig:format_compatibility_matrix` | 16 | security | Informative: distinguishes read/write/default/AAD/PADME properties by format |
| 9 | `fig:length_leakage_profile` | 17 | security | Informative: shows exact-length leakage versus PADME bucket leakage |
| 10 | `fig:conformance_outcomes` | 17 | security | Informative: shows known-good and known-bad fixture outcomes |
| 11 | `fig:security_control_matrix` | 18 | security | Informative: separates implemented, partial, and external controls without overclaiming |
| 12 | `fig:benchmark_overview` | 20 | results | Informative as a navigation panel; standalone figures carry detail |
| 13 | `fig:throughput_benchmark` | 21 | results | Informative: communicates local timing sample and avoids superiority claims |
| 14 | `fig:expansion_ratio` | 22 | results | Informative: shows exact fixture expansion values |
| 15 | `fig:expansion_heatmap` | 22 | results | Informative: shows fixture versus synthetic track overhead at a glance |
| 16 | `fig:observability_manifest_size` | 23 | results | Informative: supports manifest-size redaction tradeoff |
| 17 | `fig:unpack_latency` | 25 | benchmark interpretation | Informative: compares pack/unpack latency with labels; layout QA now covers label clipping |
| 18 | `fig:throughput_by_observability` | 26 | benchmark interpretation | Informative: shows observability metadata has no obvious throughput penalty in this local run |
| 19 | `fig:observability_throughput_tradeoff` | 27 | benchmark interpretation | Informative: connects manifest bytes to throughput dispersion |
| 20 | `fig:expansion_law` | 27 | benchmark interpretation | Informative: overlays measured ratios on the version-aware expansion identity |
| 21 | `fig:throughput_dispersion` | 28 | benchmark interpretation | Informative: shows 150-repetition timing dispersion with mean and 95% CI |
| 22 | `fig:determinism_cv` | 29 | benchmark interpretation | Informative: separates deterministic zero-CV metrics from timing metrics |
| 23 | `fig:release_evidence_map` | 34 | reproducibility | Informative: maps benchmark, visual, conformance, SBOM, checksum, and PDF/HTML evidence |
| 24 | `transmission_integrity_strip.png` | 42 | transmission evidence | Informative: closes the START/END transmission pairing |

All registered manuscript figures are claim-bearing, source-connected, and
readable in the rendered PDF sample. The two transmission strip instances and
the pairing flow are not registered manuscript figures, but they are intentional
template-generated transmission evidence.

## Residuals

- Figure QA detects clipping/overlap and nonblankness, not the semantic strength
  of a figure; this document provides the manual semantic review.
- The release manifest is a local checksum inventory; external Sigstore/Cosign,
  SLSA provenance, CI attestation, and HSM/KMS controls remain outside the
  standalone repository.
- Conformance fixtures are deterministic reference vectors. Independent
  implementation conformance remains future work.
