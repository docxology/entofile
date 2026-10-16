# entofile

**ENTO** (**EN**crypted, **T**yped, **O**mnitrack) format **0.5.0** reference implementation: a flat ZIP archive that bundles many independently typed research tracks — time series, genomics slices, spectrograms, provenance proofs — each sealed under per-track AES-256-GCM authenticated encryption, with graded observability levels and optional hash-chained proof export. The 0.5.0 default uses a 12-byte GCM nonce, PADMÉ length padding, and authenticated exported-manifest context in every track tag. Readers preserve compatibility with 0.2.0, 0.3.0, 0.3.1, and 0.4.0 and always *verify before unpack*.

Author: Daniel Ari Friedman (Active Inference Institute). DOI: [10.5281/zenodo.20396329](https://doi.org/10.5281/zenodo.20396329) (version) · [10.5281/zenodo.20396328](https://doi.org/10.5281/zenodo.20396328) (concept, always latest).

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/); project dependencies resolve automatically on the first `uv run`.

Python 3.10 and newer are supported. Installed wheels include the manifest schema,
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
# From this project root — these run on a standalone clone:
uv run python scripts/run_tests.py
uv run python scripts/ento_analysis.py
uv run python scripts/check_figure_layout.py
```

The full test gate intentionally includes publication checks. On a standalone
checkout, three promotion tests remain failing until template rendering provides
`output/pdf/entofile_combined.pdf`, `output/web/index.html`, and the transmission
manifest, followed by a release-bundle refresh. Missing release evidence is not
silently skipped. See [the maintenance review](docs/maintenance_review_2026_10_16.md)
for the latest local validation scope and remaining prerequisites.

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
