# Rendering Pipeline — entofile

Four phases from analysis to PDF. Phases 1-2 run standalone; Phases 3-4
use the **template repository** for rendering infrastructure.

## Template repository

The template repository at `github.com/docxology/template` provides the
rendering infrastructure (`infrastructure/rendering/`) that converts
manuscript markdown into publication-ready PDF, HTML, slides, and DOCX.

In the `hum-docxology` managed layout, the template lives at:

```
projects/platform/hum-docxology/repos/public/template/
```

To render entofile from the template checkout:

```bash
cd projects/platform/hum-docxology/repos/public/template

# Symlink entofile into the template's working projects (one-time):
ln -sf /path/to/entofile projects/working/entofile

# Render PDF + HTML (uses the template's pandoc + xelatex pipeline):
uv run python scripts/03_render_pdf.py --project working/entofile --skip-manuscript-hydration
```

The `--skip-manuscript-hydration` flag is used because the standalone
analysis pipeline already generates `output/data/manuscript_variables.json`
(see Phase 2 below). Without this flag, the template attempts to run
entofile's `z_generate_manuscript_variables.py` which requires the
template's `infrastructure.rendering.manuscript_injection` module —
creating a circular dependency. The standalone path avoids this.

## Phase 1 — Analysis (standalone)

```bash
cd /path/to/entofile
uv run python scripts/ento_analysis.py
```

Writes CSV, figures, container verification, artifact manifest, SBOM,
manuscript variables, figure layout report, and validation report.

## Phase 2 — Variable hydration (standalone)

```bash
cd /path/to/entofile
# Already done by ento_analysis.py, but can be run separately:
uv run python scripts/generate_manuscript_variables_standalone.py
```

Writes `output/data/manuscript_variables.json`. The template-based
`z_generate_manuscript_variables.py` also resolves `{{TOKEN}}` injection
and writes the substituted manuscript tree, but requires the template
infrastructure.

## Phase 3 — Prerender validation (template checkout)

```bash
cd /path/to/template
uv run python -m infrastructure.validation.cli prerender projects/working/entofile/manuscript --repo-root .
```

## Phase 4 — PDF render (template checkout)

```bash
cd /path/to/template
uv run python scripts/03_render_pdf.py --project working/entofile --skip-manuscript-hydration
```

Reads `manuscript/config.yaml`, `references.bib`, substituted markdown,
and figure paths under `output/figures/`. The project config enables the
template's transmission-bookend renderer
(`publication.transmission_bookends.enabled: true`), so the combined PDF
uses the template-managed `BEGINNING OF TRANSMISSION` page, cover/title
page, table of contents, manuscript body, bibliography, and final
`END OF TRANSMISSION` page in that order.

Outputs:
- `output/pdf/entofile_combined.pdf`
- `output/web/index.html` (+ per-section HTML files)

## Full standalone pipeline (no template required)

```bash
cd /path/to/entofile
uv run python scripts/ento_analysis.py
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
uv run python scripts/build_release_bundle.py
```

This generates all release artifacts except `output/pdf/` and
`output/web/` (which require the template rendering pipeline).

## Troubleshooting

- **Unresolved `{{TOKEN}}`**: re-run variable script; check
  `tests/test_manuscript_variables.py`.
- **Missing figures**: run analysis first.
- **LaTeX errors** (`cleveref.sty not found`, `natbib` missing): install
  with `tlmgr --usermode install cleveref natbib seqsplit`.
- **Mermaid errors** (`mmdc failed`): install Chrome headless with
  `npx puppeteer browsers install chrome-headless-shell`.
- **Bib errors**: from template root, `uv run python -m
  infrastructure.reference.citation.cli validate
  projects/working/entofile/manuscript/references.bib --strict`
- **Transmission page overflow**: run `uv run python
  scripts/04_validate_output.py --project working/entofile` from the
  template root.
