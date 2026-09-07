# scripts/ AGENTS.md

Scripts coordinate I/O only. Business logic lives in `src/`. Stage 02 discovers
`ento_analysis.py` and `build_dashboard.py` automatically. All other scripts are
explicit operator commands:

- `00_preflight.py` — render-prerequisite check
- `z_generate_manuscript_variables.py` — `{{TOKEN}}` hydration
- `generate_manuscript_variables_standalone.py` — variables JSON only, no template hydration
- `ento_cli.py` — pack / unpack / verify / inspect wrapper
- `generate_conformance_fixtures.py` / `verify_conformance_fixtures.py`
- `check_figure_layout.py`
- `generate_api_docs.py`
- `run_benchmark_profile.py`
- `audit_publication_readiness.py` — publication readiness gate
- `build_release_bundle.py`
- `export_sbom.py`
- `check_public_promotion_metadata.py`
- `run_tests.py` — canonical test gate, writes `output/reports/test_results.json`

See `README.md` in this directory for the per-script delegation table.
