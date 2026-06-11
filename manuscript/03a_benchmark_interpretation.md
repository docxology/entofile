# Benchmark interpretation {#sec:benchmark_interpretation}

Benchmarks execute via `src/benchmarks.py::run_all_benchmarks` and write `output/data/ento_benchmark_results.csv` (SHA-256: `{{BENCHMARK_CSV_SHA256}}`). Filter definitions for plots and injected statistics match [`docs/methods.md`](../docs/methods.md#figure-filter-contract). This section interprets primary metrics declared in `experiment_plan.yaml`.

## Baselines and conditions

| Condition | Role | Tracks |
| --- | --- | --- |
| `small_tracks_r*` | Baseline | Fixture tracks under 4 KiB |
| `medium_tracks_r*` | Throughput | Synthetic {{CONFIG_MEDIUM_TRACK_BYTES}}-byte spectrogram payload |
| Observability sweep | Ablation | Export levels {{CONFIG_OBSERVABILITY_LEVELS}} |

Each row records pack/unpack latency, expansion ratio, manifest bytes, and a tamper-injection outcome.

## Pack and unpack latency

![{{FIG_CAPTION_UNPACK_LATENCY}}](../output/figures/unpack_latency.png){#fig:unpack_latency width={{FIGURE_WIDTH}}%}

[@fig:unpack_latency] compares mean pack versus unpack wall time on medium tracks at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}. Mean unpack latency on the throughput condition: {{RESULT_AVG_UNPACK_SECONDS}} s ([@fig:throughput_benchmark]).

## Throughput across observability levels

![{{FIG_CAPTION_THROUGHPUT_BY_OBSERVABILITY}}](../output/figures/throughput_by_observability.png){#fig:throughput_by_observability width={{FIGURE_WIDTH}}%}

[@fig:throughput_by_observability] plots pack throughput for all `medium_tracks_*` rows grouped by observability level, with a min–max band across repetitions. Lower export levels reduce manifest work during pack, which can shift throughput relative to level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}.

## Manifest size vs throughput trade-off

![{{FIG_CAPTION_OBSERVABILITY_THROUGHPUT_TRADEOFF}}](../output/figures/observability_tradeoff.png){#fig:observability_throughput_tradeoff width={{FIGURE_WIDTH}}%}

[@fig:observability_throughput_tradeoff] scatters `manifest_bytes` against `pack_throughput_mib_s` for medium tracks at level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}, linking observability export size to pack performance ([@sec:proof_observability]).

## Primary metrics

**Pack throughput** (MiB/s) measures plaintext bytes divided by pack wall time on the medium-track condition at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}. Mean across {{RESULT_THROUGHPUT_N}} repetitions: {{RESULT_AVG_THROUGHPUT_MIB_S}} MiB/s (SD {{RESULT_THROUGHPUT_SD_MIB_S}}, CV {{RESULT_THROUGHPUT_CV_PERCENT}}%; [@fig:throughput_benchmark], dispersion in [@fig:throughput_dispersion]). The mean alone is a weak summary here — see the statistical-dispersion subsection below.

**Unpack latency** on the same condition averages {{RESULT_AVG_UNPACK_SECONDS}} seconds per container. Unpack authenticates AEAD tags (format {{FORMAT_VERSION}}) before release and checks plaintext SHA-256 digests when present.

**Expansion ratio** compares ciphertext track size to plaintext on fixture tracks. Mean: {{RESULT_AVG_EXPANSION_RATIO}} ([@fig:expansion_ratio]). Overhead reflects the {{TRACK_HEADER_BYTES}}-byte GCM header (`nonce || tag`) plus the version-selected ciphertext body; for format {{FORMAT_VERSION}}, that body is PADMÉ-padded ([@fig:crypto_overhead]).

### Expansion follows a closed-form law

![{{FIG_CAPTION_EXPANSION_LAW}}](../output/figures/expansion_law.png){#fig:expansion_law width={{FIGURE_WIDTH}}%}

Expansion is not an empirical artifact to be averaged — it is fixed by the selected format. For format {{FORMAT_VERSION}}, a track of $n$ plaintext bytes occupies the {{TRACK_HEADER_BYTES}}-byte header plus a PADMÉ bucket containing an original-length prefix and payload, giving {{FORMAT_DEFAULT_EXPANSION_MODEL}} as derived in [@sec:formal_model]. [@fig:expansion_law] overlays the measured fixture-track ratios on this analytic curve: every point lands on the model (maximum absolute residual at floating-point noise, reported in the figure). Because the header and padding function are spec-fixed rather than fit to the data, the overlay is an empirical confirmation that the implementation realises the closed form over the sampled sizes — not a regression with free parameters. The practical reading is that overhead combines a constant header tax with a bounded length-hiding bucket; it is predictable before packing, but it should not be described as pure timing or compression behavior.

## Statistical dispersion and reliability

![{{FIG_CAPTION_THROUGHPUT_DISPERSION}}](../output/figures/throughput_dispersion.png){#fig:throughput_dispersion width={{FIGURE_WIDTH}}%}

The release benchmark runs {{CONFIG_BENCHMARK_REPETITIONS}} repetitions, a {{CONFIG_BENCHMARK_REPETITION_SCALE}}x increase over the {{CONFIG_BENCHMARK_PILOT_REPETITIONS}}-repetition pilot setting used for routine smoke checks. Each repetition contributes {{RESULT_ROWS_PER_REPETITION}} rows, so the expected release matrix is {{RESULT_EXPECTED_BENCHMARK_ROWS}} rows before any validation filtering. For medium-track pack throughput at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}} the sample is n = {{RESULT_THROUGHPUT_N}} (df = {{RESULT_THROUGHPUT_DF}}), with mean {{RESULT_AVG_THROUGHPUT_MIB_S}} MiB/s, sample standard deviation {{RESULT_THROUGHPUT_SD_MIB_S}} MiB/s, and coefficient of variation {{RESULT_THROUGHPUT_CV_PERCENT}}% ([@fig:throughput_dispersion]). The two-sided 95% confidence interval is [{{RESULT_THROUGHPUT_CI95_LO_MIB_S}}, {{RESULT_THROUGHPUT_CI95_HI_MIB_S}}] MiB/s, computed as {{RESULT_THROUGHPUT_CI_METHOD}}.

The larger repetition count improves the within-run estimate, but it does not turn a local wall-clock measurement into a portable performance claim. Re-running the benchmark re-measures elapsed time, so the mean, CV, and interval bounds remain host-state snapshots affected by CPU scheduling, filesystem cache state, background load, and Python/cryptography build details. The operational claim is therefore bounded: **the reported throughput summarizes this release run, and ENTO makes no cross-implementation throughput-superiority claim from it**. This caveat is specific to wall-clock metrics. The data-derived metrics (expansion ratio, ciphertext byte counts, manifest size, and tamper outcomes) are exact functions of byte counts, schema choices, or deterministic checks; their reproducibility is anchored separately by the data fingerprint. The figures split accordingly: [@fig:expansion_law] is a byte-exact overlay, [@fig:throughput_dispersion] is a re-measured timing sample, and [@fig:determinism_cv] shows which columns belong to each side of the boundary. The code enforces the distinction through the figure registry's `data_derived` determinism contract.

### Variation by metric

![{{FIG_CAPTION_DETERMINISM_CV}}](../output/figures/determinism_cv.png){#fig:determinism_cv width={{FIGURE_WIDTH}}%}

[@fig:determinism_cv] makes the deterministic/measured split directly visible: the coefficient of variation across repetitions is exactly zero for the data-derived columns (expansion ratio, ciphertext bytes, manifest bytes) and strictly positive for the wall-clock columns (pack and unpack time, pack throughput). This is the empirical basis for the data fingerprint in [@sec:reproducibility], which hashes only the zero-variation columns and leaves the timing columns to be reported with their dispersion ([@fig:throughput_dispersion]) rather than folded into a reproducibility anchor.

## Observability trade-off

Manifest byte counts shrink monotonically from level {{CONFIG_OBSERVABILITY_LEVEL_MAX}} → 0 ([@fig:observability_manifest_size]; numeric levels in [@sec:proof_observability]). Level 0 minimizes metadata leakage at the cost of auditability—appropriate for sealed distribution; level {{CONFIG_OBSERVABILITY_LEVEL_MAX}} supports reproducibility checks against fixture digests in [@sec:ontology_fixtures].

## Tamper detection

Every benchmark row corrupts a ciphertext tag byte and expects unpack to fail closed. Detected attempts: {{RESULT_TAMPER_DETECTED_COUNT}} of {{RESULT_BENCHMARK_ROWS}} ([@fig:tamper_detection]). Validation requires tamper detection rate {{RESULT_TAMPER_DETECTION_RATE}} with status {{RESULT_BENCHMARK_VALIDATION_STATUS}} in `output/reports/benchmark_validation.json`, and `container_verification.json` with aggregate status {{RESULT_CONTAINER_VERIFY_OK}} ([@sec:security_verification]).

## Results table

Table [@tbl:ento_benchmark_results] summarizes fixture-track rows at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}:

| Track | Type | Plaintext bytes | Expansion | Throughput (MiB/s) |
| --- | --- | --- | --- | --- |
{{RESULT_TABLE_ROWS}}

: Benchmark summary for fixture tracks at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}. {#tbl:ento_benchmark_results}

Raw CSV rows: {{RESULT_BENCHMARK_ROWS}} total across all conditions and repetitions ({{CONFIG_BENCHMARK_REPETITIONS}} repetitions × {{RESULT_ROWS_PER_REPETITION}} rows per repetition; expected total {{RESULT_EXPECTED_BENCHMARK_ROWS}}).
