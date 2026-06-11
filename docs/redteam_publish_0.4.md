# RedTeam — entofile 0.4 paper release candidate (2026-05-30)

Workflow: internal RedTeam panel using the RedTeam doctrine plus NationStateSecurity
pillar review. Target: `projects/working/entofile` 0.4 paper release candidate.
Repo-wide verifier and visualization confirmation lives in
[`redteam_repo_visual_audit_0.4.md`](redteam_repo_visual_audit_0.4.md).
The claim-by-claim scholarship audit lives in
[`redteam_claim_scholarship_audit_0.4.md`](redteam_claim_scholarship_audit_0.4.md).

## Position tested

Initial passes treated 0.4 as a paper/manuscript release only. This pass changes
the tested position: paper release `0.4` now promotes default ENTO wire
`format_version` to `0.4.0`, while `0.2.0`, `0.3.0`, and `0.3.1` remain
version-dispatched compatibility formats.

## Findings and fixes

| ID | Finding | Risk | Fix in 0.4 RC |
| --- | --- | --- | --- |
| RT-04-001 | Stale release labels still said `1.0` in readiness gates and publication docs | A 0.4 artifact could certify itself under the wrong release line | Release is read from `manuscript/config.yaml`; docs/tests use 0.4 |
| RT-04-002 | Active-vs-working path drift in docs and claim ledger | Operators could run the wrong tree or validate stale artifacts | Commands now use project-root-relative paths and template `--project working/entofile` |
| RT-04-003 | Project docs referenced nonexistent local `scripts/execute_pipeline.py` | Reproduction instructions failed before analysis/render | Standalone commands use `scripts/ento_analysis.py`, hydration, and template renderer |
| RT-04-004 | Stale cite key `dworkin2001recommendation` survived in research notes | Citation validation could fail or route readers to a non-existent key | GCM references use `dworkin2007gcm` |
| RT-04-005 | Artifact-manifest validation failed for standalone working output | Release validation reported drift even after render | `src/artifact_manifest.py` writes a populated manifest for the actual project-root `output/` tree |
| RT-04-006 | Duplicate-ZIP tests intentionally wrote duplicate members but did not capture `zipfile` warnings | Warning-as-error runs surfaced expected test setup warnings as failed tests | Tests capture expected `UserWarning` while still asserting duplicate rejection |
| RT-04-007 | Earlier wire-format language conflated paper release `0.4` with ENTO `format_version` | Implementers might add an ambiguous `0.4` string or miss the semver wire-version boundary | Docs now state paper `0.4` and default wire `0.4.0`; `0.2.0`, `0.3.0`, and `0.3.1` are explicit compatibility profiles |
| RT-04-008 | PDF density depended on the template fallback `0.75in` margin | The 0.4 RC render could silently drift from the requested compact layout | Project-local `metadata.geometry: "margin=0.5in"` is the single source of truth |
| RT-04-009 | Public-destination language was absent or could be read as already public | Operators could publish docs that confuse the private working path with the future public repo | Docs say `https://github.com/docxology/entofile` is the planned public home, while `projects/working/entofile` remains current |
| RT-04-010 | Methods prose still said the registry had 14 figures after the security visuals landed | Figure-count claims could pass render while misleading readers | Methods no longer hard-codes the count; figure count is code-derived and ledger-tested |
| RT-04-011 | Architecture docs described the manifest enum as `0.2.0` only | A reader could reject valid `0.3.0`/`0.3.1`/`0.4.0` containers or think support is undocumented | Architecture docs list the supported enum and explain `0.4.0` is now default |
| RT-04-012 | Threat-model index stopped at TM-007 while top abuse paths included length disclosure | The length side channel could be omitted from review checklists | TM-008 now covers sealed plaintext-length disclosure and `0.3.1` mitigation |
| RT-04-013 | Reproducibility prose over-specified the audit script as rewriting benchmarks | A future audit implementation could become correct while the manuscript stayed false | Wording now binds variables after any live audit/test refresh without asserting a single rewrite mechanism |
| RT-04-014 | Nation-state matrix risked implying external release controls were implemented in-repo | A security reader could over-trust SBOM/signing/KMS posture | Roadmap splits repository-enforced, partial/documented, and external/residual controls |
| RT-04-015 | User intent changed from paper-only 0.4 to default `.ento` `0.4.0` | Existing prose and tests would falsely assert no wire-format migration | Crypto constants, schema enum, conformance fixtures, benchmark rows, docs, and manuscript prose now bind default `format_version` to `0.4.0` |
| RT-04-016 | Expansion figures still assumed unpadded `r(n)=1+H/n` | Default padding would make the visual/math claim false | Expansion model is version-aware and default prose uses `r(n)=(H+PADME(n+8))/n` |
| RT-04-017 | Figure set lacked compatibility, length-leakage, conformance, redaction, and release-evidence visuals | Readers could not audit the 0.4.0 migration from the manuscript alone | Added registered code-derived figures for those five surfaces and extended figure QA/caption tests |
| RT-04-018 | Load-bearing security claims cited specs but not the strongest primary scholarship | Reviewers could challenge AEAD/GCM, nonce-reuse, JSON digest, ZIP/path, and proof-chain claims as under-sourced | Added primary citations and manuscript guardrails for GCM analysis, AEAD, nonce misuse, SHA/AES, JCS, hash-chain lineage, CWE-409/CWE-22, COSE, RO-Crate, and Kaitai |
| RT-04-019 | Real-world-only wording could imply all benchmark inputs are observational datasets | The paper could overclaim by hiding deterministic fixtures, the synthetic throughput track, and conformance test vectors | Added `docs/evidence_provenance.md`, manuscript provenance tokens, and tests that separate no-mock execution from fixture/synthetic/test-vector input classes |
| RT-04-020 | Perplexity scholarship lane was requested but unavailable during this pass | A reader could infer uncited or tool-derived scholarship shaped the crypto prose | Recorded the 401 `insufficient_quota` result and grounded crypto prose in direct NIST, RFC, MITRE CWE, IACR/USENIX, and PURB sources |
| RT-04-021 | Reproducibility, artifact-review, key-custody, and supply-chain claims were bounded in prose but under-cited relative to crypto claims | A reviewer could treat those non-crypto claims as weaker than the implementation evidence | Added PLOS reproducible-computing, ACM artifact-badging, NIST SP 800-57, NIST SP 800-161, and in-toto citations with tests that require renderable manuscript use |
| RT-04-022 | GCM nonce-misuse text named the hazard but not a standards-track future alternative | Readers could miss that nonce-misuse-resistant AEAD is a format-design option, not an ENTO 0.4.0 property | Added RFC 8452 AES-GCM-SIV as a future-format candidate and test-guarded the non-implementation boundary |
| RT-04-023 | `SECURITY.md`, `ISA.md`, and format-0.3.0 test docs retained stale 0.2.0 default-language | Release readers could infer the current/default wire format was still 0.2.0 | Public wording now says paper 0.4 / default wire 0.4.0; 0.2.0/0.3.0/0.3.1 are compatibility formats, with negative-control tests |
| RT-04-024 | Release manifest `source_dirty` was polluted by unrelated sibling project dirtiness | A clean ENTO subtree could look dirty, or dirty-state semantics could be ambiguous | Release manifest now reports `source_dirty_project` and `source_dirty_repository`; legacy `source_dirty` is project-scoped |
| RT-04-025 | Draft transmission bookends embedded a stale prior PDF hash | A pending/unpublished artifact could falsely advertise a digest for a different render | Template bookends now leave draft PDF hashes pending and use a PDF digest only from a publication ledger |
| RT-04-026 | Planned public GitHub and Zenodo endpoints returned 404 in live checks | Local RC evidence could be mistaken for public availability | Public release remains blocked until endpoint checks succeed after authorized promotion |
| RT-04-027 | Related-work scholarship cited RO-Crate/BagIt/FAIR but did not name OAIS or PREMIS | Reviewers could read ENTO as claiming archival-repository or preservation-metadata responsibilities it does not implement | Added OAIS/PREMIS citations, a preservation layer boundary, and tests that require renderable manuscript coverage |
| RT-04-028 | `output/reports/test_results.json` can contain a template-wide side-file summary with failures unrelated to the project-scoped certifying gate | A stale side file could contradict or falsely certify release readiness | `audit_publication_readiness.py --check` re-runs project tests live; docs now mark `test_results.json` as contextual, not certifying |

## Convergence map

- **Repeated objection:** stale labels and paths create false assurance even when code is sound.
- **Repeated objection:** keyless verification and unsigned artifacts must be described as weaker than keyed authentication or signed release provenance.
- **Unique objection:** timing hashes must not be presented as reproducibility anchors; the data fingerprint must cover only deterministic columns.
- **First-principles objection:** ZIP visibility, key custody, AEAD AAD inputs, and wall-clock volatility are hard constraints; release labels, margin defaults, and public-repo wording are soft/documentation constraints that must be made explicit.
- **Evidence objection:** "no mocks" is an execution claim, not a claim that every input byte is field-collected or observational.

## Core deciding assumption

The release is both a paper/manuscript release candidate (`0.4`) and a default
wire-format migration (`0.4.0`). Compatibility is a read/write requirement for
older containers, not a promise that new default outputs keep the old version.

## Verification evidence required

- Focused tests for publication, RedTeam remediations, security hardening, format
  `0.3.0`/`0.3.1`/`0.4.0`, figures, captions, manuscript variables, claim ledger, and docs.
- Full project coverage gate at or above 90%.
- Fresh analysis, dashboard/API docs/SBOM, hydration, template render, output validation,
  and publication readiness audit.
- Final resolved manuscript tree with no unresolved `{{TOKEN}}` placeholders.
- Public-promotion metadata check with local `ok:true`; public `release_ready`
  must remain false until project-scoped release metadata is clean and
  GitHub/Zenodo/DOI endpoint checks resolve.

## Residuals

- Artifact signing, HSM/KMS, SLSA provenance, SIEM forwarding, and PQC transport are
  external deployment controls, not implemented by this offline reference repository.
- Default 0.4.0 hides exact plaintext length only to PADMÉ buckets. ZIP names, member
  presence, and padded bucket sizes remain visible.
- Public release signing, KMS/HSM custody, CI provenance, and SOC routing remain outside this
  offline reference repository until the planned `docxology/entofile` promotion adds release
  infrastructure.
- Live public endpoint checks currently remain the public-release blocker: the
  private/local RC can be reproduced from this tree, but the GitHub repository,
  Zenodo record, and DOI are not release evidence until they resolve.
