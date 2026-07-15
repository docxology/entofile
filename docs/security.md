# Security operations — entofile

Operational guidance for ENTO key handling, container verification, and hostile-archive ingestion.

## Threat model reference

Full AppSec report: [`entofile-threat-model.md`](entofile-threat-model.md) (includes MITRE ATT&CK mapping). Manuscript: `manuscript/08_limitations_and_threat_model.md`, `manuscript/02c_security_verification.md`.

## First-principles security baseline

Start from the bytes an attacker can actually control:

| Boundary | Hard truth | Operational rule |
| --- | --- | --- |
| ZIP envelope | Member names, central-directory metadata, comments, and sizes are visible and attacker-supplied before validation | Treat every archive as hostile; run member-set, duplicate-name, and size gates before release of plaintext |
| Manifest/proof | JSON digests and hash chains are unkeyed unless externally signed | Use them for corruption detection and reproducibility, not origin authentication |
| Track payload | AES-GCM only proves authenticity when the correct master key and format-specific AAD are used [@rfc5116; @dworkin2007gcm; @mcgrew2004gcm] | Keyed `verify`/`unpack` is the adversarial integrity gate |
| Keys | Master keys are intentionally outside the ENTO ZIP | Store keys in operator-controlled KMS/HSM or locked-down files; apply key-management policy outside the file format [@nistsp80057pt1r5] |
| Length | ZIP_STORED preserves member size; default 0.4.0 and opt-in 0.5.0 pad only to PADMÉ buckets | Treat bucket size as visible; use external traffic controls when even bucket leakage is sensitive |
| Release artifacts | SBOMs and rendered PDFs are files an attacker can swap | Public releases need external signature/provenance policy, not just local checks |

## Master keys

| Rule | Implementation |
| --- | --- |
| 32-byte CSPRNG | `crypto.generate_master_key()` / CLI `genkey` |
| File permissions | `genkey` sets mode `0600` on Unix when supported |
| Separation | Keys are never embedded in ENTO ZIP files |
| Storage | Treat keys like SSH private keys; no world-readable paths |

```bash
uv run python -m src.cli genkey -o ./master.key
chmod 600 ./master.key   # redundant on Unix when genkey succeeds
```

Benchmark temp keys under `output/data/_bench_tmp/` are disposable pipeline artifacts.

## Cryptography (default 0.4.0, opt-in 0.5.0, plus compatibility formats)

| `format_version` | Write | Read | Module |
| --- | --- | --- | --- |
| `0.2.0` (compatibility) | AES-256-GCM, 16-byte nonce, no AAD | Yes | `src/crypto_gcm.py` |
| `0.3.0` (compatibility) | AES-256-GCM, 12-byte nonce, AAD binds `format_version`+`track_id` | Yes | `src/crypto_gcm.py` |
| `0.3.1` (compatibility + length-hiding) | 0.3.0 + PADMÉ plaintext padding (`src/padding.py`) | Yes | `src/crypto_gcm.py`, `src/track.py` |
| `0.4.0` (default) | 0.3.1 profile promoted as the default writer | Yes | `src/crypto_gcm.py`, `src/track.py` |
| `0.5.0` (opt-in) | 0.4.0 layout plus exported-manifest context in GCM AAD | Yes | `src/manifest_binding.py`, `src/crypto.py`, `src/container.py` |

Default `pack` writes `0.4.0`. Select `0.5.0` explicitly when every reader supports authenticated exported-manifest context, or select a compatibility format with `pack --format 0.2.0|0.3.0|0.3.1`. `pack_container(..., format_version=...)` exposes the same choice. Verify/unpack dispatch on the manifest's `format_version`, so existing 0.2.0/0.3.0/0.3.1/0.4.0 containers keep working unchanged.

The source `observability_level` is an upper bound on an export: `export_level`
may reduce metadata exposure, but cannot raise it. The pack APIs reject an attempted
SEALED-to-AUDITABLE (or equivalent) escalation instead of leaking fields retained in
the in-memory full manifest.

Facade: `src/crypto.py` — `encrypt_payload` / `decrypt_payload` dispatch on
`format_version` and reject unsupported versions. Per-track keys are
HKDF-SHA256 derived with `info = "ento:track:<id>"` via the vetted
`cryptography` HKDF (byte-identical to the prior hand-rolled loop; locked by
`data/test_vectors/hkdf_regression.json`) [@krawczyk2010hkdf; @nistfips1804].
HKDF gives each track a labelled subkey under the same master key, so a track
swap is checked under the wrong subkey and fails. The default 0.4.0 wire layout
is `nonce(12) || tag(16) || ciphertext`, with AAD
`ento:0.4.0:track:<track_id>` and a PADMÉ-padded plaintext body. The opt-in
0.5.0 layout uses `ento:0.5.0:manifest:<manifest_binding>:track:<track_id>`
and binds the canonical manifest view that is actually exported. AAD is
cleartext context authenticated by GCM; it is like a tamper-evident label on the
sealed payload, not extra plaintext hidden inside the ciphertext. The frozen
0.2.0 compatibility layout remains `nonce(16) || tag(16) || ciphertext` with no
AAD. Any GCM nonce reuse under one key would invalidate the authentication
bound, so ENTO relies on per-track HKDF separation and fresh random nonces
rather than counters [@joux2006forbidden; @bock2016nonce]. AES-GCM-SIV is the
standards-track nonce-misuse-resistant AEAD to evaluate for future formats when
fresh-nonce assumptions cannot be made operationally; it is not implemented in
the current default profile [@rfc8452].

Regression vectors: `data/test_vectors/hkdf_regression.json`, `aes256_gcm_regression.json`.

## Verify before unpack

```bash
uv run python -m src.cli verify -i container.ento.zip
uv run python -m src.cli verify -i container.ento.zip -k master.key
uv run python -m src.cli verify -i container.ento.zip --require-proof
```

On failure the CLI prints a JSON audit line to stderr. `unpack` performs the same integrity checks before writing plaintext.

**Integrity basis — verify with the key for adversarial assurance.** `verify_container`
returns an `integrity` field: `key-authenticated` (key supplied, GCM passed — the only
adversarial-strong level), `digest-only` (keyless, all ciphertext digests matched — detects
*accidental* corruption only), or `unverified` (keyless, digests absent). Keyless verify cannot
detect a motivated attacker, who can recompute or blank the unkeyed digests and proof chain.
Pass `require_integrity=True` to fail closed on `unverified`. The on-disk pipeline gate
`output/reports/container_verification.json` (from `src/verification_report.py`) is keyless and
therefore establishes `digest-only` integrity; adversarial tamper detection is proven separately
by the **key-based** benchmark (`tamper_detection_rate`, which decrypts and trips the GCM tag).

Pipeline gate: `output/reports/container_verification.json` from `src/verification_report.py` (see [`claim_ledger.md`](claim_ledger.md)).

## Safe output paths

Track IDs must match `^[a-z0-9._-]+$`. CLI `unpack` resolves outputs under `--output-dir` only.

## ZIP ingestion limits

| Limit | Value (`src/security.py`) |
| --- | --- |
| Max archive size | 256 MiB |
| Max member count | 256 |
| Max uncompressed member | 64 MiB (enforced on **actual** decompressed bytes via `safe_read_member`, not declared `file_size`) |
| Max aggregate uncompressed | 512 MiB |
| Max manifest.json | 4 MiB |

`ZipInfo.file_size` is attacker metadata, so members are read through `safe_read_member`, which
bounds the real decompressed stream — a highly compressible member cannot fan out past the cap.
This is the ZIP/data-amplification class captured by CWE-409 [@cwe409].
`validate_zip_archive` additionally rejects declared per-member and aggregate overflow up front.

For padded formats, decoding also requires the canonical PADMÉ bucket and zero-filled
tail. GCM authenticates the padding bytes, but canonical decoding prevents a validly
authenticated producer from creating alternate encodings that the reader would accept.

Conformance verification binds each manifest entry to the code-defined version/attack
matrix and recomputes the fixture size and SHA-256. The manifest is an index, not an
authority for its own expected outcomes.

## Observability and leakage

| Level | Proof | Plaintext digests in manifest |
| --- | --- | --- |
| 0 (sealed) | Omitted | Omitted (and manifest `byte_length` zeroed) |
| 1–3 | Present (1–3) | Level 3 exposes SHA-256 plaintext hashes |

**Exact-length hiding is now the default, but bucket size remains visible.** At 0.2.0/0.3.0,
SEALED zeroes the manifest-declared `byte_length`, but AES-GCM is length-preserving and
containers are ZIP_STORED, so each track's plaintext length is recoverable from its on-disk
member size. Formats 0.3.1, 0.4.0, and 0.5.0 PADMÉ-pad the plaintext so the member size reveals only a
coarse bucket; this mitigates exact-length disclosure, not all size or traffic analysis.

## Supply chain (optional)

```bash
uv run python scripts/export_sbom.py
```

Writes `output/reports/sbom.cyclonedx.json` (CycloneDX skeleton from `uv export`). Not part of the default core pipeline unless enabled in release profile.

For the planned public repository (`https://github.com/docxology/entofile`),
release operators should sign the source archive, wheels/sdists if produced,
SBOM, rendered PDF, and validation reports with Sigstore/cosign, in-toto/SLSA,
or equivalent controls aligned with supply-chain-risk guidance [@nist2022sp800161r1;
@torresarias2019intoto; @slsa2024levels; @sigstore2026cosign].
Those signatures are deliberately external to the offline reference container:
ENTO can verify a container's keyed track integrity, but it does not certify who
built the release bundle. COSE is a standards-track option for detached signing
metadata when operators need a compact CBOR-based provenance envelope [@rfc9052].

## Residual gaps

- No HSM/KMS integration or artifact signing in-repo
- ZIP comment/metadata not authenticated
- No replay/timestamp binding on manifests
- Keyless verification is corruption-detection only; the manifest and proof chain are unkeyed
  (an attacker who controls the bytes can recompute them) — adversarial integrity requires the key
- Aggregate decompression is bounded per-member (actual bytes) and by a declared-size aggregate
  cap; a crafted archive of many members that each under-declare size is still bounded by
  `member_count × per-member` actual-byte caps — tune `MAX_*_UNCOMPRESSED` down for hostile inputs

See [`nation_state_roadmap.md`](nation_state_roadmap.md) for the 0.4 RC deployment matrix.

## API

```python
from src.container import verify_container
from src.security import validate_track_id, safe_output_path
from src.verification_report import build_container_verification_report

verify_container(path)                          # keyless -> integrity: "digest-only" or "unverified"
verify_container(path, master_key)              # keyed   -> integrity: "key-authenticated"
verify_container(path, require_integrity=True)  # fail closed (ok=False) on "unverified"
```
