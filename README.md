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

From a checkout, use Python 3.15 and [uv](https://docs.astral.sh/uv/) to run the bundled deterministic example.

```sh
uv sync --locked --extra dev
uv run entofile genkey -o master.key
uv run entofile pack -k master.key -o example.ento.zip
uv run entofile verify -i example.ento.zip -k master.key
uv run entofile unpack -i example.ento.zip -k master.key -o decrypted
```

The [documentation index](docs/README.md) links to the [quickstart](docs/quickstart.md),
the [operator checklist](docs/operator_checklist.md), the [format specification](docs/format_0_5_0.md),
and the [manuscript](docs/manuscript/README.md). The [evidence provenance guide](docs/evidence_provenance.md) identifies the inputs behind the reported results. See [SECURITY.md](SECURITY.md)
for vulnerability reporting and [CITATION.cff](CITATION.cff) for citation metadata.

Public home: [github.com/docxology/entofile](https://github.com/docxology/entofile).
Development source: `projects/working/entofile` in the maintainer's template checkout.
