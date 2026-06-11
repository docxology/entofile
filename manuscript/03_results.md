# Results {#sec:results}

Benchmarks run via `scripts/ento_analysis.py` and hydrate into this section through `scripts/z_generate_manuscript_variables.py`.

## Code-derived figures

All plots are generated from `output/data/ento_benchmark_results.csv` — never hand-edited. The pipeline in `src/analysis.py`:

1. Runs `src/benchmarks.py::run_all_benchmarks` using parameters from `manuscript/config.yaml` (`experiment.benchmark_repetitions`, `observability_levels`, `medium_track_bytes`).
2. Calls `src/figure_registry.py::generate_all_figures`, which dispatches each registered generator in `src/figures.py`.
3. Writes `output/figures/figure_registry.json` with `generated_by` paths, CSV provenance, `kind`, `manuscript_section`, and `caption_token` names that mirror the manuscript figure-caption variables.

The manuscript references {{FIGURE_COUNT}} figures at {{CONFIG_VIZ_DPI}} DPI via `experiment.viz` in config. Registry path after analysis: `{{FIGURE_REGISTRY_PATH}}`. Alt text for each figure is injected from `FIGURE_SPECS[].caption` in `src/figure_registry.py` (see `docs/figure_registry.md`).

## Benchmark overview

![{{FIG_CAPTION_BENCHMARK_OVERVIEW}}](../output/figures/benchmark_overview.png){#fig:benchmark_overview width={{FIGURE_OVERVIEW_WIDTH}}%}

[@fig:benchmark_overview] summarizes the four primary benchmark views in one panel: medium-track throughput, fixture expansion ratios, EEG manifest shrinkage across observability levels, and tamper-detection outcomes. Use the standalone figures below for print-scale detail.

## Throughput

![{{FIG_CAPTION_THROUGHPUT_BENCHMARK}}](../output/figures/throughput_benchmark.png){#fig:throughput_benchmark width={{FIGURE_WIDTH}}%}

[@fig:throughput_benchmark] summarizes pack throughput for the medium-track condition ({{CONFIG_MEDIUM_TRACK_BYTES}} bytes plaintext) at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}. Mean throughput across filtered repetitions: {{RESULT_AVG_THROUGHPUT_MIB_S}} MiB/s. Registry filters: `condition_prefix=medium_tracks`, `observability_level={{CONFIG_OBSERVABILITY_LEVEL_MAX}}`. The plot overlays individual repetitions with a dashed mean line.

## Expansion ratio

![{{FIG_CAPTION_EXPANSION_RATIO}}](../output/figures/expansion_ratio.png){#fig:expansion_ratio width={{FIGURE_WIDTH}}%}

[@fig:expansion_ratio] compares ciphertext expansion on fixture tracks for `small_tracks_r0` at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}. Mean expansion ratio across those rows: {{RESULT_AVG_EXPANSION_RATIO}}. Registry filters: `condition_prefix=small_tracks_r0`, `observability_level={{CONFIG_OBSERVABILITY_LEVEL_MAX}}`.

## Expansion heatmap

![{{FIG_CAPTION_EXPANSION_HEATMAP}}](../output/figures/expansion_heatmap.png){#fig:expansion_heatmap width={{FIGURE_WIDTH}}%}

[@fig:expansion_heatmap] shows mean `expansion_ratio` for every `condition` × `track_id` pair at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}, highlighting how fixture size and synthetic medium tracks diverge in ciphertext overhead.

## Observability manifest size

![{{FIG_CAPTION_OBSERVABILITY_MANIFEST_SIZE}}](../output/figures/observability_manifest_size.png){#fig:observability_manifest_size width={{FIGURE_WIDTH}}%}

[@fig:observability_manifest_size] traces manifest payload size for the EEG fixture across observability levels declared in config ({{CONFIG_OBSERVABILITY_LEVELS}}). Registry filters: `condition_prefix=small_tracks_r0`, `track_id=eeg`. At level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}, manifest size for this track averages {{RESULT_MANIFEST_BYTES_L3}} bytes in the benchmark CSV.

## Summary table

| Track | Type | Plaintext bytes | Expansion | Throughput (MiB/s) |
| --- | --- | --- | --- | --- |
{{RESULT_TABLE_ROWS}}
