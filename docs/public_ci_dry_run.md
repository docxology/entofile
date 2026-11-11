# Public CI Dry-Run Map

This document maps release-candidate commands to the non-publishing
`docxology/entofile` GitHub Actions gates. It is intentionally non-publishing:
the workflow should prove that the public repository can rebuild and validate
the release surfaces, but it must not upload packages, create releases, sign
artifacts, or mutate Zenodo.

## Non-Publishing Contract

- Run on pull requests, pushes to `main`, explicit manual dispatches, and a weekly
  scheduled regression check (see `.github/workflows/ci.yml`).
- Use read-only repository permissions by default.
- Upload temporary CI artifacts only when needed for review; do not publish
  release assets.
- Treat live endpoint checks as reporting gates until the public repository,
  DOI, and Zenodo record are intentionally promoted.
- Keep signing commands documented but disabled unless a release operator
  explicitly runs the public release workflow.

## Local Command to CI Stage Map

| Local command | CI stage | Purpose | Publish side effect |
| --- | --- | --- | --- |
| `uv run python scripts/run_tests.py` | `test` | Certify live project tests and coverage from source, writing the structured sidecar. | None |
| `uv run ruff check src/ tests/ scripts/` | `lint` | Lint gate. | None |
| `uv run --extra dev mypy src/` | `lint` | Type gate — MUST use the dev extra so stub packages (`types-PyYAML`, `types-jsonschema`) are installed; a stub-less invocation errors out early and silently shrinks the checked surface (this hid 13 real errors until 2026-06-10). | None |
| `./run.sh no-mocks` | `test` | Fail on prohibited mock usage or scanner errors; preserve the no-mock evidence boundary. | None |
| `uv run python scripts/ento_analysis.py` | `analysis` | Regenerate benchmark and validation reports. | None |
| `uv run python scripts/export_sbom.py` | `supply-chain` | Generate the CycloneDX SBOM surface for review. | None |
| `uv run python scripts/generate_conformance_fixtures.py` | `conformance` | Rebuild deterministic known-good and known-bad fixtures. | None |
| `uv run python scripts/verify_conformance_fixtures.py` | `conformance` | Verify fixture acceptance and rejection semantics. | None |
| `uv run python scripts/check_figure_layout.py` | `figures` | Check rendered figure text/layout metadata. | None |
| `uv run python scripts/z_generate_manuscript_variables.py` | `docs/manuscript` | Refresh manuscript injection variables from generated evidence. | None |
| `uv run python scripts/audit_publication_readiness.py --check` | `publication-readiness` | Run the certifying private/local readiness oracle. | None |
| `uv run python scripts/build_release_bundle.py` | `release-bundle-dry-run` | Build checksum and manifest surfaces for inspection. | None |
| `uv run python scripts/check_public_promotion_metadata.py --check` | `public-metadata` | Verify local public-facing metadata consistency. | None |
| `uv run python scripts/check_public_promotion_metadata.py --check --require-public-endpoints --live-public-endpoints` | `public-endpoints` | Confirm promoted endpoints resolve after publication. | None in dry run; expected to block before promotion. |

## Executable workflow

`.github/workflows/ci.yml` is the executable source of truth, with immutable action
and SDK pins and a single Python 3.15 consumer cell. It renders genuine PDF/HTML,
runs the complete test suite, then rehydrates measured values and certifies live
tests in the SDK environment. The complete current-output snapshot and stage 04
validation precede the final outer `release/` envelope and checksum verification.
No template-render-dependent test is excluded. See
[`rendering_pipeline.md`](rendering_pipeline.md) for the matching local sequence;
do not use an abbreviated example that tests before generating its prerequisites.

Pull-request updates cancel only superseded runs for the same pull request.
Maintainers can also dispatch the workflow manually. A weekly Monday 09:17 UTC run
checks the locked source against fresh hosted-image, Python-patch, and native-package state.
On success, the minimal generated release evidence is retained for seven days for
endpoint verification. On failure, explicitly listed public reports, rendered
deliverables, and release metadata are retained from both the project and pinned SDK
clone as temporary CI diagnostics for the same period; neither is a release asset.

The live endpoint command runs only through the separately dispatched
[`public-endpoints` workflow](../.github/workflows/public-endpoints.yml); it never
runs on push or pull request. Dispatch it with the numeric ID of a successful CI run
so it can download that run's release evidence, then confirm the promoted public home,
DOI, and Zenodo record resolve. Artifact signing also stays outside this dry run; see
[`provenance_signing.md`](provenance_signing.md).
