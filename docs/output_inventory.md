# Output Inventory — entofile

Producer → consumer graph for pipeline artifacts.

| Artifact | Producer | Consumer |
| --- | --- | --- |
| `ento_benchmark_results.csv` | `scripts/ento_analysis.py` → `src/analysis.py` | `manuscript_variables.py`, figures, validation |
| `benchmark_validation.json` | `src/benchmarks.py` (analysis stage) | `src/analysis.py::validate_generated_outputs`; tamper rate must be `1.0` |
| `validation_report.json` | Pipeline Stage 6 | PDF/manuscript validation; evidence registry |
| `conformance_report.json` | `scripts/verify_conformance_fixtures.py` → `src/conformance.py` | Known-good/known-bad conformance acceptance report |
| `artifact_manifest.json` | `src/artifact_manifest.py` | Standalone output-tree declaration for validation |
| `release_manifest.json` | `scripts/build_release_bundle.py` → `src/release_bundle.py` | Local release checksum inventory for external signing |
| `output/figures/*.png` | `src/figure_registry.py` + `src/figures.py` | Manuscript sections, PDF/HTML, figure-layout QA |
| `output/figures/figure_registry.json` | `src/figure_registry.py::write_figure_registry` | Output gates, manuscript variables, visual evidence contract; includes `generated_by`, caption token, filters, `takeaway`, `evidence`, and `caution` |
| `manuscript_variables.json` | `z_generate_manuscript_variables.py` | PDF injection |
| `output/manuscript/*.md` | infrastructure injection | `03_render_pdf.py` |
| `data/claim_ledger.yaml` | committed | `tests/test_claim_ledger.py` |
| `docs/evidence_provenance.md` | committed | `tests/test_evidence_provenance.py`; reader-facing input/output claim boundary |

See [`output_conventions.md`](output_conventions.md) for paths.
