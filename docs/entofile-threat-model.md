# entofile threat model

AppSec-oriented threat model for ENTO (`projects/working/entofile`). Only `format_version` **0.5.0** is accepted: AES-256-GCM with AAD, mandatory PADMÉ padding, and authenticated exported-manifest context. Every other wire version is rejected.

## Executive summary

ENTO is an offline CLI/library for encrypted research ZIP containers. Top risks are **hostile-archive ingestion** (ZIP/member tampering, path escape via track IDs), **integrity bypass**, and **operational key handling** (no in-repo HSM/signing). The 0.5.0 read/write path uses audited AEAD (`cryptography`); residual gaps include unsigned ZIP metadata, visible padded bucket sizes, optional proof at level 0, and no replay timestamps.

### Integrity model — what actually authenticates (read first)

**The master key (AES-256-GCM) is the only adversarial integrity anchor** [@nistfips197; @rfc5116; @dworkin2007gcm; @mcgrew2004gcm]. Decrypting a
track under the key authenticates that ciphertext; any tamper fails the GCM tag. The track key
is HKDF-derived with `info = "ento:track:<id>"`, so a ciphertext swapped to a different track
fails to decrypt — track context is bound implicitly through key derivation.

Everything ENTO can check **without** the key is *corruption detection only, not adversarial
authentication*:

- **Manifest `sha256_*` digests** are unkeyed and live in an unauthenticated manifest. An
  attacker who rewrites the container recomputes them (or blanks them — the schema permits
  empty digests for redacted exports).
- **The proof chain** is an unkeyed SHA-256 hash chain. It binds a proof to a given
  `manifest.json` and detects accidental edits, but carries **no secret**, so any party that
  controls the bytes can regenerate a self-consistent chain. It is a transparency/consistency
  structure, **not** a signature of origin.

`verify_container` reports this explicitly via its `integrity` field:
`"key-authenticated"` (key supplied, GCM passed), `"digest-only"` (keyless, digests present and
matched — corruption detection), or `"unverified"` (keyless, digests absent). Pass
`require_integrity=True` to fail closed on `"unverified"`. For adversarial assurance, always
verify (or unpack) **with the key**.

### Current wire profile

ENTO 0.5.0 is the only accepted format. The `pack` CLI has no format selector,
and readers reject every other manifest version. Each track uses a fresh random
96-bit (12-byte) GCM nonce and AAD of
`ento:0.5.0:manifest:{manifest_binding}:track:{track_id}`. This binds the format,
track id, and exported manifest projection to the authentication tag. The public
binding is not a signature of origin.

Every plaintext is length-prefixed and padded to a canonical PADMÉ bucket before
encryption [@nikitin2019purb]. Keyed verification authenticates the padding and
metadata context; keyless binding checks remain corruption detection only.
Nonce reuse under one key is catastrophic, so fresh CSPRNG draws and per-track
HKDF separation are mandatory [@joux2006forbidden; @bock2016nonce].
AES-GCM-SIV is a possible separate research direction when deployments cannot
bound nonce uniqueness, but ENTO does not implement it [@rfc8452].

## Scope and assumptions

**In scope:** `src/` (crypto, container, CLI, manifest, proof, security), `scripts/ento_cli.py`, `data/ento_manifest_schema.json`, benchmark/analysis pipeline writing local files.

**Out of scope:** Layer 1 template CI, Ollama/LLM stages, network services, Zenodo deposit automation.

**Assumptions (validate for your deployment):**

- Operators run CLI locally on researcher workstations or batch nodes.
- Untrusted `.ento.zip` files may arrive from collaborators or public mirrors.
- Master keys are out-of-band secrets; ENTO does not provide escrow,
  cryptoperiod policy, or HSM/KMS custody [@nistsp80057pt1r5].
- Internet exposure: none (no listening ports).

**Open questions:** multi-tenant hosting, centralized key vault, mandatory artifact signing policy.

## System model

### Primary components

| Component | Role | Evidence |
| --- | --- | --- |
| CLI | genkey, pack, unpack, verify, inspect, proof | `src/cli.py` |
| Container | ZIP pack/unpack/verify | `src/container.py` |
| Crypto | HKDF, AES-256-GCM AEAD | `src/crypto.py`, `src/crypto_gcm.py` |
| Verification report | Per-container verify JSON | `src/verification_report.py` |
| Manifest | JSON Schema validation | `src/manifest.py`, `data/ento_manifest_schema.json` |
| Security | Track ID policy, ZIP limits, safe paths | `src/security.py` |
| Analysis | Benchmarks → figures (local I/O) | `src/analysis.py` |

### Data flows and trust boundaries

- **Operator → CLI:** key file, fixture dir, container path, output dir — local filesystem, no auth layer.
- **Publisher → recipient:** ENTO ZIP (manifest + encrypted tracks [+ proof]) — confidentiality from AES-256-GCM; adversarial integrity from GCM AEAD on key-based verify (the unkeyed digests/proof are corruption checks only).
- **Untrusted ZIP → verify/unpack:** attacker-controlled archive bytes — must fail closed (`verify_container`, `unpack_container`).

#### Diagram

```mermaid
flowchart LR
  subgraph operator
    KEY["Master key file"]
    CLI["CLI"]
  end
  subgraph untrusted
    ZIP["ENTO ZIP archive"]
  end
  subgraph host
    OUT["Plaintext output dir"]
  end
  KEY --> CLI
  ZIP --> CLI
  CLI --> OUT
```

## Assets and security objectives

| Asset | Why it matters | Objective |
| --- | --- | --- |
| Master key | Decrypts all tracks | C |
| Plaintext tracks | Research data | C, I |
| Manifest metadata | Types, digests, observability | C, I |
| Proof chain | Manifest binding | I |
| Host filesystem | CLI output paths | I, A |

## Attacker model

### Capabilities

- Supply malicious or tampered ENTO ZIP files.
- Read sealed manifests without key (metadata/filename leakage).
- Local access to run CLI with operator privileges.

### Non-capabilities

- Remote exploitation without operator executing CLI on the archive (no network daemon).
- Break AES-256-GCM or HKDF-SHA256 without key or implementation flaw (assumed out of scope for this reference).

## Entry points and attack surfaces

| Surface | How reached | Trust boundary | Notes | Evidence |
| --- | --- | --- | --- | --- |
| CLI argv/paths | Shell | Operator ↔ host FS | Paths user-supplied | `src/cli.py` |
| ZIP read | `-i container` | Untrusted → parser | zipfile + limits | `src/security.py` |
| manifest.json | Inside ZIP | Untrusted → jsonschema | Schema + track id pattern | `data/ento_manifest_schema.json` |
| Track blobs | `tracks/*.ento` | Untrusted → crypto | GCM AEAD authenticates at decrypt | `src/crypto.py`, `src/crypto_gcm.py` |
| Key file | `-k` | Operator secret | 32-byte check | `src/cli.py:_load_key` |

## Top abuse paths

1. **Path escape on unpack** — Malicious manifest track id `../../etc/passwd` → write outside output dir (CWE-22) → **Mitigated:** `validate_track_id`, `safe_output_path` (`src/security.py`, `src/cli.py`) [@cwe22].
2. **Ciphertext swap** — Replace track blob, keep manifest → decrypt wrong data → **Mitigated (key-based):** GCM authentication fails on `unpack_container` / keyed `verify_container`. The keyless `sha256_ciphertext` check only detects accidental corruption — an attacker recomputes or blanks the digest (`src/container.py`).
3. **Manifest swap** — Alter manifest.json → **Partially mitigated:** `verify_proof_export` detects a manifest that no longer matches its proof, but the proof is **unkeyed** and the attacker regenerates it. Adversarial detection of a manifest swap still relies on key-based decryption mismatching the rewritten descriptors (`src/proof.py`, `src/container.py`).
4. **ZIP bomb** — Oversized members → DoS / data amplification (CWE-409) → **Mitigated:** size limits (`src/security.py`) [@cwe409].
5. **Extra member injection** — Hidden tracks/malware file in ZIP → **Mitigated:** member-set equality check (`assert_zip_members_match_manifest`).
6. **Key exfil via world-readable genkey** — Local user reads key → **Partially mitigated:** `chmod 0600` on genkey; operator discipline required.
7. **Sealed export metadata leak** — Level 0 still exposes track filenames in ZIP → Residual risk documented in manuscript §08.
8. **Sealed plaintext-length disclosure** — ENTO 0.5.0 PADMÉ-pads every plaintext, so the on-disk member size reveals a bucket rather than exact length. Non-sealed manifests still expose `byte_length`, and bucket size remains visible even under SEALED export; both are residual metadata.

## Threat model table

| ID | Threat | Impact | Controls (evidence) | Gaps | Mitigations | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| TM-001 | Path escape via track id [@cwe22] | Host file write | `validate_track_id`, `safe_output_path` | None in v0.1.1+ | Keep schema pattern aligned | medium |
| TM-002 | Ciphertext tamper | Wrong/malicious plaintext | GCM AEAD on key-based unpack/verify; keyless digest = corruption-detection only | Keyless verify is NOT adversarial; digests are blankable/recomputable | Verify/unpack **with the key**; `require_integrity=True` to reject unverified | high |
| TM-003 | Manifest/proof mismatch | Undetected swap | `verify_proof_export` (consistency only); key-based descriptor mismatch | Proof chain is **unkeyed** → attacker regenerates it; proof omitted at level 0 | Key-based verify; external signing for origin authentication | high |
| TM-004 | ZIP bomb / DoS [@cwe409] | Availability | Size/member limits | Defaults may be high for some envs | Tune limits | medium |
| TM-005 | Weak crypto implementation | Confidentiality break | GCM regression vectors + tamper benchmarks | Not FIPS-validated deployment | HSM + FIPS module selection | medium |
| TM-006 | No artifact signing | Supply-chain swap | Optional CycloneDX SBOM via `scripts/export_sbom.py` | No in-repo Sigstore/provenance policy | Sign releases and SBOMs externally using NIST C-SCRM / SLSA / in-toto style controls [@nist2022sp800161r1; @slsa2024levels; @torresarias2019intoto] | medium |
| TM-007 | Key mishandling | Key theft | genkey CSPRNG, chmod 600 | No HSM/KMS or cryptoperiod policy | KMS/HSM integration and key-management policy outside the file format [@nistsp80057pt1r5] | high |
| TM-008 | Sealed plaintext-length disclosure | Metadata inference | Mandatory ENTO `0.5.0` PADMÉ padding; sealed export zeroes `byte_length` | Bucket size remains visible; non-sealed manifests disclose exact length | Use sealed export and external traffic controls when bucket leakage is sensitive | medium |

## Criticality calibration

- **Critical:** Pre-auth RCE — N/A (CLI only).
- **High:** Integrity bypass on unpack, key theft from world-readable files, custom crypto break.
- **Medium:** ZIP DoS, metadata leakage at sealed export, missing proof on audit paths.
- **Low:** Informational manifest fields at level 3 without key.

## Focus paths for security review

| Path | Why | Threat IDs |
| --- | --- | --- |
| `src/container.py` | Verify/unpack orchestration | TM-002, TM-003 |
| `src/security.py` | ID policy, ZIP limits | TM-001, TM-004 |
| `src/crypto.py` | Custom crypto surface | TM-005 |
| `src/padding.py` | Length-hiding padding | TM-008 |
| `src/cli.py` | Operator entrypoints | TM-001, TM-007 |
| `src/proof.py` | Manifest binding | TM-003 |
| `data/ento_manifest_schema.json` | Input validation contract | TM-001 |

## MITRE ATT&CK mapping (lightweight)

| Technique | Name | ENTO control | Evidence |
| --- | --- | --- | --- |
| T1565.001 | Stored data manipulation | GCM AEAD on key-based verify/unpack (digests are corruption-detection only) | `verify_container(key=...)`, `decrypt_track` |
| T1499 | Endpoint denial of service | ZIP size/member limits | `validate_zip_archive` |
| T1083 | File and directory discovery | Sealed observability redaction | `filter_manifest` level 0 |
| T1005 | Data from local system | Safe unpack paths | `validate_track_id`, `safe_output_path` |
| T1552.001 | Credentials in files | `genkey` chmod 0600 | `src/cli.py` genkey |
| T1190 | Exploit public-facing app | N/A | No network service |

Mapping is illustrative for offline CLI scope—not a FedRAMP control baseline.

## Quality check

- Entry points: CLI, ZIP, manifest, key file — covered.
- Trust boundaries: operator/untrusted/host — in diagram and flows.
- Runtime vs CI: analysis pipeline local-only; CI runs tests without production keys.
- Assumptions: documented above; confirm deployment model with service owner.
