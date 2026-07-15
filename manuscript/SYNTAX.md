# Manuscript Syntax Reference (entofile)

Overlay for ENTO manuscript authoring (default format 0.5.0; compatibility formats 0.2.0/0.3.0/0.3.1/0.4.0). Repository-wide semantics: [docxology manuscript semantics guide](https://github.com/docxology/template/blob/main/docs/guides/manuscript-semantics.md).

## Citations

```markdown
[@wilkinson2016fair]
[@hdf5_tr; @zarr_v2]
[@krawczyk2010hkdf, sec. 2]
@ferguson2010cryptography recommend verifying tags before release.
```

Keys must exist in [`references.bib`](references.bib). Do not use raw `\cite{}` in Markdown.

## Figures

```markdown
![{{FIG_CAPTION_THROUGHPUT_BENCHMARK}}](../output/figures/throughput_benchmark.png){#fig:throughput_benchmark width={{FIGURE_WIDTH}}%}
[@fig:throughput_benchmark] shows...
```

Alt text must use `{{FIG_CAPTION_*}}` tokens exported from `src/figure_registry.py::figure_caption_variables()` — do not hand-author figure captions in markdown.

Registry source of truth: `src/figure_registry.py::FIGURE_SPECS` ({{FIGURE_COUNT}} figures). Optional section blocks: `{{FIGURE_BLOCK_RESULTS}}`, `{{FIGURE_BLOCK_BENCHMARK_INTERP}}`, `{{FIGURE_BLOCK_METHODOLOGY}}`, `{{FIGURE_BLOCK_SECURITY}}`. Index: `{{FIGURE_INDEX}}` in [@sec:reproducibility].

| Label | PNG | Section | Kind |
| --- | --- | --- | --- |
| `{#fig:benchmark_overview}` | `benchmark_overview.png` | results | panel |
| `{#fig:throughput_benchmark}` | `throughput_benchmark.png` | results | scatter |
| `{#fig:expansion_ratio}` | `expansion_ratio.png` | results | bar |
| `{#fig:expansion_heatmap}` | `expansion_heatmap.png` | results | heatmap |
| `{#fig:observability_manifest_size}` | `observability_manifest_size.png` | results | line |
| `{#fig:unpack_latency}` | `unpack_latency.png` | benchmark_interp | bar |
| `{#fig:throughput_by_observability}` | `throughput_by_observability.png` | benchmark_interp | line |
| `{#fig:observability_throughput_tradeoff}` | `observability_tradeoff.png` | benchmark_interp | scatter |
| `{#fig:manifest_multitrack}` | `manifest_multitrack.png` | methodology | line |
| `{#fig:crypto_overhead}` | `crypto_overhead.png` | methodology | bar |
| `{#fig:tamper_detection}` | `tamper_detection.png` | security | bar |

## Tables

```markdown
: Caption text. {#tbl:ento_benchmark_results}
```

Reference with `[@tbl:ento_benchmark_results]`.

## Section cross-references

Use `[@sec:label]` where `#sec:label` appears on section headers (e.g. `{#sec:methodology}`).

## {{TOKEN}} registry

| Token | Source |
| --- | --- |
| `FORMAT_VERSION` | Current default ENTO wire format (`0.5.0`) |
| `FORMAT_VERSION_PREVIOUS` | Explicit compatibility profile (`0.4.0`) |
| `FORMAT_VERSION_NEXT` | Deprecated source-compatible alias for the current profile (`0.5.0`) |
| `FORMAT_NEXT_AAD_TEMPLATE` | Version-derived manifest-context AAD template |
| `FORMAT_NEXT_BINDING_DESCRIPTION` | Version-derived binding description |
| `CRYPTO_BACKEND_DEFAULT` | `crypto_backend_for_format(FORMAT_VERSION)` |
| `PAPER_TITLE` / `PAPER_SUBTITLE` / `PAPER_VERSION` | `manuscript/config.yaml` `paper.*` |
| `NONCE_BYTES` / `TAG_BYTES` | `crypto.NONCE_SIZE` / `TAG_SIZE` |
| `CONFIG_OBSERVABILITY_LEVEL_MAX` | Max observability level |
| `RESULT_TAMPER_DETECTION_RATE` | `benchmark_validation.json` |
| `RESULT_BENCHMARK_VALIDATION_STATUS` | Validation report status |
| `FIGURE_OVERVIEW_WIDTH` | Overview panel width % |
| `RESULT_CONTAINER_VERIFY_OK` | Aggregate container verify gate |
| `RESULT_CONTAINER_VERIFY_SAMPLE` | Sample id from verification report |
| `CONFIG_*` | `experiment_config` + `manuscript/config.yaml` |
| `RESULT_*` | `output/data/ento_benchmark_results.csv` |
| `FIXTURE_*_SHA256` | `data/fixtures/` file hashes |
| `BENCHMARK_CSV_SHA256` | Benchmark CSV hash |
| `ARTIFACT_*` | `output/figures/`, `output/data/` listings |
| `FIG_CAPTION_*` | `figure_registry.py::FIGURE_SPECS[].caption` |
| `FIGURE_BLOCK_*` | `figure_block_markdown(section)` |
| `FIGURE_INDEX` | `figure_index_markdown()` |
| `PYTHON_VERSION`, `PLATFORM`, `GENERATION_TIMESTAMP` | Runtime |
