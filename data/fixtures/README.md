# Fixture tracks

Deterministic inputs for pack, benchmark, and manuscript digest tokens.

| File | Track id | Type URI |
| --- | --- | --- |
| `eeg.csv` | `eeg` | `ento:timeseries.eeg` |
| `sample.vcf` | `vcf` | `ento:genomics.vcf` |
| `spectrogram.bin` | `spectrogram` | `ento:spectrogram` |

`spectrogram.bin` is 64 bytes (8×8 matrix, values `i % 256`). Load via `src/fixtures.py::load_fixture_tracks`.
