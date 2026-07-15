# src/ AGENTS.md

Technical reference for ENTO domain modules. Security: [`../docs/security.md`](../docs/security.md).

## Module map

| Module | Public API |
| --- | --- |
| `crypto.py` | `FORMAT_VERSION`, `NONCE_SIZE`, `TAG_SIZE`, `encrypt_payload`, `decrypt_payload`, `crypto_backend_for_format` |
| `errors.py` | Stable `EntofileError` hierarchy for configuration, manifest, container, integrity, pipeline, and artifact failures |
| `paths.py` | Frozen `ProjectPaths` contract for multi-root output and release workflows |
| `structured_data.py` | Duplicate-key-safe structured readers and atomic JSON/text writers |
| `test_results.py` | Fail-closed JUnit XML and coverage summary parser |
| `crypto_gcm.py` | AES-256-GCM encrypt/decrypt (default `0.4.0`; compatibility `0.2.0`/`0.3.0`/`0.3.1`) |
| `container.py` | `pack_container`, `unpack_container`, `inspect_container`, `verify_container`, `_with_verified_container` |
| `security.py` | `validate_track_id`, `validate_zip_archive`, `safe_output_path` |
| `verification_report.py` | `build_container_verification_report`, `write_container_verification_report` |
| `output_gates.py` | `validate_all_outputs`, `benchmark_report_ok`, `container_verification_report_ok` |
| `artifact_manifest.py` | Standalone `output/reports/artifact_manifest.json` writer |
| `benchmark_profiles.py` | Optional benchmark profile runner outside release outputs |
| `conformance.py` | Deterministic fixture generator and conformance report verifier |
| `figure_qa.py` | Renderer-aware figure text clipping/overlap QA |
| `public_promotion.py` | Public-promotion metadata consistency checker |
| `release_bundle.py` | Release manifest and `SHA256SUMS` builder for external signing |
| `telemetry.py` | CLI JSON sidecar and JSONL telemetry helpers |
| `benchmark_filters.py` | `AUDITABLE_LEVEL`, `MEDIUM_TRACK_PREFIX`, `SMALL_TRACKS_R0_PREFIX`, `filter_rows`, `is_tamper_detected` |
| `benchmark_stats.py` | `avg_field`, `result_table_rows`, `tamper_detected_count` (uses `figure_registry.spec_by_label`, `filter_rows_for_spec`) |
| `viz_theme.py` | `bind_viz`, `open_figure`, `open_panel`, `save_figure`, `PALETTE`, `FIGSIZE_PRESETS` |
| `figure_plotters.py` | `plot_*`, `render_to_path` (matplotlib plotters; filters via `filter_rows_for_spec`) |
| `figure_registry.py` | `FIGURE_SPECS`, `spec_by_label`, `filter_rows_for_spec`, `spec_filter_description`, `plot_title`, `figure_caption`, `generate_all_figures` |
| `figures.py` | `generate_*_figure`, `configure_viz` (thin dispatch to plotters) |
| `analysis.py` | `run_benchmark_pipeline`, `validate_generated_outputs` |
| `manuscript_variables.py` | `generate_variables` |

## Security invariants

1. **Track IDs** — `validate_track_id()` before pack/unpack/CLI output.
2. **Format dispatch** — `decrypt_payload(..., format_version=...)` from manifest.
3. **Container prelude** — shared `_with_verified_container`; `inspect` uses `manifest_only` integrity.
4. **Analysis gate** — `validate_all_outputs` reads on-disk reports only.

Line-count: prefer focused modules; `figure_registry.py` and `figure_plotters.py` may exceed 250 lines when registry/plot code stays cohesive. Project script hard fail is 950 lines (`scripts/gates/module_line_count_check.py`).
