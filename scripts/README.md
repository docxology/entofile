# scripts/ — thin orchestrators

Scripts coordinate I/O only; business logic lives in `src/` (tested). Pipeline
Stage 02 discovers `ento_analysis.py` and `build_dashboard.py` automatically;
everything else is an explicit operator command.

## Pipeline-discovered

| Script | Delegates to | Purpose |
| --- | --- | --- |
| `ento_analysis.py` | `src.analysis.main` | Benchmarks, figures, validation reports |
| `build_dashboard.py` | `src.dashboard.run_dashboard_build` | Dashboard HTML |

The reproducible test gate is explicit and writes the contextual
`output/reports/test_results.json` sidecar used by manuscript variable generation:

```bash
uv run python scripts/run_tests.py
```

## Manuscript / rendering

| Script | Delegates to | Purpose |
| --- | --- | --- |
| `00_preflight.py` | `src.experiment_config`, env checks | Render-prerequisite check |
| `z_generate_manuscript_variables.py` | `src.manuscript_variables.generate_variables` | Hydrate `{{TOKEN}}` variables |
| `check_figure_layout.py` | `src.figure_qa` | Renderer-aware figure text-layout QA |
| `generate_api_docs.py` | `src.documentation` | API documentation |

## CLI

| Script | Delegates to | Purpose |
| --- | --- | --- |
| `ento_cli.py` | `src.cli.main` | pack / unpack / verify / inspect |

## Conformance / benchmarks

| Script | Delegates to | Purpose |
| --- | --- | --- |
| `generate_conformance_fixtures.py` | `src.conformance` | Deterministic fixtures (0.2.0–0.4.0 + tamper cases) |
| `verify_conformance_fixtures.py` | `src.conformance` | Verify fixtures, write `conformance_report.json` |
| `run_benchmark_profile.py` | `src.benchmark_profiles` | Non-default benchmark profiles (isolated outputs) |

## Release / publication

| Script | Delegates to | Purpose |
| --- | --- | --- |
| `audit_publication_readiness.py` | `src.publication.check_publication_readiness` | Publication readiness gate (`--check` is certifying) |
| `build_release_bundle.py` | `src.release_bundle` | Release manifest + checksum list for `output/release/` |
| `export_sbom.py` | `src.sbom.build_cyclonedx_skeleton` | CycloneDX SBOM (optional release gate) |
| `check_public_promotion_metadata.py` | `src.public_promotion` | Public-promotion metadata consistency |

## Research source of truth

The machine-readable research protocol is [`../experiment_plan.yaml`](../experiment_plan.yaml), and its human-readable agenda is [`../docs/research/agenda.md`](../docs/research/agenda.md). Research changes must preserve the preregistration contract: three competing hypotheses per question, a control or baseline, exact metrics, falsification criteria, sample-size or repetition rationale, stopping rules, and explicit limits on interpretation.
