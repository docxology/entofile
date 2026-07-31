# Adversarial Premortem + Devil's Advocate — entofile crypto/container core

**Date:** 2026-07-31
**Scope:** `src/crypto.py`, `src/crypto_gcm.py`, `src/container.py`, `src/security.py`,
`src/verification_report.py`, `src/padding.py`, `src/proof.py`, `src/track.py`,
`src/manifest.py`, `src/manifest_binding.py`, `src/observability.py`, `src/models.py`
**Method:** Source review + 24 adversarial probe scripts (executed against real code, zero mocks)
**Baseline:** 56 security/crypto tests pass; 448 total tests pass; 90.34% coverage

---

## BLUF

The 0.5.0 format (the default) is cryptographically sound: manifest_binding is
recomputed and verified on every read, GCM AAD binds format_version + track_id +
manifest context, nonces are fresh per call, format downgrades fail closed, and
padding is inside the authenticated envelope (no padding oracle). The historical
F1 (keyless verify returning ok:True with corrupted ciphertext) is genuinely
fixed — `require_integrity=True` is enforced by all shipped entrypoints.

**The silent failure modes that passed 448 tests live in the pre-0.5.0
compatibility surface and the library API defaults.** An attacker controlling a
0.2.0–0.4.0 container can freely mutate manifest metadata (observability_level,
creator, created) without breaking `key-authenticated` verification, because
those fields are outside the GCM AAD and there is no manifest binding. The
project is aware of this (it is documented and one test explicitly asserts the
downgrade produces `key-authenticated`), but a library consumer who treats
`verify_container(..., key)` as a full integrity guarantee on a legacy container
gets metadata-tampered results reported as authentic.

---

## Findings Table

| # | Finding | Severity | Confidence | Evidence (file:line) |
|---|---------|----------|------------|---------------------|
| F1 | **Pre-0.5.0 manifest metadata is unauthenticated** — attacker can set arbitrary observability_level / creator / created on 0.2.0–0.4.0 containers; keyed verify still reports `key-authenticated` with tampered metadata | **Medium** | **High** | `container.py:84-100` (AAD excludes obs/creator for <0.5.0); `manifest_binding.py:77` (binding only for 0.5.0); probes 01/09/15/16; `test_security_review_hardening.py:118-153` (explicitly accepts this) |
| F2 | **`require_integrity=False` default returns `ok:True` for unverified containers** — a library caller using defaults gets `ok:True` with `integrity:"unverified"` for a digest-stripped/forged container; the `ok` field means "structural validity", not integrity | **Medium** | **High** | `container.py:224,297`; probes 03/18; `test_container_security.py:32-37` (asserts ok:True keyless) |
| F3 | **Digest comparisons use `!=` not `hmac.compare_digest`** — ciphertext and plaintext digest checks in `verify_container` and `_verify_ciphertext_hashes` use plain string `!=`, a potential timing side channel; manifest_binding correctly uses `hmac.compare_digest` | **Low** | **High** | `container.py:148` (`digest != entry.sha256_ciphertext`); `container.py:278` (`digest != entry.sha256_plaintext`); `manifest_binding.py:83` (uses `compare_digest`); probe 19 |
| F4 | **`_nonce` parameter accessible on public `encrypt_payload`** — the test-only nonce injection knob is underscore-prefixed and documented, but is a public parameter on `crypto.encrypt_payload` and `crypto_gcm.encrypt_payload`; a caller who passes a fixed nonce with the same key gets catastrophic GCM nonce reuse | **Low** | **High** | `crypto.py:149`; `crypto_gcm.py:27,42` |
| F5 | **`inspect_container` returns manifest with zero integrity checks** — a ciphertext-corrupted or metadata-tampered container's manifest is returned without any verification; documented as by-design but a consumer that trusts `inspect` output gets unvalidated metadata | **Low** | **High** | `container.py:485-488` (`integrity="manifest_only"`); probe 08 |
| F6 | **ZIP aggregate cap uses `>` not `>=`** — `MAX_TOTAL_UNCOMPRESSED` check is `declared_total > MAX_TOTAL_UNCOMPRESSED`, so exactly 512 MiB passes; 8 members × 64 MiB = 512 MiB is within bounds but allocates 512 MiB of memory | **Low** | **Moderate** | `security.py:70` |
| F7 | **Empty 0.2.0–0.4.0 container verifies `ok:True` with default `require_integrity`** — a container with zero tracks has `digests_present=False` → `integrity:"unverified"`, but `ok=True` under the default; `require_integrity=True` correctly fails closed | **Low** | **High** | `container.py:96-100` (`bool(manifest.tracks)` → False); probe 17/18 |

---

## Non-Findings (verified solid)

| Hypothesis | Verdict | Evidence |
|-----------|---------|----------|
| Nonce reuse in production path | **Not vulnerable** — `encrypt_track` never passes `_nonce`; `secrets.token_bytes` draws fresh per call | probe 05; `track.py:25-31` |
| Format downgrade 0.5.0→0.4.0 | **Not vulnerable** — AAD string includes format_version; changing it breaks GCM auth | probe 06 |
| Padding oracle | **Not vulnerable** — PADMÉ padding is inside the GCM authenticated envelope; attacker cannot modify padding without breaking auth | `padding.py:41-69`; `track.py:24` |
| Manifest binding not recomputed on verify | **Not vulnerable** — `manifest_from_json` → `validate_manifest_binding` recomputes via `compute_manifest_binding` and uses `hmac.compare_digest` | `manifest.py:66`; `manifest_binding.py:82-83`; probe 02/14 |
| GCM auth bypassed by matching ciphertext digest | **Not vulnerable** — GCM decrypt is always attempted in keyed path; ciphertext tamper with recomputed digest still fails auth | probe 23 |
| Duplicate ZIP members (parser differential) | **Not vulnerable** — `validate_zip_member_names` rejects duplicates up front | `security.py:111-113`; probe 13 |
| Verify-before-unpack enforcement | **Not vulnerable** — `unpack_container` uses `_with_verified_container(integrity="full")` which runs ZIP + manifest + digest + proof checks before yielding | `container.py:460` |
| Keyless wrong ciphertext digest | **Not vulnerable** — `_verify_ciphertext_hashes` catches mismatched digests | probe 24 |
| HKDF hand-rolled vs library | **Not vulnerable** — delegates to `cryptography.hazmat.primitives.kdf.hkdf.HKDF`; byte-pinned by test vectors | `crypto.py:122-127`; `test_security_review_hardening.py:239-250` |
| SEALED→AUDITABLE upgrade bypass | **Not vulnerable** — byte_length reconcile catches `0 != len(plaintext)` for AUDITABLE | probe 11 |

---

## Ranked Failure Modes (Premortem)

### FM-1: Pre-0.5.0 metadata tamper passes key-authenticated (F1)

**Plausibility: 8/10 × Impact: 5/10 = 40**

**Narrative:** A research pipeline receives a legacy 0.4.0 container from a
collaborator. An intermediary (compromised storage, MITM) rewrites the
`observability_level` from AUDITABLE (3) to SEALED (0) and sets `byte_length=0`
on all tracks. The pipeline calls `verify_container(path, key,
require_integrity=True)`. GCM auth passes (ciphertext is unchanged). The
`_reconcile_byte_length` SEALED branch checks `byte_length == 0` — it passes.
The pipeline sees `integrity:"key-authenticated"`, `observability_level:0`, and
treats the container as SEALED when it is actually AUDITABLE. Downstream logic
that filters on observability level misroutes the data.

**Leading indicator:** A 0.4.0 container reporting `observability_level` that
disagrees with the export level used at pack time.

**Mitigation:** Require 0.5.0 for all new containers (the manifest_binding
authenticates the full manifest context). For legacy containers, document that
metadata fields are unauthenticated and should not be used for access-control
decisions.

### FM-2: Library caller trusts `ok:True` as integrity (F2)

**Plausibility: 7/10 × Impact: 6/10 = 42**

**Narrative:** A library consumer calls `verify_container(path)` (no key,
default `require_integrity=False`) on a digest-stripped container. The result
is `{"ok": True, "integrity": "unverified"}`. The consumer checks only `ok`
and proceeds to unpack, treating the container as verified. The docstring warns
about this, but the default is the footgun — the shipped CLI sets
`require_integrity=True` but the library API does not.

**Leading indicator:** A consumer that checks `result["ok"]` without checking
`result["integrity"]` or passing `require_integrity=True`.

**Mitigation:** Change `require_integrity` default to `True` (breaking change
for structural-only callers, who can pass `False` explicitly). Or deprecate
`ok` in favor of `integrity` as the primary field.

### FM-3: Timing side channel on digest comparison (F3)

**Plausibility: 3/10 × Impact: 4/10 = 12**

**Narrative:** An attacker co-located with the verifier can observe timing of
the `!=` comparison on `sha256_plaintext` to recover the hash of the plaintext
byte-by-byte. This requires ~16384 carefully-timed verification calls. The
practical exploitability is very low (co-location required, nanosecond
precision), but the fix is trivial (`hmac.compare_digest`).

**Mitigation:** Replace `digest != entry.sha256_*` with
`not hmac.compare_digest(digest, entry.sha256_*)` in `container.py`.

---

## Claim-by-Claim Counter-Case

### Claim: "Keyless verify is explicitly documented as corruption-detection only (not adversarial integrity)"

**Counter-case:** True and enforced. `verify_container` with no key reports
`"digest-only"` or `"unverified"`, never `"key-authenticated"`. The negative
control in `verification_report.py:71-142` crafts a digest-stripped container
and asserts keyless fail-closed rejection. The integrity level is derived from
the decrypt attempt, not from a manifest field. **Verdict: Survived.**

### Claim: "448 tests passing, zero mocks, clean ruff/mypy"

**Counter-case:** True. All 56 security/crypto tests pass. The no-mocks claim
is verified — probes build real containers and exercise real code paths. But
the test suite has a **positive-control-only** blind spot for F1: the test at
`test_security_review_hardening.py:118-153` asserts the downgrade produces
`key-authenticated` — it tests that integrity is NOT downgraded, but does not
flag that metadata IS wrong. No test asserts that `observability_level` in the
result matches the original pack-time value for 0.4.0. **Verdict: Partially
refuted — tests pass but don't cover the metadata-tamper finding.**

### Claim: "Hand-rolled HKDF proven byte-identical to cryptography.io's"

**Counter-case:** True — the code now DELEGATES to `cryptography.hazmat.primitives.kdf.hkdf.HKDF`
(`crypto.py:122-127`), so there is no hand-rolled HKDF in production. The
byte-pin test (`test_security_review_hardening.py:239-250`) locks the output.
**Verdict: Survived.**

### Claim: "PADMÉ length padding prevents length leakage"

**Counter-case:** Partially true. PADMÉ pads to coarse buckets, hiding exact
length. But the observability.py docstring (line 39-42) honestly notes: "this
does NOT fully hide length — AES-GCM is length-preserving and the container is
ZIP_STORED, so plaintext length is still recoverable from the on-disk track
member size." PADMÉ hides exact length, not bucket size. **Verdict: Survived
(claim is already qualified).**

---

## Next Discriminating Checks

1. **F1 — Does any downstream consumer make access-control or routing decisions
   based on `observability_level` from a pre-0.5.0 container?** If yes, this
   escalates to HIGH. Grep for `observability_level` in analysis/pipeline code.
2. **F2 — Are there library consumers (outside the CLI) calling
   `verify_container` without `require_integrity=True`?** If yes, this escalates
   to HIGH. Grep for `verify_container(` in non-test code.
3. **F3 — Is the verifier exposed over a network where an attacker can make
   high-frequency timing observations?** If yes, this escalates to MEDIUM.

---

## Confidence Assessment

**HIGH** — All findings were confirmed by executing adversarial probe scripts
against the real codebase (not static analysis alone). 24 probes were run,
covering nonce reuse, format downgrade, manifest tampering (0.4.0 and 0.5.0),
observability level manipulation, digest stripping, ZIP bomb, duplicate members,
empty containers, timing comparison, and unpack-before-verify. The baseline test
suite (56 security tests) was run and passes, confirming the findings are not
already caught by existing tests.

The analysis cannot determine: (1) whether downstream consumers exist that trust
pre-0.5.0 metadata for security decisions, (2) whether the `require_integrity`
default has caused issues in real library usage, (3) the network exposure of
the verifier for timing attack assessment.
