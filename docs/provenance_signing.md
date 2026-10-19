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

1. Follow [the complete rendering pipeline](rendering_pipeline.md) in order:
   independent evidence (including conformance), actual render, complete tests,
   measured-value hydration, live audit, full inventory snapshot, SDK validation,
   and the outer release envelope. Do not regenerate conformance or any other
   inner producer after final hashing without repeating finalization.
2. Verify the finalized checksum surface from the project root:

   ```bash
   sha256sum --check release/SHA256SUMS
   ```

3. Confirm local metadata and live endpoint state:

   ```bash
   uv run python scripts/check_public_promotion_metadata.py --check
   uv run python scripts/check_public_promotion_metadata.py --check --require-public-endpoints --live-public-endpoints
   ```

4. Confirm the release manifest was rebuilt from a project-clean checkout:
   `source_dirty_project` and the legacy `source_dirty` compatibility field
   must both be `false`.
5. With an operator-approved signing identity and installed signing tool, sign
   both the checksum list and the release manifest. The checksum list binds
   artifact bytes; the separate manifest binds the source revision and release
   metadata. Signing only the list does not authenticate those manifest fields.
   The identity-based Cosign bundle flow is:

   ```bash
   cosign sign-blob --yes release/SHA256SUMS \
     --bundle release/SHA256SUMS.sigstore.json
   cosign sign-blob --yes release/release_manifest.json \
     --bundle release/release_manifest.json.sigstore.json
   ```

6. Emit SLSA-compatible and/or in-toto-style provenance in CI for the build and
   render job.
7. Verify both bundles against the approved identity/issuer, not permissive
   identity regexes. Set `SIGNING_IDENTITY` and `OIDC_ISSUER` through the approved
   operator policy, then run:

   ```bash
   : "${SIGNING_IDENTITY:?set approved certificate identity}"
   : "${OIDC_ISSUER:?set approved OIDC issuer}"
   for artifact in release/SHA256SUMS release/release_manifest.json; do
     cosign verify-blob "$artifact" --bundle "$artifact.sigstore.json" \
       --certificate-identity "$SIGNING_IDENTITY" \
       --certificate-oidc-issuer "$OIDC_ISSUER"
   done
   ```

8. Attach the PDF, HTML, SBOM, artifact manifest, conformance report, release
   manifest, checksums, signatures, and provenance to the public release.

These examples follow the official Sigstore [blob-signing documentation](https://docs.sigstore.dev/cosign/signing/signing_with_blobs/)
and [signature-verification documentation](https://docs.sigstore.dev/cosign/verifying/verify/),
checked on 2026-10-19. Validate the selected tool version and organizational
identity/issuer policy before execution. This repository does not install or
authorize a signer. The local metadata tool's `release_ready` flag does not execute
signing, verification, upload, pairing, or attestation; record external evidence
separately rather than inferring it from endpoint reachability.

## Residual Controls

Key custody, release signing policy, transparency-log monitoring, vulnerability
triage, and SIEM routing remain deployment responsibilities. Master-key custody,
cryptoperiods, escrow, and rotation are governed outside the `.ento` file format
[@nistsp80057pt1r5].
