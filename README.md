# entofile

<p align="center">
  <a href="https://github.com/docxology/entofile/actions/workflows/ci.yml"><img alt="ci.yml workflow status on main" src="https://github.com/docxology/entofile/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://doi.org/10.5281/zenodo.20396328"><img alt="Digital Object Identifier (DOI), concept record: 10.5281/zenodo.20396328" src="https://zenodo.org/badge/DOI/10.5281/zenodo.20396328.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="Requires Python 3.15" src="https://img.shields.io/badge/python-3.15-3776AB?logo=python&logoColor=white">
</p>

**ENTO** (**EN**crypted, **T**yped, **O**mnitrack) format **0.5.0** reference implementation: a flat ZIP archive that bundles many independently typed research tracks — time series, genomics slices, spectrograms, provenance proofs — each sealed under per-track AES-256-GCM authenticated encryption, with graded observability levels and optional hash-chained proof export. ENTO 0.5.0 is the only supported wire format. It uses a 12-byte GCM nonce, mandatory PADMÉ length padding, and authenticated exported-manifest context in every track tag. Always *verify before unpack*.

Author: Daniel Ari Friedman (Active Inference Institute). DOI: [10.5281/zenodo.20396329](https://doi.org/10.5281/zenodo.20396329) (version) · [10.5281/zenodo.20396328](https://doi.org/10.5281/zenodo.20396328) (concept, always latest).

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/); project dependencies resolve automatically on the first `uv run`.

Python 3.15 is required. Installed wheels include the manifest schema,
deterministic example tracks, and type marker, so container operations also work
outside a source checkout:

```bash
uv tool install .
entofile genkey -o master.key
entofile pack -k master.key -o example.ento.zip
entofile verify -i example.ento.zip -k master.key
entofile unpack -i example.ento.zip -k master.key -o decrypted
```

Optional `--json-output` and `--telemetry-jsonl` paths must be distinct from each
other, command inputs/outputs, and fixture or extraction directories. Symlinked
or multiply-linked sidecars are rejected; JSON results are replaced atomically. A sidecar write
failure returns a nonzero exit code even if the primary operation completed.

```bash
# From this project root — install the development tools once:
uv sync --locked --extra dev
# These validation commands run on a standalone clone:
uv run python scripts/run_tests.py
uv run python scripts/ento_analysis.py
uv run python scripts/check_figure_layout.py
```

The full test gate intentionally includes publication checks. On a standalone
checkout, three promotion tests require template rendering to provide
`output/pdf/entofile_combined.pdf`, `output/web/index.html`, and the transmission
manifest, followed by a release-bundle refresh. Missing release evidence is not
silently skipped. See [the maintenance review](docs/maintenance_review_2026_10_16.md)
for the historical standalone scope, and [publication validation](docs/publication_validation_2026_10_18.md)
for the completed render-dependent checks and remaining external release boundary.

Manuscript-variable injection and PDF rendering are template-integrated: they
require a template repository checkout and exit with a clear message on a
standalone clone.

```bash
# Requires a template checkout (see docs/rendering_pipeline.md):
uv run python scripts/z_generate_manuscript_variables.py
```

Public home: [github.com/docxology/entofile](https://github.com/docxology/entofile).
Development source: `projects/working/entofile` (within the maintainer's monorepo).

See [AGENTS.md](AGENTS.md) for module map, [docs/architecture.md](docs/architecture.md) for the format specification, [docs/format_0_5_0.md](docs/format_0_5_0.md) for the current authenticated-manifest profile, [docs/operator_checklist.md](docs/operator_checklist.md) for safe operations, [docs/evidence_provenance.md](docs/evidence_provenance.md) for the no-mock evidence boundary, [docs/figure_registry.md](docs/figure_registry.md) for the code-derived visual evidence contract, [docs/research/agenda.md](docs/research/agenda.md) and [docs/research/agenda.yaml](docs/research/agenda.yaml) for the preregistered research agenda, [SECURITY.md](SECURITY.md) for vulnerability reporting, [CITATION.cff](CITATION.cff) for citation metadata, and [TODO.md](TODO.md) for roadmap items.
