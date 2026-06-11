# Benchmark Profiles

The 0.4 paper release candidate uses `manuscript/config.yaml`: 150 repetitions,
four observability levels, fixture tracks plus the medium synthetic track, for
2400 rows. Keep that profile stable for release comparisons.

## Expanded Reviewer Profile

`configs/benchmark_expanded.yaml` is a non-default stress profile. It enables:

- a 1 MiB synthetic `large` track;
- a mixed multi-track container containing the fixture tracks plus the medium
  synthetic track;
- 30 repetitions, producing 36 rows per repetition and 1080 rows total.

Run it only when you want additional stress evidence without overwriting release
outputs:

```bash
uv run python scripts/run_benchmark_profile.py \
  --config configs/benchmark_expanded.yaml
```

The script writes CSV, validation, and summary files under
`output/benchmark_profiles/expanded/`. It does not replace
`output/data/ento_benchmark_results.csv`, so the manuscript variables and
release figures remain bound to the 0.4 release matrix unless explicitly
regenerated from `manuscript/config.yaml`.
