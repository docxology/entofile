# Syntax Guide — entofile

Manuscript authoring reference. Project overlay: [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md).

## {{TOKEN}} table

| Token | Meaning |
| --- | --- |
| `FORMAT_VERSION` | `0.4.0` |
| `FORMAT_VERSION_NEXT` | Opt-in authenticated-manifest-context profile |
| `FORMAT_NEXT_AAD_TEMPLATE` | 0.5.0 AAD template |
| `FORMAT_VERSIONS_COMPATIBILITY` | Prior supported wire formats |
| `FORMAT_DEFAULT_EXPANSION_MODEL` | Default format expansion-law wording |
| `CONFIG_BENCHMARK_REPETITIONS` | Benchmark repetitions |
| `CONFIG_BENCHMARK_PILOT_REPETITIONS` | Pilot repetition baseline |
| `CONFIG_BENCHMARK_REPETITION_SCALE` | Repetition multiplier relative to the pilot setting |
| `CONFIG_OBSERVABILITY_LEVELS` | Level sweep list |
| `CONFIG_MEDIUM_TRACK_BYTES` | Medium synthetic track size |
| `CONFIG_HASH` | Config SHA-256 prefix |
| `CONFIG_VERSION` | Paper version |
| `CONFIG_FIRST_AUTHOR` | Primary author |
| `CONFIG_KEYWORDS` | Keyword list |
| `RESULT_BENCHMARK_ROWS` | CSV row count |
| `RESULT_ROWS_PER_REPETITION` | Rows contributed by each repetition |
| `RESULT_EXPECTED_BENCHMARK_ROWS` | Config-derived expected row count |
| `RESULT_AVG_THROUGHPUT_MIB_S` | Mean pack throughput |
| `RESULT_THROUGHPUT_N` | Headline throughput repetition count |
| `RESULT_THROUGHPUT_DF` | Headline throughput degrees of freedom |
| `RESULT_THROUGHPUT_CI_METHOD` | Confidence-interval method wording |
| `RESULT_AVG_UNPACK_SECONDS` | Mean unpack latency |
| `RESULT_AVG_EXPANSION_RATIO` | Mean expansion |
| `RESULT_TAMPER_DETECTED_COUNT` | Tamper detections |
| `RESULT_TABLE_ROWS` | Table markdown rows |
| `RESULT_MANIFEST_BYTES_L0`–`L3` | Manifest size by level |
| `FIXTURE_*_SHA256` | Fixture digests |
| `FIXTURE_TRACK_COUNT` | Fixture count |
| `BENCHMARK_CSV_SHA256` | CSV digest |
| `ARTIFACT_FIGURES` | Figure filenames |
| `ARTIFACT_DATA_FILES` | Data filenames |
| `PYTHON_VERSION` | Python version |
| `PLATFORM` | OS platform string |
| `GENERATION_TIMESTAMP` | UTC timestamp |

## Figures

All registered benchmark and security figures live in `output/figures/` and use `{#fig:…}` labels documented in [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md).

## Citations

Use `[@citekey]` with keys from [`../manuscript/references.bib`](../manuscript/references.bib). Research backing: [`research/related_formats.md`](research/related_formats.md).
