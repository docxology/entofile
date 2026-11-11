# entofile — project documentation

Active project implementing **ENTO** on **Python 3.15** with **`format_version` 0.5.0 only** and AES-256-GCM. Layout mirrors `template_code_project`: modular `src/`, thin `scripts/`, 90% test coverage, manuscript with `{{TOKEN}}` injection.

## Module map

| Module | Role |
| --- | --- |
| `src/crypto.py` | Facade: HKDF, strict 0.5.0 encrypt/decrypt, nonce/AAD/padding policy |
| `src/errors.py` | Stable ENTO domain error hierarchy |
| `src/paths.py` | Shared `ProjectPaths` output/data/release path contract |
| `src/structured_data.py` | Fail-closed JSON/YAML/TOML readers and atomic report writers |
| `src/crypto_gcm.py` | AES-256-GCM write path (`cryptography`); 12-byte nonce + manifest-context AAD |
| `src/padding.py` | Mandatory PADMÉ length-padding for ENTO 0.5.0 |
| `src/security.py` | Track ID policy, ZIP limits (+ dup-member reject), safe output paths |
| `src/verification_report.py` | `container_verification.json` builder |
| `src/output_gates.py` | Figure registry metadata gate |
| `src/conformance.py` | Deterministic conformance fixtures and verifier |
| `src/benchmark_profiles.py` | Optional expanded benchmark profile runner |
| `src/figure_qa.py` | Renderer-aware figure text layout checks |
| `src/public_promotion.py` | Public-promotion metadata consistency checks |
| `src/telemetry.py` | CLI JSON sidecars and JSONL telemetry |
| `src/release_bundle.py` | Release manifest and checksum bundle |
| `src/track.py` | Track encrypt/decrypt, binary header |
| `src/manifest.py` | JSON Schema validation |
| `src/container.py` | ZIP pack/unpack/inspect/**verify** |
| `src/figure_registry.py` | Code-derived figures, `FIG_CAPTION_*` tokens |
| `src/analysis.py` | Pipeline orchestration; `validate_generated_outputs` |
| `src/publication.py` | `check_publication_readiness` |
| `src/test_results.py` | Fail-closed JUnit XML and coverage summary parser |

## Pipeline

```bash
uv run python scripts/ento_analysis.py
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
uv run python scripts/check_figure_layout.py
uv run python scripts/export_sbom.py
cd <template-checkout>
uv run --no-sync --locked --python 3.15 python scripts/pipeline/stage_03_render.py --project working/entofile
cd projects/working/entofile
uv run python scripts/build_release_bundle.py
uv run python scripts/run_tests.py
cd ../../..
uv run --no-sync --locked --python 3.15 python scripts/pipeline/stage_03_render.py --project working/entofile
uv run --no-sync --locked --python 3.15 python projects/working/entofile/scripts/audit_publication_readiness.py --check
uv run --no-sync --locked --python 3.15 python scripts/maintenance/refresh_artifact_manifests.py --project working/entofile
uv run --no-sync --locked --python 3.15 python scripts/pipeline/stage_04_validate.py --project working/entofile
cd projects/working/entofile
uv run python scripts/build_release_bundle.py
uv run python scripts/check_public_promotion_metadata.py --check
```

## Output reports

| File | Role |
| --- | --- |
| `output/reports/benchmark_validation.json` | Tamper rate gate |
| `output/reports/container_verification.json` | Per-sample `verify_container` |
| `output/reports/conformance_report.json` | Known-good/bad fixture acceptance report |
| `output/reports/figure_layout_report.json` | Renderer-aware figure text layout QA |
| `release/release_manifest.json` | Outer release artifact/checksum manifest for signing |
| `output/reports/validation_report.json` | SDK stage 04 PDF/manuscript validation |
| `output/reports/test_results.json` | Pytest summary |

Release gate: `scripts/audit_publication_readiness.py --check`.

## Reproducibility anchor

`benchmark_data_fingerprint` (`src/benchmark_stats.py`) SHA-256s only the deterministic
benchmark columns (expansion ratios, manifest bytes, tamper outcomes) — excluding the
re-measured wall-clock timings — and is exposed as `BENCHMARK_DATA_FINGERPRINT`. Unlike
`BENCHMARK_CSV_SHA256` (a one-run provenance stamp), it reproduces byte-for-byte on every
regeneration; see the determinism contract in [`docs/methods.md`](docs/methods.md#determinism-contract)
and the binding + negative-control tests in `tests/test_data_fingerprint.py`.

## Security invariants

- Track IDs: `^[a-z0-9._-]+$`.
- ENTO format `0.5.0` only / AES-256-GCM with authenticated exported-manifest context; reject every other wire version.
- Verify before unpack; structured stderr JSON on failure.
- Docs: [`docs/security.md`](docs/security.md), [`docs/entofile-threat-model.md`](docs/entofile-threat-model.md), [`docs/claim_ledger.md`](docs/claim_ledger.md), [`docs/nation_state_roadmap.md`](docs/nation_state_roadmap.md).
