# Manuscript directory

ENTO default format **0.5.0** paper source for the manuscript release, including compatibility notes for formats **0.2.0**, **0.3.0**, **0.3.1**, and **0.4.0**. Sections `00_abstract` through `08_limitations_and_threat_model`, plus `99_references`.

## Render order

Lexicographic `NN_*.md` files. Paper-grade inserts: `02a`, `02b`, `03a`, `08`.

## Variables

Numeric claims use `{{TOKEN}}` placeholders resolved by `scripts/z_generate_manuscript_variables.py` from `src/manuscript_variables.py`. See [`AGENTS.md`](AGENTS.md) for the full token catalog.

## Agent docs

- [`AGENTS.md`](AGENTS.md) — token registry and workflow
- [`SYNTAX.md`](SYNTAX.md) — citation, figure, table syntax
- [`../docs/rendering_pipeline.md`](../docs/rendering_pipeline.md) — PDF pipeline
