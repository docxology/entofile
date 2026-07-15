# Public CI Dry-Run Map

This document maps the private release-candidate commands to a future
`docxology/entofile` GitHub Actions dry run. It is intentionally non-publishing:
the workflow should prove that the public repository can rebuild and validate
the release surfaces, but it must not upload packages, create releases, sign
artifacts, or mutate Zenodo.

## Non-Publishing Contract

- Run on pull requests, pushes to protected release branches, and manual
  dispatch.
- Use read-only repository permissions by default.
- Upload temporary CI artifacts only when needed for review; do not publish
  release assets.
- Treat live endpoint checks as reporting gates until the public repository,
  DOI, and Zenodo record are intentionally promoted.
- Keep signing commands documented but disabled unless a release operator
  explicitly runs the public release workflow.

## Local Command to CI Job Map

| Local command | Future CI job | Purpose | Publish side effect |
| --- | --- | --- | --- |
| `uv run python scripts/run_tests.py` | `test` | Certify live project tests and coverage from source, writing the structured sidecar. | None |
| `uvx ruff check src/ tests/ scripts/` | `lint` | Lint gate. | None |
| `uv run --extra dev mypy src/` | `lint` | Type gate — MUST use the dev extra so stub packages (`types-PyYAML`, `types-jsonschema`) are installed; a stub-less invocation errors out early and silently shrinks the checked surface (this hid 13 real errors until 2026-06-10). | None |
| `grep -r "unittest.mock\\|MagicMock\\|@patch" tests/` | `test` | Preserve the no-mock evidence boundary. | None |
| `uv run python scripts/ento_analysis.py` | `analysis` | Regenerate benchmark and validation reports. | None |
| `uv run python scripts/export_sbom.py` | `supply-chain` | Generate the CycloneDX SBOM surface for review. | None |
| `uv run python scripts/generate_conformance_fixtures.py` | `conformance` | Rebuild deterministic known-good and known-bad fixtures. | None |
| `uv run python scripts/verify_conformance_fixtures.py` | `conformance` | Verify fixture acceptance and rejection semantics. | None |
| `uv run python scripts/check_figure_layout.py` | `figures` | Check rendered figure text/layout metadata. | None |
| `uv run python scripts/z_generate_manuscript_variables.py` | `manuscript` | Refresh manuscript injection variables from generated evidence. | None |
| `uv run python scripts/audit_publication_readiness.py --check` | `publication-readiness` | Run the certifying private/local readiness oracle. | None |
| `uv run python scripts/build_release_bundle.py` | `release-bundle-dry-run` | Build checksum and manifest surfaces for inspection. | None |
| `uv run python scripts/check_public_promotion_metadata.py --check` | `public-metadata` | Verify local public-facing metadata consistency. | None |
| `uv run python scripts/check_public_promotion_metadata.py --check --require-public-endpoints --live-public-endpoints` | `public-endpoints` | Confirm promoted endpoints resolve after publication. | None in dry run; expected to block before promotion. |

## Candidate Workflow Shape

```yaml
name: entofile dry run

on:
  pull_request:
  push:
    branches: ["main", "release/**"]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  release-dry-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv run python scripts/run_tests.py
      - run: grep -r "unittest.mock\\|MagicMock\\|@patch" tests/ || echo "Clean"
      - run: uv run python scripts/ento_analysis.py
      - run: uv run python scripts/export_sbom.py
      - run: uv run python scripts/generate_conformance_fixtures.py
      - run: uv run python scripts/verify_conformance_fixtures.py
      - run: uv run python scripts/check_figure_layout.py
      - run: uv run python scripts/z_generate_manuscript_variables.py
      - run: uv run python scripts/audit_publication_readiness.py --check
      - run: uv run python scripts/build_release_bundle.py
      - run: uv run python scripts/check_public_promotion_metadata.py --check
```

The live endpoint command remains a separate manual or protected job until the
public home, DOI, and Zenodo record are expected to resolve. Artifact signing
also stays outside this dry run; see [`provenance_signing.md`](provenance_signing.md).
