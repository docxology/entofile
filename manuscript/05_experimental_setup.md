# Experimental setup {#sec:experimental_setup}

## Software

- Python {{PYTHON_VERSION}} on {{PLATFORM}}
- ENTO format version {{FORMAT_VERSION}} (suite {{CRYPTO_BACKEND_DEFAULT}})
- Manuscript config version {{CONFIG_VERSION}} (paper version {{PAPER_VERSION}})

## Fixtures

| File | Track id | Ontology type |
| --- | --- | --- |
| `data/fixtures/eeg.csv` | eeg | `ento:timeseries.eeg` |
| `data/fixtures/sample.vcf` | vcf | `ento:genomics.vcf` |
| `data/fixtures/spectrogram.bin` | spectrogram | `ento:spectrogram` |

Evidence classes are intentionally separated rather than collapsed into a vague
real-world-input claim. Fixture inputs are **{{FIXTURE_INPUT_CLASSIFICATION}}**;
the medium throughput condition is a **{{BENCHMARK_STRESS_INPUT_CLASSIFICATION}}**
of {{CONFIG_MEDIUM_TRACK_BYTES}} bytes; conformance cases are
**{{CONFORMANCE_INPUT_CLASSIFICATION}}**; and the benchmark CSV, reports, figures,
and rendered manuscript are **{{EXECUTION_EVIDENCE_CLASSIFICATION}}**. The
fixture and conformance bytes are therefore reproducibility inputs, not
field-collected research observations. This separation follows reproducible
computational research practice: expose scripts, data classes, run parameters,
and outputs so readers can inspect what was actually executed [@sandve2013reproducible;
@wilson2017goodenough]. Figure export uses {{CONFIG_VIZ_DPI}} DPI from
`experiment.viz` in config.

## Benchmark protocol

- Repetitions: {{CONFIG_BENCHMARK_REPETITIONS}}
- Rows per repetition: {{RESULT_ROWS_PER_REPETITION}} (expected total {{RESULT_EXPECTED_BENCHMARK_ROWS}})
- Observability sweep: {{CONFIG_OBSERVABILITY_LEVELS}} (maximum level {{CONFIG_OBSERVABILITY_LEVEL_MAX}})
- Analysis entry point: `uv run python scripts/ento_analysis.py`
- CLI: `uv run python scripts/ento_cli.py pack|unpack|inspect|proof|genkey`

Each repetition packs fixture tracks at every observability level, packs the
synthetic medium track for throughput, corrupts one ciphertext tag byte, and
records whether unpack rejects the container. Results append to
`output/data/ento_benchmark_results.csv` with columns for pack/unpack seconds,
expansion ratio, manifest bytes, and tamper outcome. This is a real execution of
the ENTO pack/unpack/verify path over documented inputs, not a mock or a
substituted result table.

Validation requires `output/reports/benchmark_validation.json` to report status {{RESULT_BENCHMARK_VALIDATION_STATUS}} and tamper detection rate {{RESULT_TAMPER_DETECTION_RATE}}, and `output/reports/container_verification.json` to report all benchmark samples verified (`{{RESULT_CONTAINER_VERIFY_OK}}`). HKDF and GCM vectors in `data/test_vectors/` are exercised before release. Figure DPI follows `src/figures.py::VIZ_CONFIG`; caption tokens follow `src/figure_registry.py` (`tests/test_figure_captions.py`). Claims bind via `data/claim_ledger.yaml` and [`docs/claim_ledger.md`](../docs/claim_ledger.md).

## Statistical methods

Each timing metric is summarized across the {{CONFIG_BENCHMARK_REPETITIONS}} repetitions as mean, sample standard deviation (n − 1), coefficient of variation, and a two-sided 95% confidence interval (`src/benchmark_stats.py::summary_stats`). For the headline throughput sample this is {{RESULT_THROUGHPUT_CI_METHOD}}, with n = {{RESULT_THROUGHPUT_N}} and df = {{RESULT_THROUGHPUT_DF}}. Wall-clock metrics carry run-to-run measurement noise, so the interval describes this release run under local host conditions rather than a cross-host population result — see [@fig:throughput_dispersion] and [@sec:benchmark_interpretation]. Data-derived metrics (expansion ratio, manifest size, ciphertext byte counts, tamper outcomes) are exact functions of byte counts, schema choices, or deterministic checks; their reproducibility is anchored by `BENCHMARK_DATA_FINGERPRINT`, not by timing dispersion. The figure registry encodes this split as a per-figure `data_derived` determinism contract, enforced by `tests/test_figure_determinism.py`.

The project does not request an external artifact badge in this release, but
the generated PDF/HTML, source-bound variables, figure registry, and release
manifest are organized to make the artifact-review distinction between available,
functional, and reusable evidence explicit [@acm2024artifactbadging].

## Environment notes

Benchmarks use a fixed master key per run generated in `run_all_benchmarks`. Timing uses `time.perf_counter()` around pack and unpack calls; throughput divides plaintext MiB by pack seconds on the medium-track rows at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}} only.
