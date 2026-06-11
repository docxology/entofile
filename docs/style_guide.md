# Style Guide — entofile

1. **Zero mock tests** — real execution over documented fixture, synthetic stress, and conformance-vector inputs; do not claim universal real-world observational inputs.
2. **Infrastructure delegation** — optional imports behind try/except in orchestration modules.
3. **Thin orchestrators** — scripts call `src/`; no crypto in scripts.
4. **Show not tell** — manuscript cites file paths and function names.
5. **Explicit paths** — `data/fixtures/`, `output/data/ento_benchmark_results.csv`.
6. **Type hints** — public APIs in `src/` annotated.
7. **Error messages** — fail closed with actionable strings (e.g. digest mismatch).

## Naming

- Track types: `ento:` URI prefix
- Observability: `ObservabilityLevel` enum names in code; numeric levels in CSV

## Module size

Keep modules under 250 lines; extract helpers rather than growing monoliths.
