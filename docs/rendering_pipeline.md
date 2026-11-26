# Rendering Pipeline — entofile

The complete publication gate requires real PDF, HTML, transmission metadata,
hydrated manuscript, analysis, tests, and a complete output inventory. A standalone
variables JSON is not manuscript hydration. Never skip hydration for certification.
See [publication validation](publication_validation_2026_10_18.md) for dated evidence.

## Pinned template SDK

Use Python 3.15, uv, Pandoc 3.14 with its matching pandoc-crossref release,
XeLaTeX, BibTeX, Latin Modern and DejaVu fonts, and Poppler. This walkthrough
uses the [documentation reference revision](https://github.com/docxology/template/tree/87704feae0a4490ef7dad9c931d268e8c30273c2).
The [CI workflow](../.github/workflows/ci.yml) records its own SDK and
converter pins for release verification.

Set `ENTO_CHECKOUT` to the absolute path of a clean entofile checkout, then
register a physical clone inside the runner so hydration can discover the SDK
from its parent directories. Keep the public entofile origin so source links
identify the right repository.

```sh
git clone https://github.com/docxology/template.git ento-template-runner
cd ento-template-runner
git checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
uv sync --locked --python 3.15
mkdir -p projects/working
git clone --no-hardlinks "$ENTO_CHECKOUT" projects/working/entofile
git -C projects/working/entofile checkout --detach "$(git -C "$ENTO_CHECKOUT" rev-parse HEAD)"
git -C projects/working/entofile remote set-url origin https://github.com/docxology/entofile.git
cd projects/working/entofile
uv sync --locked --extra dev
```

The SDK uses its Git index to attest the renderer source.

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
uv run --no-sync --locked --python 3.15 python scripts/pipeline/stage_03_render.py --project working/entofile
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
uv run --no-sync --locked --python 3.15 python projects/working/entofile/scripts/audit_publication_readiness.py --check
uv run --no-sync --locked --python 3.15 python scripts/maintenance/refresh_artifact_manifests.py --project working/entofile
uv run --no-sync --locked --python 3.15 python scripts/pipeline/stage_04_validate.py --project working/entofile
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

The envelope is always `release/release_manifest.json` and
`release/SHA256SUMS`, outside `output/`. Otherwise the full inner artifact
inventory and the outer checksum list would hash each other cyclically. No
`output/release/` fallback is read. Move old generated envelopes to evidence
storage outside `output/` before taking a complete new snapshot.

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
- **Slow full analysis:** use a deliberate larger bound such as `scripts/run_tests.py --timeout 2400` and `audit_publication_readiness.py --check --live-test-timeout 2400`; never remove the timeout or skip live tests.
