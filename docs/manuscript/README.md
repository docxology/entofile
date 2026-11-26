# Manuscript directory

ENTO wire format **0.5.0**-only paper source for the manuscript release. The implementation requires Python 3.15 and rejects every other wire version. Sections `00_abstract` through `08_limitations_and_threat_model`, plus `99_references`.

## Read in render order

1. [Abstract](00_abstract.md) and [introduction](01_introduction.md)
2. [Methods](02_methodology.md), [ontology and fixtures](02a_ontology_and_fixtures.md), [proof and observability](02b_proof_and_observability.md), [security verification](02c_security_verification.md), and [formal model](02d_formal_model.md)
3. [Results](03_results.md) and [benchmark interpretation](03a_benchmark_interpretation.md)
4. [Conclusion](04_conclusion.md), [experimental setup](05_experimental_setup.md), and [reproducibility](06_reproducibility.md)
5. [Scope and related work](07_scope_and_related_work.md), [limitations](08_limitations_and_threat_model.md), and [references](99_references.md)

The [configuration](config.yaml), [preamble](preamble.md), and
[bibliography](references.bib) travel with the editable sections. The figure
registry links to analysis-generated images. Hydrated sources and generated
assets live under `output/`.

## Variables

Numeric claims use `{{TOKEN}}` placeholders resolved by `scripts/z_generate_manuscript_variables.py` from `src/manuscript_variables.py`. See [`AGENTS.md`](AGENTS.md) for the full token catalog.

## Agent docs

- [`AGENTS.md`](AGENTS.md) — token registry and workflow
- [`SYNTAX.md`](SYNTAX.md) — citation, figure, table syntax
- [Rendering pipeline](../rendering_pipeline.md) — PDF pipeline
