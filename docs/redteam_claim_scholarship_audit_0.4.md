# RedTeam claim and scholarship audit -- ENTO 0.4 RC

Date: 2026-06-02. Target: `projects/working/entofile` paper release `0.4`
and default ENTO wire format `0.4.0`.

## Target classification

Structured artifact review:

- Q1: yes -- claims reside in manuscript sections, docs, claim ledger entries,
  generated reports, bibliography entries, and tests.
- Q2: yes -- defects can be cited by file path, manuscript section, citation key,
  report field, or test assertion.
- Q3: yes -- citation tests, evidence registry validation, claim-ledger tests,
  template citation prerender, publication readiness, and rendered-output checks
  are oracles.

Execution mode: internal RedTeam VectorSpecialists panel. Perplexity was used as
the requested discovery lane, but `llm -m sonar ...` returned
`401 insufficient_quota`; final scholarship additions were therefore verified
directly from primary, official, or peer-reviewed sources rather than accepted
from a Perplexity summary.

## Verifier-first oracle review

| Oracle | What it checks | False-certification gap attacked | Status after this pass |
| --- | --- | --- | --- |
| Citation scholarship tests | Required bibliography keys, DOI/URL metadata, manuscript citation coverage, no false JCS claim | A citation can resolve but still be too weak or uncited in renderable text | Strengthened with reproducibility, key-management, supply-chain, and nonce-misuse-resistance keys |
| Evidence provenance tests | No-mock boundary, fixture/synthetic/conformance labels, generated-output classes | "No mocks" could be laundered into "all real-world data" | Strengthened with Perplexity-failure and direct-source provenance wording |
| Claim ledger tests | Numeric/version/security claims tied to code or output artifacts | Hard-coded prose could drift from `src/crypto.py`, figure registry, or reports | Existing oracle remains relevant; no new volatile metric was introduced |
| Template citation prerender | Undefined citations and render-blocking pitfalls | Citation syntax can pass while scholarship is underspecified | Still required after edits |
| Publication readiness | Live project gates, PDF existence, variables, evidence registry, DOI | A green audit can miss scholarship quality | Paired with this claim-level RedTeam pass |

## Claim vectors reviewed

| Vector | Claim surface | Scholarship/source boundary | RedTeam verdict |
| --- | --- | --- | --- |
| Wire-format and release labels | Paper `0.4`, default `format_version` `0.4.0`, compatibility formats | Bound to `src/crypto.py`, schema enum, manuscript tokens, conformance fixtures | Clean: code-bound and tokenized |
| AEAD, AAD, and GCM | AES-256-GCM, associated data, tag failure, nonce uniqueness | NIST FIPS 197, RFC 5116, SP 800-38D, McGrew/Viega, Joux, Bock et al. | Clean after adding AES-GCM-SIV as a future alternative only |
| Key derivation and custody | HKDF per-track keys, master key outside ZIP, no in-repo HSM/KMS | RFC 5869, FIPS 180-4, NIST SP 800-57 | Clean: implementation and custody boundary are separated |
| Proof and JSON hashing | Hash chain, exact emitted manifest JSON bytes, no JCS interoperability claim | Merkle, Haber-Stornetta, PROV-DM/PROV-O, RFC 8785 | Clean: proof is consistency evidence, not origin authentication |
| ZIP/path threats | Hostile archive ingestion, path traversal, data amplification, duplicate members | PKWARE APPNOTE, CWE-22, CWE-409 | Clean: threat classes are cited and repo tests exercise concrete controls |
| Evidence provenance | No mocks, deterministic fixtures, synthetic throughput track, conformance vectors | Repo evidence contract plus reproducible-computing scholarship | Clean after adding Sandve et al., Wilson et al., and ACM artifact-badging boundary |
| Statistics and benchmarks | 150 repetitions, 2400 rows, local timing dispersion, deterministic fingerprint | Code-derived variables, benchmark reports, figure registry | Clean: timing is bounded to local run; deterministic metrics are fingerprinted |
| Supply chain and signing | SBOM/checksum manifest, external signatures/provenance, planned public release | NIST SP 800-161, SLSA, Sigstore, in-toto, COSE | Clean: external controls are not described as implemented in-repo |
| Preservation positioning | OAIS, PREMIS, FAIR repository boundary | CCSDS OAIS and Library of Congress PREMIS | Clean after adding preservation-system boundary to abstract, introduction, related work, limitations, and research notes |
| Related formats | RO-Crate, BagIt, Frictionless, HDF5, Zarr, EPUB/MKV, OpenTDF | Primary specs and peer-reviewed RO-Crate paper | Clean: ENTO is positioned as an encrypted track envelope, not a repository, preservation metadata standard, or DRM system |

## Findings closed in this pass

| ID | Finding | Risk | Fix |
| --- | --- | --- | --- |
| RT-CLAIM-001 | Reproducibility prose had strong repo-local evidence but thin external scholarship | A reviewer could see "reproducible" as an unsupported term of art | Added PLOS reproducible-computing citations and ACM artifact-review boundary |
| RT-CLAIM-002 | Key-custody language named HSM/KMS as residual but lacked a key-management primary source | The manuscript could sound like operational key management is an informal aside | Added NIST SP 800-57 citations to manuscript and security docs |
| RT-CLAIM-003 | Supply-chain provenance was documented but under-specified outside SLSA/Sigstore | Local checksum manifest could be overread as complete release provenance | Added NIST SP 800-161 and in-toto scholarship to manuscript and release docs |
| RT-CLAIM-004 | GCM nonce-misuse discussion lacked a named future design alternative | Readers could infer the current format is the only relevant AEAD path | Added RFC 8452 as a future-format candidate and explicitly stated it is not implemented |
| RT-CLAIM-005 | Perplexity was requested but unavailable | Scholarship could appear to rely on an unrecorded failed discovery lane | Recorded the 401 quota failure and grounded final claims in direct sources |
| RT-CLAIM-006 | Follow-up found stale default-format wording outside the manuscript body | A public reader could treat 0.2.0 as current release guidance despite the 0.4.0 manuscript | Updated public/historical surfaces and added stale-phrase/public-promotion tests |
| RT-CLAIM-007 | Related work cited RO-Crate/BagIt/FAIR but did not explicitly name preservation-system standards | Reviewers could ask whether ENTO claims archive/repository responsibilities it does not implement | Added OAIS/PREMIS citations and an explicit layer boundary: ENTO is a file envelope, not archive operations or preservation metadata |

No unresolved critical manuscript-claim findings remain in this pass. Release
readiness remains separate: public endpoints, clean committed release metadata,
external signing/provenance, KMS/HSM policy, and independent conformance
implementations are not completed by local manuscript edits.

## Negative controls added

- Required new scholarship keys must exist in `manuscript/references.bib`.
- Each new load-bearing key must be cited in renderable manuscript body text.
- The manuscript must not imply AES-GCM-SIV is implemented.
- The evidence-provenance document must record the Perplexity quota failure and
  the direct-source fallback.
- Preservation-system scholarship must cite OAIS and PREMIS in renderable
  manuscript text and distinguish file-format claims from archive operations.
- The new claim-scholarship audit must be indexed and included in the release
  checksum manifest.
