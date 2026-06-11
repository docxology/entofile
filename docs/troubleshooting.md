# Troubleshooting — entofile

## Tests fail on coverage

```bash
uv run pytest tests/ --cov=src --cov-report=term-missing
```

Target: ≥90% on `src/`.

## `FileNotFoundError: ento_benchmark_results.csv`

Run analysis before variable generation:

```bash
uv run python scripts/ento_analysis.py
```

## Unresolved tokens in PDF

```bash
uv run python scripts/z_generate_manuscript_variables.py
grep -r "{{" output/manuscript/
```

Fix failing `test_all_manuscript_tokens_are_generated`.

## Validation gate `ok: false`

Check `output/reports/benchmark_validation.json` — requires `status: pass` and `tamper_detection_rate: 1.0`.

## Unpack digest mismatch

Manifest `sha256_plaintext` must match decrypted bytes; update manifest or payload consistently.

## Proof verify fails after export

Ensure `verify_proof_export` receives the same manifest JSON bytes used at export; tampering `manifest.json` invalidates chain.

## Missing fixtures

Ensure `data/fixtures/eeg.csv`, `sample.vcf`, `spectrogram.bin` exist. See `src/fixtures.py`.

## PDF figure missing

Confirm PNGs under `output/figures/` and paths in manuscript use `../output/figures/`.
