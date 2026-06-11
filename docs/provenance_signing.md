# Provenance and Signing Recipe

This repository exports a CycloneDX SBOM and artifact manifest, but it does not
perform release signing itself. A public release pipeline should bind the source
revision, manuscript artifacts, SBOM, and checksums with an external signing and
provenance system aligned with NIST supply-chain-risk guidance, SLSA/Sigstore,
and in-toto-style attestations [@nist2022sp800161r1; @slsa2024levels;
@sigstore2026cosign; @torresarias2019intoto].

## Release Inputs

- Git commit SHA and clean worktree assertion.
- `output/pdf/entofile_combined.pdf`.
- `output/web/index.html`.
- `output/reports/sbom.cyclonedx.json`.
- `output/reports/artifact_manifest.json`.
- `output/reports/conformance_report.json`.
- `output/data/ento_benchmark_results.csv`.
- `output/data/manuscript_variables.json`.
- `output/conformance/conformance_manifest.json`.

## Recommended Flow

1. Run the full test and render gate from the project root and template root.
2. Generate and verify the deterministic conformance fixtures:

   ```bash
   uv run python scripts/generate_conformance_fixtures.py
   uv run python scripts/verify_conformance_fixtures.py
   ```

3. Build the local release checksum surface:

   ```bash
   uv run python scripts/build_release_bundle.py
   uv run python scripts/check_public_promotion_metadata.py --check
   uv run python scripts/check_public_promotion_metadata.py --check --require-public-endpoints --live-public-endpoints
   ```

4. Confirm the release manifest was rebuilt from a project-clean checkout:
   `source_dirty_project` and the legacy `source_dirty` compatibility field
   must both be `false`.
5. Sign release artifacts with Sigstore Cosign or an equivalent signer:

   ```bash
   cosign sign-blob --yes output/release/SHA256SUMS \
     --output-signature output/release/SHA256SUMS.sig \
     --output-certificate output/release/SHA256SUMS.pem
   ```

6. Emit SLSA-compatible and/or in-toto-style provenance in CI for the build and
   render job.
7. Attach the PDF, HTML, SBOM, artifact manifest, conformance report, release
   manifest, checksums, signatures, and provenance to the public release.

## Residual Controls

Key custody, release signing policy, transparency-log monitoring, vulnerability
triage, and SIEM routing remain deployment responsibilities. Master-key custody,
cryptoperiods, escrow, and rotation are governed outside the `.ento` file format
[@nistsp80057pt1r5].
