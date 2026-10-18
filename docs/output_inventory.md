# Output Inventory — entofile

Producer → consumer graph for pipeline artifacts.

| Artifact | Producer | Consumer |
| --- | --- | --- |
| `ento_benchmark_results.csv` | `scripts/ento_analysis.py` → `src/analysis.py` | `manuscript_variables.py`, figures, validation |
| `benchmark_validation.json` | `src/benchmarks.py` (analysis stage) | `src/analysis.py::validate_generated_outputs`; tamper rate must be `1.0` |
| `validation_report.json` | SDK pipeline stage 04 | PDF/manuscript validation; evidence registry |
| `conformance_report.json` | `scripts/verify_conformance_fixtures.py` → `src/conformance.py` | Known-good/known-bad conformance acceptance report |
| `artifact_manifest.json` | Intermediate: `src/artifact_manifest.py`; final: SDK `scripts/maintenance/refresh_artifact_manifests.py` | Complete current rendered-output snapshot checked by SDK stage 04 |
| `release/release_manifest.json` (project root) | `scripts/build_release_bundle.py` → `src/release_bundle.py` | Outer release checksum inventory for external signing; outside `output/` to avoid cyclic hashes |
| `output/figures/*.png` | `src/figure_registry.py` + `src/figures.py` | Manuscript sections, PDF/HTML, figure-layout QA |
| `output/figures/figure_registry.json` | `src/figure_registry.py::write_figure_registry` | Output gates, manuscript variables, visual evidence contract; includes `generated_by`, caption token, filters, `takeaway`, `evidence`, and `caution` |
| `manuscript_variables.json` | `z_generate_manuscript_variables.py` | PDF injection |
| `output/manuscript/*.md` | infrastructure injection | `scripts/pipeline/stage_03_render.py` |
| `data/claim_ledger.yaml` | committed | `tests/test_claim_ledger.py` |
| `docs/evidence_provenance.md` | committed | `tests/test_evidence_provenance.py`; reader-facing input/output claim boundary |

See [`output_conventions.md`](output_conventions.md) for paths.
