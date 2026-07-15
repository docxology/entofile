# data/ AGENTS.md

Fixture files are committed and small. Do not store secrets or large datasets here.

## Artifacts

| Path | Role |
| --- | --- |
| `ento_manifest_schema.json` | `format_version` enum: `0.2.0`, `0.3.0`, `0.3.1`, `0.4.0`, `0.5.0`; 0.5.0 requires `manifest_binding` |
| `ento_track_header.ksy` | Binary track layout; tag semantics per format version |
| `claim_ledger.yaml` | Publication claims → tests ([`../docs/claim_ledger.md`](../docs/claim_ledger.md)) |
| `conformance/README.md` | Deterministic fixture policy; generated vectors live under `output/conformance/` |
| `test_vectors/hkdf_regression.json` | HKDF pin |
| `test_vectors/aes256_gcm_regression.json` | GCM pin |

Figure and benchmark filters use `AUDITABLE_LEVEL` (`"3"`) from [`../src/benchmark_filters.py`](../src/benchmark_filters.py); plot titles and registry captions share `spec_filter_description()` in `figure_registry.py`.

## claim_ledger.yaml

Claims bind manuscript numbers to artifacts. Security claims: `tamper-detection-rate`, `container-verify-gate`, `crypto-backend-gcm`, `container-verification-report`, `figure-caption-registry`.
