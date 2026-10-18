# Publication readiness — entofile 0.5 paper release candidate

Manuscript **0.5** documents default ENTO format **0.5.0** (AES-256-GCM,
manifest-context AAD, PADMÉ). Compatibility formats are **0.2.0**, **0.3.0**,
**0.3.1**, and **0.4.0**. Public source is `https://github.com/docxology/entofile`.
The physical SDK consumer is `projects/working/entofile`.

## Required generation and certification

Follow [rendering_pipeline.md](rendering_pipeline.md) in order:

1. Generate analysis, conformance, figure QA, dashboard, API docs, and SBOM.
2. Render actual PDF/HTML with hydration enabled using the pinned SDK.
3. Bootstrap the release envelope and run the complete canonical test gate.
4. Rehydrate/rerender with the measured test report, then run the live certifying audit.
5. Refresh the complete artifact snapshot and run SDK stage 04 validation.
6. Rebuild `release/` last and verify every checksum without modifying inner outputs.
7. From a clean committed source, run local metadata and live public-endpoint gates.

`scripts/run_tests.py` and `scripts/audit_publication_readiness.py --check` clear
pytest's cache. Timeouts terminate the process tree and fail closed. The canonical
test report, `output/reports/test_results.json`, is pipeline context; do not use it to certify
the release. The certifying audit reruns tests and coverage live.
Diagnostic side-file mode cannot be combined with `--check`.

## Required gates

| Check | Evidence |
| --- | --- |
| All tests | Live pytest, no exclusions or render-dependent skips |
| Coverage | At least 90% on `src/` |
| Analysis | Tamper rate, figure registry, and container checks |
| Conformance | Complete known-good/bad fixture matrix and live verification |
| PDF/HTML | Actual rendered reader artifacts, SDK validation and visual QA |
| Variables | Hydrated manuscript and JSON without unresolved/sentinel metrics |
| Evidence | Live manuscript evidence registry validation in the SDK environment |
| Artifact inventory | Complete current snapshot, valid digests and rendered provenance |
| Outer envelope | `release/release_manifest.json` and verified `release/SHA256SUMS` |
| Local metadata | `check_public_promotion_metadata.py --check` reports `ok: true` |
| Clean source | Final committed source and rebuilt manifest have `source_dirty_project: false` |
| Live endpoints | `--check --require-public-endpoints --live-public-endpoints` reports `release_ready: true` |

## External release boundary

Local audit success and the metadata tool's `release_ready` flag are **not** proof
of a signed, uploaded 0.5 release. Independently verify:

- Actual versioned GitHub release and Zenodo record contain the final reader artifacts.
- Published transmission pairing records the real release URL and PDF SHA-256/SHA-512.
- External signing binds checksums and source revision; key custody is authorized.
- External provenance/attestation is emitted and independently verifiable.

Never fabricate pairing, signatures, or provenance. A reachable existing DOI can
still refer to older bytes. See [dated validation evidence](publication_validation_2026_10_18.md)
for the observed boundary and [provenance_signing.md](provenance_signing.md) for
the signing procedure. Opt-in LLM stages remain disabled in project configuration.

## Version semantics

| Label | Value | Meaning |
| --- | --- | --- |
| Manuscript `paper.version` | 0.5 | Current paper release candidate |
| ENTO default write | 0.5.0 | Current authenticated-manifest format |
| Compatibility formats | 0.2.0, 0.3.0, 0.3.1, 0.4.0 | Explicit predecessor profiles |
| Python package | 0.5.0 | Current package release line |
