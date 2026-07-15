# Testing Philosophy — entofile

## Zero mocks

No `unittest.mock`, `MagicMock`, or `@patch`. Tests exercise real crypto, real temp files, fixtures, ZIP I/O, subprocesses, CSV parsing, and generated reports. Fixture and conformance inputs may be deterministic or synthetic by design; the no-mock rule means the execution path is real, not that every input is a real-world observational dataset.

## Coverage

90% minimum on project-root `src/`. Run from the project root (`projects/working/entofile` in the private checkout):

```bash
uv run python scripts/run_tests.py
```

## Test modules

| File | Focus |
| --- | --- |
| `test_crypto.py` | AEAD round-trip, tamper rejection |
| `test_container.py` | Pack/unpack, digest binding |
| `test_proof.py` | Chain + manifest_sha256 export |
| `test_observability.py` | Levels 0–3 redaction |
| `test_manifest.py` | JSON Schema validation |
| `test_benchmarks.py` | Benchmark row shape |
| `test_analysis_integration.py` | Pipeline + validation gate |
| `test_figures.py` | Figure registry + PNG DPI contract |
| `test_crypto_vectors.py` | Pinned HKDF/AES regression vectors |
| `test_experiment_config.py` | YAML-driven benchmark + viz config |
| `test_manuscript_variables.py` | Tokens + live cross-reference |
| `test_claim_ledger.py` | Claim ledger YAML |

## Negative controls

Security tests include forged manifest hashes, tampered tags, invalid schema digests, and proof export mismatch cases added during RedTeam hardening.

Generated outputs are not required for core statistics tests: tests use deterministic
in-memory rows so an ignored or stale `output/` tree cannot turn a broken assertion into
a skip. Publication conformance checks require the complete code-defined case matrix,
not merely one passing fixture.
