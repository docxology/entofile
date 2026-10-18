# Rendering Pipeline — entofile

The complete publication gate requires real PDF, HTML, transmission metadata,
hydrated manuscript, analysis, tests, and a complete output inventory. A standalone
variables JSON is not manuscript hydration. Never skip hydration for certification.
See [publication validation](publication_validation_2026_10_18.md) for dated evidence.

## Pinned template SDK

Use the template commit pinned in `.github/workflows/ci.yml`:
`4670c48cc490636455f2eac09ba4396baed9ffd7`. Its locked environment requires
Python 3.14; entofile supports Python 3.10+. Install Pandoc and compatible
pandoc-crossref, XeLaTeX, BibTeX, fonts, and Poppler as in CI. CI pins its
converters separately; a different local converter version is not identical CI parity.

Prepare a **physical clone**, not a symlink, at
`<template-checkout>/projects/working/entofile`. Hydration discovers the SDK from
the project's physical parents. Keep its origin set to the public entofile repository
so immutable source-document links name the consumer rather than the SDK pool.
Synchronize the exact source revision and all relevant changes before generation.

```bash
cd <template-checkout>
uv sync --locked --python 3.14
```

Use a real Git-backed SDK checkout with the exact pinned source indexed. An
archive export can render when `SOURCE_DATE_EPOCH` is set to the SDK commit's
timestamp (`1792325058` here), but cannot certify stage-source provenance without
the genuine Git index. Do not invent timestamps or bypass provenance checks.

## 1. Generate independent evidence

From the physical entofile clone (use its locked development environment):

```bash
uv run python scripts/ento_analysis.py
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
uv run python scripts/check_figure_layout.py
uv run python scripts/build_dashboard.py
uv run python scripts/generate_api_docs.py
uv run python scripts/export_sbom.py
```

Analysis writes an intentionally analysis-scoped artifact manifest. That is useful
intermediate evidence, **not** the final full-render integrity snapshot.

## 2. Render, establish tests, then hydrate measured values

From the template root:

```bash
uv run --locked --python 3.14 python scripts/pipeline/stage_03_render.py --project working/entofile
```

The renderer runs `z_generate_manuscript_variables.py`, substitutes tokens, and
produces `output/pdf/entofile_combined.pdf`, `output/web/index.html`, and
`output/data/transmission_manifest.json`. The combined PDF has beginning/end
transmission bookends (`BEGINNING OF TRANSMISSION` and `END OF TRANSMISSION`);
title content may share the first page. Inspect the actual
render rather than assuming a separate cover-page number.

From entofile, bootstrap the outer envelope and run **all** tests:

```bash
uv run python scripts/build_release_bundle.py
uv run python scripts/run_tests.py
```

Now rerun stage 03 from the template root. This second hydration binds measured
coverage from `output/reports/test_results.json`; an initial `N/A` coverage token
does not qualify as publication evidence. If environments/checkouts differ, copy
the genuine test report back before rerendering, as CI does.

## 3. Certify and finalize the inner output tree

From the template root, using its environment so live evidence validation is available:

```bash
uv run --locked --python 3.14 python projects/working/entofile/scripts/audit_publication_readiness.py --check
uv run --locked --python 3.14 python scripts/maintenance/refresh_artifact_manifests.py --project working/entofile
uv run --locked --python 3.14 python scripts/pipeline/stage_04_validate.py --project working/entofile
```

The certifying audit reruns live tests, coverage, conformance, container checks,
and manuscript evidence checks. `--no-live-tests` is diagnostic only and cannot
be combined with `--check`. The supported maintenance operation snapshots the
complete current output inventory using the SDK-authorized working-project mode;
it is labelled `current-output-snapshot`, not fabricated stage provenance.
Stage 04 validates the real PDF/HTML/manuscript, registry, inventory, and digests,
and writes validation and rendered-provenance reports. Preserve every failure.

## 4. Build the outer release envelope last

From entofile:

```bash
uv run python scripts/build_release_bundle.py
sha256sum --check release/SHA256SUMS
uv run python scripts/check_public_promotion_metadata.py --check
uv run python scripts/check_public_promotion_metadata.py --check --require-public-endpoints --live-public-endpoints
```

The envelope is `release/release_manifest.json` and `release/SHA256SUMS`, outside
`output/`. Otherwise the full inner artifact inventory and the outer checksum list
would hash each other cyclically. Legacy `output/release/release_manifest.json`
remains readable only when no current envelope exists. Move old generated envelopes
to evidence storage outside `output/` before taking a complete new snapshot.

Do not regenerate analysis, tests, variables, or renders after final hashing without
repeating snapshot, validation, and envelope generation. Building the outer envelope
must leave the inner output bytes untouched. A clean committed source and live
endpoints are separate requirements from local audit success. Endpoint reachability
does not prove the new PDF was uploaded, paired, signed, or externally attested;
follow [the publication checklist](publication_checklist.md) and
[signing recipe](provenance_signing.md) before claiming an actual public release.

## Troubleshooting

- **Unresolved or `N/A` tokens:** establish the real test report, then hydrate and render again.
- **Missing figures:** regenerate analysis before rendering.
- **Incomplete manifest:** use the supported maintenance snapshot after all inner producers finish.
- **LaTeX/BibTeX errors:** install the native dependencies listed in CI; never substitute placeholder PDFs.
- **Transmission validation:** run `scripts/pipeline/stage_04_validate.py`; inspect the first and last pages visually.
