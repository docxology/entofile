# Output Conventions — entofile

Project-root `output/` is disposable; regenerate via analysis scripts.

## Layout

| Path | Contents |
| --- | --- |
| `figures/*.png` | Benchmark plots (300 DPI) |
| `data/ento_benchmark_results.csv` | Primary metrics |
| `data/manuscript_variables.json` | Token map |
| `data/_bench_tmp/` | Ephemeral benchmark containers |
| `conformance/` | Generated known-good/bad fixture containers and manifest |
| `reports/benchmark_validation.json` | Tamper rate gate (analysis) |
| `reports/conformance_report.json` | Fixture accept/reject report |
| `reports/figure_layout_report.json` | Renderer-aware figure text clipping/overlap QA |
| `reports/validation_report.json` | SDK stage 04 output validation |
| `reports/test_results.json` | Pipeline test summary side file; contextual only, not the certifying publication oracle |
| `benchmark_profiles/expanded/` | Optional non-release stress benchmark output |
| `manuscript/*.md` | Token-resolved copies |
| `pdf/` | Combined PDF after render |

Rendered deliverables remain under project-root `output/` for the standalone
`working/entofile` RC.

The outer envelope is **project-root** `release/release_manifest.json` and
`release/SHA256SUMS`, not `output/release/`. Rebuilding it must not alter inner
output bytes; a full inventory and an envelope cannot hash each other cyclically.
Both generated trees are ignored by Git.

## Regeneration

```bash
uv run python scripts/ento_analysis.py
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
uv run python scripts/check_figure_layout.py
```

Then follow [`rendering_pipeline.md`](rendering_pipeline.md): actual render,
bootstrap envelope, complete tests, measured-value rehydration, live audit,
complete SDK snapshot/validation, and final outer envelope. The standalone
commands above are only the independent evidence preparation, not certification.

Use `uv run python scripts/check_public_promotion_metadata.py --check
--require-public-endpoints --live-public-endpoints` only for the final public
promotion check; local release-candidate regeneration is allowed to pass the
deterministic metadata gate while public endpoints are still pending.

The optional expanded benchmark profile is separate from the 0.4 release matrix:

```bash
uv run python scripts/run_benchmark_profile.py \
  --config configs/benchmark_expanded.yaml
```

Do not commit `output/` contents.

Publication certification must not trust `reports/test_results.json` by itself.
Use `uv run python scripts/audit_publication_readiness.py --check`, which
re-runs the project test suite live and treats stale side files as non-binding.
