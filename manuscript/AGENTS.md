# Manuscript (`projects/working/entofile/manuscript/`)

Agent rules: [`../docs/agent_instructions.md`](../docs/agent_instructions.md). This file covers ENTO-specific tokens, figures, and section map.

## Section map

| File | Section id | Tokens / cites |
| --- | --- | --- |
| `00_abstract.md` | — | CONFIG_*, RESULT_* |
| `01_introduction.md` | `{#sec:introduction}` | Citations |
| `02_methodology.md` | `{#sec:methodology}` | `fig:manifest_multitrack`, `fig:observability_redaction_matrix`, `fig:crypto_overhead` |
| `02a_ontology_and_fixtures.md` | `{#sec:ontology_fixtures}` | FIXTURE_*, FIXTURE_TRACK_COUNT |
| `02b_proof_and_observability.md` | `{#sec:proof_observability}` | RESULT_MANIFEST_BYTES_L0–L3 |
| `02c_security_verification.md` | `{#sec:security_verification}` | `fig:tamper_detection`, `fig:format_ladder`, `fig:format_compatibility_matrix`, `fig:length_leakage_profile`, `fig:conformance_outcomes`, `fig:security_control_matrix`, FORMAT_VERSION, RESULT_CONTAINER_VERIFY_* |
| `02d_formal_model.md` | `{#sec:formal_model}` | `eq:container_map`…`eq:observability_monotone`, `fig:expansion_law` |
| `03_results.md` | `{#sec:results}` | Overview + results figures (`fig:benchmark_overview` … `fig:observability_manifest_size`) |
| `03a_benchmark_interpretation.md` | `{#sec:benchmark_interpretation}` | `fig:unpack_latency`, `fig:throughput_by_observability`, `fig:observability_throughput_tradeoff`, `fig:expansion_law`, `fig:throughput_dispersion`, RESULT_THROUGHPUT_* |
| `04_conclusion.md` | `{#sec:conclusion}` | RESULT_BENCHMARK_ROWS, RESULT_TAMPER_DETECTED_COUNT |
| `05_experimental_setup.md` | `{#sec:experimental_setup}` | CONFIG_*, PYTHON_VERSION |
| `06_reproducibility.md` | `{#sec:reproducibility}` | `FIGURE_INDEX`, CONFIG_HASH, ARTIFACT_* |
| `07_scope_and_related_work.md` | `{#sec:scope}` | Citations |
| `08_limitations_and_threat_model.md` | `{#sec:limitations}` | Citations |
| `99_references.md` | `{#sec:references}` | — |

## {{TOKEN}} protocol

1. `scripts/z_generate_manuscript_variables.py` → `generate_variables()` → `output/data/manuscript_variables.json`
2. `write_resolved_manuscript_tree()` → `output/manuscript/*.md`
3. PDF render reads substituted copies

**Adding a token:** extend `src/manuscript_variables.py`, assert in `tests/test_manuscript_variables.py`, reference as `{{TOKEN}}`. Figure alt text must use `{{FIG_CAPTION_*}}` from `figure_caption_variables()` — see `tests/test_figure_captions.py`.

Doc-only files (excluded from cross-reference test): `AGENTS.md`, `README.md`, `SYNTAX.md`.

## Token catalog

| Token | Description |
| --- | --- |
| `FORMAT_VERSION` | Stable default ENTO format (`0.5.0`) |
| `FORMAT_VERSION_PREVIOUS` | Explicit compatibility profile (`0.4.0`) |
| `FORMAT_VERSION_NEXT` | Deprecated source-compatible alias for the current profile (`0.5.0`) |
| `FORMAT_NEXT_AAD_TEMPLATE` | Canonical 0.5.0 manifest-context AAD template |
| `FORMAT_NEXT_BINDING_DESCRIPTION` | Generated description of the bound exported manifest context |
| `CRYPTO_BACKEND_DEFAULT` | Suite from `crypto_backend_for_format(FORMAT_VERSION)` |
| `PAPER_TITLE` | `manuscript/config.yaml` `paper.title` |
| `PAPER_SUBTITLE` | `paper.subtitle` |
| `PAPER_VERSION` | `paper.version` |
| `NONCE_BYTES` | `crypto.NONCE_SIZE` |
| `TAG_BYTES` | `crypto.TAG_SIZE` |
| `CONFIG_OBSERVABILITY_LEVEL_MAX` | Max `experiment.observability_levels` |
| `RESULT_TAMPER_DETECTION_RATE` | `benchmark_validation.json` |
| `RESULT_BENCHMARK_VALIDATION_STATUS` | `benchmark_validation.json` `status` |
| `FIGURE_OVERVIEW_WIDTH` | `fig:benchmark_overview` width percent |
| `RESULT_CONTAINER_VERIFY_OK` | `true`/`false` from verification report |
| `RESULT_CONTAINER_VERIFY_SAMPLE` | First sample id in verification report |
| `CONFIG_BENCHMARK_REPETITIONS` | Repetitions per benchmark condition |
| `CONFIG_BENCHMARK_PILOT_REPETITIONS` | Pilot repetition baseline |
| `CONFIG_BENCHMARK_REPETITION_SCALE` | Repetition multiplier relative to the pilot setting |
| `CONFIG_OBSERVABILITY_LEVELS` | Comma-separated level list |
| `CONFIG_MEDIUM_TRACK_BYTES` | Synthetic medium track size |
| `CONFIG_VIZ_DPI` | Figure export DPI from config |
| `CONFIG_HASH` | Config file SHA-256 prefix |
| `CONFIG_VERSION` | Paper version from config |
| `CONFIG_FIRST_AUTHOR` | First author name |
| `CONFIG_KEYWORDS` | Comma-separated keywords |
| `RESULT_BENCHMARK_ROWS` | Total CSV rows |
| `RESULT_ROWS_PER_REPETITION` | Rows contributed by each benchmark repetition |
| `RESULT_EXPECTED_BENCHMARK_ROWS` | Config-derived expected benchmark row total |
| `RESULT_AVG_THROUGHPUT_MIB_S` | Mean medium-track pack throughput |
| `RESULT_THROUGHPUT_N` | Headline throughput sample size |
| `RESULT_THROUGHPUT_DF` | Headline throughput degrees of freedom |
| `RESULT_THROUGHPUT_CI_METHOD` | Confidence interval method wording |
| `RESULT_AVG_UNPACK_SECONDS` | Mean medium-track unpack seconds |
| `RESULT_AVG_EXPANSION_RATIO` | Mean fixture expansion ratio |
| `RESULT_TAMPER_DETECTED_COUNT` | Tamper rows detected |
| `RESULT_TABLE_ROWS` | Markdown table body rows |
| `RESULT_MANIFEST_BYTES_L0`–`L3` | EEG manifest bytes by level |
| `FIXTURE_EEG_SHA256` | `eeg.csv` digest |
| `FIXTURE_VCF_SHA256` | `sample.vcf` digest |
| `FIXTURE_SPECTROGRAM_SHA256` | `spectrogram.bin` digest |
| `FIXTURE_TRACK_COUNT` | Number of registered fixtures |
| `FIGURE_COUNT` | Registered figure count |
| `FIGURE_REGISTRY_PATH` | Path to figure_registry.json |
| `BENCHMARK_CSV_SHA256` | Benchmark CSV digest |
| `SBOM_STATUS` | `present`/`missing` for `output/reports/sbom.cyclonedx.json` |
| `SBOM_PATH` | Project-relative CycloneDX SBOM path when present |
| `SBOM_COMPONENT_COUNT` | Component count in the generated CycloneDX SBOM |
| `ARTIFACT_FIGURES` | PNG filenames in `output/figures/` |
| `ARTIFACT_DATA_FILES` | Filenames in `output/data/` |
| `PYTHON_VERSION` | Interpreter version |
| `PLATFORM` | `platform.platform()` |
| `GENERATION_TIMESTAMP` | UTC ISO timestamp |
| `MASTER_KEY_BYTES` | AES master key size (`src/crypto.py`) |
| `TRACK_HEADER_BYTES` | Nonce + tag bytes per track header |
| `TEST_COVERAGE_MIN` | Pytest `--cov-fail-under` floor (90) |
| `MEASURED_COVERAGE_PERCENT` | Latest measured `src/` coverage from test report |
| `FIGURE_WIDTH` | Figure width percent from `manuscript/config.yaml` |
| `FIG_CAPTION_*` | Publication alt text from `figure_registry.py::FIGURE_SPECS[].caption` |
| `FIGURE_INDEX` | Bullet list of all registered figures |
| `FIGURE_BLOCK_*` | Concatenated image markdown per `manuscript_section` (optional) |

## Workflow

```bash
uv run python scripts/ento_analysis.py
uv run python scripts/z_generate_manuscript_variables.py
grep -r "{{" output/manuscript/ || echo "All resolved"
cd <template-checkout>
uv run python scripts/03_render_pdf.py --project working/entofile
```

See [`SYNTAX.md`](SYNTAX.md) and [`../docs/syntax_guide.md`](../docs/syntax_guide.md).
