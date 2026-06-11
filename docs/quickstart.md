# Quick Start — entofile

Run ENTO default format **0.4.0** benchmarks and render the 0.4 paper release
candidate; compatibility `0.2.0`/`0.3.0`/`0.3.1` containers remain supported via
`pack --format`.

## Prerequisites

- Python 3.10+
- `uv sync` at repo root

## Tests

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -v
```

## Analysis

```bash
uv run python scripts/ento_analysis.py
```

`z_generate_manuscript_variables.py` injects manuscript variables and is
template-integrated — it requires a template repository checkout and exits with
a clear message on a standalone clone:

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

Outputs under `output/`:

- `figures/` — benchmark plots
- `data/ento_benchmark_results.csv` — primary metrics
- `reports/benchmark_validation.json` — tamper gate (analysis stage)
- `reports/validation_report.json` — Stage 6 pipeline validation (after full pipeline)

## PDF

```bash
cd <template-checkout>
uv run python scripts/03_render_pdf.py --project working/entofile
```

## CLI

From this project root:

```bash
uv run python -m src.cli genkey -o /tmp/ento.key
uv run python -m src.cli pack -k /tmp/ento.key -o /tmp/demo.ento.zip
uv run python -m src.cli verify -i /tmp/demo.ento.zip -k /tmp/ento.key
```

See [`architecture.md`](architecture.md) and [`agent_instructions.md`](agent_instructions.md).
