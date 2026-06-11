# Publication readiness — entofile 0.4 paper release candidate

Manuscript release **0.4** documents ENTO container format **0.4.0**
(AES-256-GCM with AAD and PADMÉ padding) as the default on-disk contract, with
supported compatibility formats **0.2.0**, **0.3.0**, and **0.3.1**. Gate before
Zenodo update or public promotion.
Planned public home after readiness is `https://github.com/docxology/entofile`;
until promotion, the source and render path remain `projects/working/entofile`.

## Automated gate

From the project root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run python scripts/ento_analysis.py
uv run python scripts/build_dashboard.py
uv run python scripts/generate_api_docs.py
uv run python scripts/export_sbom.py
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/audit_publication_readiness.py --check
uv run python scripts/build_release_bundle.py
uv run python scripts/check_public_promotion_metadata.py --check
uv run python scripts/check_public_promotion_metadata.py --check --require-public-endpoints --live-public-endpoints
```

Render/validate through the sibling template:

```bash
cd <template-checkout>
uv run python scripts/03_render_pdf.py --project working/entofile
uv run python scripts/04_validate_output.py --project working/entofile
```

## Blockers

| Check | Evidence |
| --- | --- |
| Tests | live `pytest` via `audit_publication_readiness.py --check`; no trusted stale side file |
| Coverage | >= 90% on `src/` |
| Analysis outputs | `validate_generated_outputs()` — tamper rate, figures, registry, container verify |
| Container verification | `output/reports/container_verification.json` — substantive sample set and negative control |
| Crypto vectors | `data/test_vectors/*.json` exercised by crypto vector tests |
| Figure captions | `tests/test_figure_captions.py`; registry `caption_token` parity |
| Combined PDF | `output/pdf/*_combined.pdf` with real `%PDF-` header and non-trivial size |
| Variables | `output/data/manuscript_variables.json` without unresolved or sentinel metric tokens |
| Artifact manifest | `output/reports/artifact_manifest.json` declares actual working-project outputs |
| Public metadata | `check_public_promotion_metadata.py --check` reports local `ok: true` |
| Public endpoints | `check_public_promotion_metadata.py --check --require-public-endpoints --live-public-endpoints` reports `release_ready: true` |
| Clean source | `release_manifest.json` has `source_dirty_project: false` after final commit/clean rebuild |

`output/reports/test_results.json` is retained as pipeline context only. It may
summarize a broader template run; do not use it to certify the ENTO 0.4 RC.
The certifying test oracle is the live subprocess invoked by
`audit_publication_readiness.py --check`.

## Warnings

| Item | Action |
| --- | --- |
| SBOM / signing | `scripts/export_sbom.py` writes a CycloneDX SBOM; external release signing remains required |
| SLSA provenance | External CI/release system should emit provenance; not implemented by standalone project |
| Opt-in LLM stages | Disabled in config |

## RedTeam summary

See `docs/redteam_publish_0.4.md` for 0.4 RC findings and remediations. The
previous `docs/redteam_publish_1.0.md` remains historical evidence only.

## Version semantics

| Label | Value | Meaning |
| --- | --- | --- |
| Manuscript `paper.version` | 0.4 | This PDF/manuscript release candidate |
| ENTO `format_version` default write | 0.4.0 | Current on-disk container spec (AES-256-GCM, AAD, PADMÉ) |
| ENTO supported compatibility formats | 0.2.0, 0.3.0, 0.3.1 | Legacy baseline, AAD-bound, and padded predecessor profiles |
| Python package `version` | 0.1.0 | PyPI-style project version, unchanged for this paper RC |
