# Ontology and fixtures {#sec:ontology_fixtures}

ENTO registers track types as stable URIs in `src/ontology.py`. Each URI maps to required resolution keys validated before pack, so manifests cannot claim a genomics track without the chromosome/build metadata the ontology expects.

## URI registry

| URI | Label | Required resolution keys |
| --- | --- | --- |
| `ento:timeseries.eeg` | EEG time series | `hz` |
| `ento:genomics.vcf` | VCF genomics slice | `build`, `chr` |
| `ento:spectrogram` | Spectrogram matrix | `hz`, `n_fft`, `shape` |
| `ento:blockchain.proof` | Proof chain anchor | (none) |

New types extend the registry without changing the ZIP layout: manifests reference the URI string; exporters may redact resolution fields at lower observability levels ([@sec:methodology]). The URI table is the contract between producers and downstream tools that interpret manifests without opening ciphertext.

## Committed fixtures

The benchmark pipeline loads {{FIXTURE_TRACK_COUNT}} deterministic tracks from `data/fixtures/` via `src/fixtures.py`:

| File | Track id | SHA-256 (plaintext) |
| --- | --- | --- |
| `eeg.csv` | `eeg` | `{{FIXTURE_EEG_SHA256}}` |
| `sample.vcf` | `vcf` | `{{FIXTURE_VCF_SHA256}}` |
| `spectrogram.bin` | `spectrogram` | `{{FIXTURE_SPECTROGRAM_SHA256}}` |

Missing fixtures fail closed when `require_all=True` (CLI pack and benchmark entry points). The spectrogram fixture is a small square deterministic byte matrix documented in `data/fixtures/README.md`. Fixtures anchor expansion and manifest-size figures ([@sec:results]) to bytes that remain in version control.

Fixture digests bind manuscript claims to committed bytes; regenerating fixtures updates both benchmarks and the `FIXTURE_EEG_SHA256`, `FIXTURE_VCF_SHA256`, and `FIXTURE_SPECTROGRAM_SHA256` tokens in `output/data/manuscript_variables.json`.
