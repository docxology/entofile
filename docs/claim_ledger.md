# Claim ledger — entofile

Machine-readable claims live in [`../data/claim_ledger.yaml`](../data/claim_ledger.yaml). Tests bind numeric and enum claims to generated artifacts so manuscript prose cannot drift from measured outputs.

## Claim table

| claim_id | Kind | Bound value | Artifact / source | Test module |
| --- | --- | --- | --- | --- |
| `format-version` | text | `0.4.0` | `src/crypto.py`, schema enum | `test_claim_ledger.py` |
| `tamper-detection-rate` | number | `1.0` | `output/reports/benchmark_validation.json` | `test_claim_ledger_security.py` |
| `container-verify-gate` | text | `verify_container` | benchmark ZIP under `output/data/_bench_tmp/` | `test_claim_ledger_security.py` |
| `figure-export-dpi` | number | `300` | `output/figures/` | `test_claim_ledger.py` |
| `master-key-bytes` | number | `32` | `src/crypto.py` | `test_claim_ledger.py` |
| `track-header-bytes` | number | `28` | nonce + tag (12 + 16) | `test_claim_ledger.py` |
| `test-coverage-min` | number | `90` | `pyproject.toml` | `test_claim_ledger.py` |
| `figure-display-width` | number | `90` | `manuscript/config.yaml` | `test_claim_ledger.py` |
| `crypto-backend-gcm` | text | `aes-256-gcm` | default write path `src/crypto.py` | `test_claim_ledger.py`, `test_crypto_gcm.py` |
| `container-verification-report` | text | `container_verification.json` | `output/reports/` | `test_claim_ledger_security.py`, `test_verification_report.py` |
| `figure-caption-registry` | text | `FIG_CAPTION_` | `src/figure_registry.py` | `test_figure_captions.py` |
| `figure-count` | number | `21` | `FIGURE_SPECS` / `output/figures/` | `test_figures.py`, `test_claim_ledger.py` |
| `evidence-provenance-boundary` | text | zero mocks, documented fixtures/vectors | `docs/evidence_provenance.md` | `test_evidence_provenance.py` |

## Adding a claim

1. Append an entry to `data/claim_ledger.yaml` with `claim_id`, `kind`, `value`, `source`, `artifact_path`.
2. Add or extend a test that reads the artifact and asserts the claim (no mocks).
3. Reference the claim in manuscript only via injected `{{TOKEN}}`s when applicable.

Evidence claims must not collapse fixture, synthetic, conformance-vector, and
executed-output classes into a single "real data" phrase. Use
[`evidence_provenance.md`](evidence_provenance.md) as the source of truth for
that boundary.

## Security claim bindings

| Claim | Gate |
| --- | --- |
| `tamper-detection-rate` | `benchmark_validation.json` → `tamper_detection_rate == 1.0` after `ento_analysis.py`. **Adversarial:** corrupts ciphertext and unpacks **with the key**, so it exercises real GCM authentication. |
| `container-verify-gate` | `container_verification.json` → all samples `ok: true` from `build_container_verification_report()`, run with `require_integrity=True`. **Keyless → `digest-only` integrity (accidental-corruption detection); NOT adversarial.** Adversarial integrity is the `tamper-detection-rate` (key-based) gate above. |
| `crypto-backend-gcm` | New packs use `format_version: 0.4.0` and GCM AEAD on write |

> **Integrity caveat.** The unkeyed manifest digests and proof chain detect corruption, not a
> motivated attacker (who recomputes them). `verify_container`'s `integrity` field reports the
> level actually achieved (`key-authenticated` / `digest-only` / `unverified`); see
> [`entofile-threat-model.md`](entofile-threat-model.md) "Integrity model".

See [`security.md`](security.md) and [`entofile-threat-model.md`](entofile-threat-model.md).
