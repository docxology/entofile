# Rendering Pipeline — entofile

Four phases from analysis to PDF.

## Phase 1 — Analysis

```bash
uv run python scripts/ento_analysis.py
```

Writes CSV, figures, validation report.

## Phase 2 — Variable hydration

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

Writes `output/data/manuscript_variables.json` and substituted `output/manuscript/*.md`.

## Phase 3 — Prerender validation

```bash
cd <template-checkout>
uv run python -m infrastructure.validation.cli prerender projects/working/entofile/manuscript --repo-root .
```

## Phase 4 — PDF render

```bash
cd <template-checkout>
uv run python scripts/03_render_pdf.py --project working/entofile
```

Reads `manuscript/config.yaml`, `references.bib`, substituted markdown, and figure paths under `output/figures/`. The project config enables the template's transmission-bookend renderer (`publication.transmission_bookends.enabled: true`), so the combined PDF uses the template-managed `BEGINNING OF TRANSMISSION` page, cover/title page, table of contents, manuscript body, bibliography, and final `END OF TRANSMISSION` page in that order.

## Core pipeline shortcut

```bash
uv run python scripts/03_render_pdf.py --project working/entofile
```

## Troubleshooting

- Unresolved `{{TOKEN}}`: re-run variable script; check `tests/test_manuscript_variables.py`.
- Missing figures: run analysis first.
- Bib errors: from template root, `uv run python -m infrastructure.reference.citation.cli validate projects/working/entofile/manuscript/references.bib --strict`
- Transmission page overflow: run `uv run python scripts/04_validate_output.py --project working/entofile` from the template root; Stage 04 checks that BEGIN and END bookends each occupy a dedicated page.
