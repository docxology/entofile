---
project: entofile
task: ENTO stable 0.4.0 plus opt-in 0.5.0 authenticated manifest context
effort: E4
phase: build
progress: current 0.5.0 implementation validated; landing and certifying publication retry pending
mode: algorithm
started: 2026-05-28
updated: 2026-07-15
---

# ISA — entofile historical 0.2.0 hardening log

> Historical note: this file records the 2026-05-28 to 2026-05-29 hardening
> sequence that began with ENTO format 0.2.0. It is not current release
> guidance. The 0.4 paper release candidate uses wire format 0.4.0 as the
> default while retaining 0.2.0, 0.3.0, and 0.3.1 as compatibility formats.

## Problem

At the time this historical log began, entofile targeted the DOI concept
10.5281/zenodo.20396329 and the ENTO 0.2.0 reference implementation. Its
**key-based** path was adversarially sound
(AES-256-GCM authenticates on `unpack_container` and keyed `verify_container`). However a
deep review found a HIGH-severity honesty/fail-open defect plus hardening gaps:

- **F1 (HIGH, reproduced):** keyless `verify_container` returns `{ok: True}` — *even with
  `require_proof=True`* — for a container whose ciphertext was corrupted, whose manifest
  digests were blanked (schema permits empty digests), and whose proof chain was forged.
  The proof chain is **unkeyed** (a plain SHA-256 hash chain), so any party that controls
  the bytes can recompute a self-consistent proof. The threat model (TM-002/TM-003) and
  `claim_ledger` (`container-verify-gate`) present keyless verify as tamper mitigation; it
  detects only *accidental corruption*, never an adversary.
- **F4 (MED, reproduced):** `validate_zip_archive` enforces `MAX_MEMBER_UNCOMPRESSED`
  against the attacker-controlled *declared* `ZipInfo.file_size`; `zf.read()` decompresses
  fully regardless (a 1026× ratio member passes), and there is no aggregate uncompressed cap.
- **F8 (MED):** HKDF is hand-rolled — exactly the custom-crypto surface TM-005 flags.
  Proven byte-identical to `cryptography`'s vetted HKDF across all test vectors.
- **F5 (LOW):** `crypto_gcm.decrypt_payload` catches every `Exception` as "tag mismatch",
  masking non-crypto errors.

## Vision

A reviewer who knows AEAD reads `verify_container`'s result and *instantly* knows what was
actually proven — "digest-only, corruption-detection" vs "key-authenticated" — with no way
to mistake an unkeyed consistency check for adversarial integrity. The hardening closes the
zip-bomb headroom and shrinks the custom-crypto surface without breaking a single published
container.

## Out of Scope

- **Historical round: no wire-format change.** Format 0.2.0 was frozen for
  that compatibility-hardening pass. The 16-byte GCM nonce and the absence of
  AAD were documented with rationale rather than altered, because changing
  either would fail to decrypt existing 0.2.0 containers. Later rounds added
  0.3.0, 0.3.1, and the current default 0.4.0 profile.
- No new crypto primitives, no signing/PKI (the threat model already lists artifact signing
  as out-of-repo).
- No manuscript/figure/viz refactors beyond what a doc-honesty fix requires.

## Principles

- **Truth in verification.** A verification function must never report more assurance than it
  computed. `ok` must not conflate "well-formed" with "integrity-verified".
- **The key is the only integrity anchor.** Unkeyed structures (manifest digests, proof
  chain) detect corruption, not adversaries. Say so.
- **Reduce custom-crypto surface** when a vetted primitive is byte-identical.
- **Fail closed** on attacker-controlled inputs (declared sizes, blankable fields).
- Backward compatibility with every existing 0.2.0 container is a hard constraint.

## Constraints

- INV-1: every currently-passing container (AUDITABLE fixtures, benchmark samples) must still
  verify `ok:True` after the change.
- INV-2: HKDF output must remain byte-identical (proven across 4 ikm × 4 info × 4 length vectors).
- INV-3: baseline = 142 tests / 92.05% coverage; must stay ≥ 90% project floor and all green.
- INV-4: no edit to the 0.2.0 nonce size (16), tag size (16), or AEAD suite.
- INV-5: ruff + mypy(strict) clean.

## Goal

Make keyless verification honest and fail-closed, harden zip ingestion against declared-size
bombs, swap to vetted HKDF byte-identically, and correct the threat-model/claim-ledger
overclaims — with zero wire-format change and the full gate green.

## Criteria

- [x] ISC-1: A container with corrupted ciphertext + blanked digests + forged proof, passed to
  keyless `verify_container`, does NOT report adversarial integrity (`integrity != "key-authenticated"`).
- [x] ISC-2: `verify_container` return includes an `integrity` field with values
  `"key-authenticated" | "digest-only" | "unverified"` reflecting what was actually checked.
- [x] ISC-3: `verify_container(..., require_integrity=True)` returns `ok:False` when no
  ciphertext digests are present and no key was supplied (fail-closed).
- [x] ISC-4: keyed `verify_container` on an intact container reports `integrity == "key-authenticated"`.
- [x] ISC-5: legit AUDITABLE container (digests present, no key) reports `integrity == "digest-only"` and `ok:True`.
- [x] ISC-6: empty `sha256_ciphertext` in full mode is recorded as undigested, not silently skipped.
- [x] ISC-7: a single ZIP member that decompresses past `MAX_MEMBER_UNCOMPRESSED` is rejected even when its declared `file_size` is small.
- [x] ISC-8: aggregate uncompressed bytes across members past a new cap is rejected.
- [x] ISC-9: HKDF swapped to `cryptography.HKDF`; a regression test pins byte-identity to the prior implementation's known vectors.
- [x] ISC-10: `crypto_gcm.decrypt_payload` catches `InvalidTag` specifically; a non-crypto bug is not relabeled "tag mismatch".
- [x] ISC-11: threat model TM-002/TM-003 state keyless verify detects corruption only; adversarial integrity requires the key.
- [x] ISC-12: docs document the 16-byte nonce and no-AAD rationale (HKDF `info` binds track_id).
- [x] ISC-13: claim_ledger / claim_ledger.yaml note that `container-verify-gate` is digest-only unless keyed.
- [x] ISC-14: full `pytest --cov` green, coverage ≥ 90% on src.
- [x] ISC-15: ruff check + format clean.
- [x] ISC-16: mypy clean on all changed src files (5/5). Pre-existing `ontology.py:65` error remains in an untouched file — out of scope, not a regression (documented, not over-claimed).
- [x] ISC-17: Anti: no existing 0.2.0 container fails to round-trip (INV-1) after changes.
- [x] ISC-18: Anti: `ok:True` is never returned for a keyless verify of a digest-stripped container under `require_integrity=True`.

## Test Strategy

| isc | type | check | threshold | tool |
|-----|------|-------|-----------|------|
| ISC-1,3,6,18 | adversarial | forged-proof+blanked-digest container | integrity not key-auth; ok False under require_integrity | pytest |
| ISC-2,4,5 | contract | integrity field values | exact strings | pytest |
| ISC-7,8 | bomb | high-ratio + aggregate members | ValueError raised | pytest |
| ISC-9 | regression | HKDF vector identity | byte-equal | pytest |
| ISC-10 | unit | InvalidTag only | raises ValueError, type narrowed | pytest |
| ISC-14,15,16 | gate | pytest/ruff/mypy | green, ≥90% | bash |
| ISC-17 | regression | round-trip all fixtures + levels | equal | pytest |

## Features

| name | satisfies | depends_on | parallelizable |
|------|-----------|------------|----------------|
| verify-honesty | ISC-1..6,18 | — | yes |
| zip-bomb-hardening | ISC-7,8 | — | yes |
| vetted-hkdf | ISC-9,17 | — | yes |
| narrow-exception | ISC-10 | — | yes |
| docs-honesty | ISC-11,12,13 | verify-honesty | yes |
| gate | ISC-14,15,16,17 | all | no |

## Decisions

- 2026-05-28: effort E4 (classifier timed out → fail-safe E3; escalated — cryptographic
  container under "deeply review and greatly improve" warrants adversarial review + cross-vendor audit). effort_source: context-override.
- 2026-05-28: wire format frozen. Nonce(16)/no-AAD documented not changed (INV-4) — DOI-published.
- 2026-05-28: F8 swap authorized because HKDF proven byte-identical (INV-2); otherwise would
  have kept hand-rolled and only added the vector-lock test.

## Changelog

- conjecture: keyless verify mitigates tamper (per TM-002/TM-003).
  refuted-by: reproduction — forged proof + blanked digests + corrupted ciphertext → ok:True.
  learned: unkeyed proof chain authenticates nothing; the master key (GCM) is the sole
  adversarial integrity anchor. criterion-now: ISC-1..6.
- 2026-05-28 ROUND 2 (0.3.0 + comprehensive RedTeam):
  - added: opt-in format **0.3.0** = 96-bit nonce + AAD binding `format_version`+`track_id`;
    0.2.0 remained the default in that historical round and stayed readable via
    version dispatch. 171 tests / 92.80%.
  - conjecture: member-set equality prevents extra-member injection.
    refuted-by: RedTeam V-D — `set(names)` collapses a DUPLICATE member name; `zf.open` reads
    the last copy → smuggle a second blob. learned: reject duplicates before set compare.
  - conjecture: SEALED reveals nothing about plaintext.
    refuted-by: V-E (manifest `byte_length` leak) + Forge (on-disk ciphertext member size leaks
    length regardless — AES-GCM length-preserving + ZIP_STORED). learned: zeroed the manifest
    channel AND documented the irreducible length residual honestly (padding = future format).
  - hardened: `_nonce` test-only private param (advisor #2); crypto reject-path coverage (advisor #4).
- 2026-05-28 ROUND 3 (close the length residual — "make all improvements as best"):
  - conjecture: length-hiding needs a future format (deferred).
    refuted-by: implemented now as **format 0.3.1** = 0.3.0 + PADMÉ length-padding (`src/padding.py`,
    Nikitin et al. PoPETs 2019). Plaintext is length-prefixed + padded to a PADMÉ bucket before GCM,
    so the on-disk member size reveals only a bucket (test: payloads 81 & 88 → identical sealed
    member size 124; 0.2.0 contrast leaks exact length). Scheme bound by version in AAD (padded↔
    unpadded downgrade fails). At that historical point the default writer had
    not yet moved beyond 0.2.0; later 0.4.0 superseded it as the default.
    142→**181 tests / 92.85%**.
    learned: PADMÉ hides length to BUCKET granularity (≈6% overhead, O(log log L)), not perfectly —
    documented honestly as bucket-not-exact, not over-claimed.
  - Forge cross-vendor (GPT-5.4, execution-verified): **PASS** — padme byte-exact to paper across all
    edges, pad/unpad round-trip-safe on zero-containing payloads, unpad fails closed on forged input,
    downgrade blocked by AAD+nonce (2 barriers), no 0.2.0/0.3.0 regression, no over-claim.
- 2026-05-28 ROUND 4 (manuscript + whole-project quality):
  - manuscript: added honest integrity model + format-ladder + PADMÉ length-hiding to 02c/08/abstract/
    conclusion (16 guard tests pass), PADMÉ citation; re-rendered — 11 figures + 28-pg PDF (4-pass+bibtex),
    new content + citation verified in PDF via pdftotext.
  - whole-project clean (was scoped to changed files only): ruff-check + ruff-format clean across
    src/scripts/tests (92 files); mypy clean (32 files, was 10 errors — json→dict[str,Any] return types,
    ontology var rename, type:ignore for runtime-only template/jsonschema imports); pre-existing dead
    imports removed.
  - added `format-version-latest` claim (0.3.1) bound to crypto.FORMAT_VERSION_LATEST + SUPPORTED + schema
    enum (test); refreshed REVIEW.md ledger; publication-readiness audit → ok:true, 0 blockers. 182 tests / 92.86%.

## Verification

### Round 16 (2026-07-14) — E5 multi-agent first-principles red-team and gate hardening

Scope: independent security, architecture, test-oracle, operations, and implementation
reviews against the current 0.4.0 surface. The installed PAI algorithm source was
unavailable in this environment; the review used the repository's existing ISA contract,
parallel specialist passes, reproduction-first tests, and current static/test evidence.

- **D1 (HIGH, confidentiality):** `pack_container` accepted an `export_level` higher
  than its source `observability_level`; filtering the full in-memory manifest could
  therefore publish hashes/resolution metadata the caller had declared unavailable.
  Both file and byte pack paths now reject escalation through a shared observability
  policy helper.
- **D2 (MED, format canonicality):** `unpad_payload` accepted noncanonical lengths and
  nonzero tails. It now requires the exact PADMÉ bucket and zero-filled tail, with
  negative tests; authenticated legacy/current round trips remain unchanged.
- **D3 (MED, reusable API):** manifest JSON parsing was public but did not validate
  before model coercion, and the schema cache ignored `project_root`. Parsing now rejects
  duplicate keys and validates raw JSON; schema cache entries are keyed by resolved schema
  path, preserving multi-checkout composability.
- **D4 (MED, configuration/operations):** YAML booleans/numbers were truthiness/coercion
  parsed and malformed JSON reports could raise out of output gates. Config parsing now
  validates mapping, type, finite-number, range, and enum constraints; report gates and
  publication reads fail closed on malformed JSON. `genkey --force` refuses symlinks and
  no longer double-closes descriptors after write failure.
- **D5 (HIGH, conformance oracle):** the verifier trusted its generated manifest for the
  expected outcomes and ignored fixture hashes, so a broken generator and verifier could
  agree on a forged matrix. Verification now binds the exact code-defined good/bad case
  set, fixed key, filenames, outcomes, descriptions, sizes, and SHA-256 bytes. Publication
  requires the complete matrix, not merely one case.
- **D6 (CI evidence):** CI and `run.sh` now lint scripts, set a job timeout, run figure QA
  and release bundling, and build/install the wheel before invoking the console script.
  Core benchmark-statistics tests no longer skip when ignored generated CSVs are absent.
- **D7 (MED, integration):** manuscript hydration and preflight now discover the documented
  `public/entofile` plus `public/template` sibling layout, while preserving clear standalone
  failure behavior. This closes a workspace-layout-specific integration failure.
- **Gate:** focused adversarial suite **56 passed**; full live suite **416 passed / 90.77%**;
  `ruff check src/ scripts/ tests/` and `mypy src/` are clean. Conformance is **7/7**,
  figure layout is **21/21**, the clean wheel contains only the intended `src` package,
  template output validation is green with 43-page bookends, and
  `audit_publication_readiness.py --check` is **ok:true with 0 blockers**.

### Round 15 (2026-06-10) — project-wide deep review ("Deeply review … and make all improvements and additions project-wide")

Scope: breadth-first sweep of every surface (src, tests, docs, manuscript, scripts, .github) via 4 parallel read-only reviewers + a stub-complete static-gate audit, then fix-everything-confirmed. Baseline watched live this session: **379 passed / 92.31%** (pytest --cov, exit 0), ruff clean — but **mypy was NOT clean**: the R14 "mypy clean" record came from a stub-less invocation that errored out before checking; a stub-complete run showed 13 genuine errors in 3 files. The auditor's own gate was the first defect.

- **D1 (MED, fail-open class — negative-control craft-failure laundering):** `verification_report._negative_control` wrapped CRAFTING and VERIFYING in one try/except that returned `{"rejected": True}` for any ValueError/OSError/KeyError. A failure while crafting the tampered container (malformed manifest JSON → JSONDecodeError ⊂ ValueError; missing manifest.json member → KeyError) was counted as a FIRED negative control — the gate could pass with zero crypto exercised (the same F1 false-assurance class D2/R14 closed for side files). A/B: malformed-JSON source pre-fix `rejected:True` → post-fix `{"available": False, "rejected": False, "reason": "could not craft…"}`. Bonus catches: corrupt-zip raised `zipfile.BadZipFile` UNCAUGHT in both old and first-draft new code (the A/B falsified my own first fix); `"tracks": null` returns None from `.get("tracks", [])` → TypeError uncaught. Fix: craft/verify split into separate try blocks; craft excepts = BadZipFile/ValueError/OSError/KeyError/TypeError/AttributeError → fail-closed; verify excepts treat `jsonschema.ValidationError` as verifier rejection; report-builder sample loop also records schema-invalid samples as `ok:False` instead of crashing. +3 tests (craft-failure fail-closed, null-tracks survival, schema-invalid sample recorded).
- **D2 (mypy surface, 13 errors → 0):** `manuscript_variables.generate_variables` rebound its typed `config: ExperimentConfig | None` parameter to the manuscript YAML dict (10 union-attr errors; renamed local → `manuscript_config`, 5 call-sites); `figure_qa._bbox_tuple` returned `tuple[float, ...]` vs declared 4-tuple; `public_promotion` imported `tomllib` unguarded while `requires-python >= 3.10` (tomllib is 3.11+ — import now `sys.version_info`-gated with `tomli` backfill dep). Gate pinned: `[tool.mypy]` in pyproject (files=src, py3.10) + mypy/types-PyYAML/types-jsonschema in dev extra → `uv run --extra dev mypy src/` = "Success: no issues found in 40 source files" is now reproducible.
- **D3 (SBOM version-of-record):** `scripts/export_sbom.py` hardcoded component `"version": "0.2.0"` (two release labels stale) and held the skeleton logic in the script. Moved to tested `src/sbom.py`; version derived from `manuscript/config.yaml paper.version` (the label CITATION.cff pins, = "0.4"), fails closed when missing. +5 tests incl. regression `version != "0.2.0"`.
- **D4 (stale 0.2.0-default wording + checker anti-recurrence):** the REVIEW.md ledger header still pinned the default-format field to the legacy 0.2.0 wire string and its scope sentence denied that the RC changed the default write format; entofile.md's spec pointer named the legacy version as the normative specification. Both fixed to 0.4.0-default + compat list. Root-cause closure at the checker: `PUBLIC_DEFAULT_FORMAT_SURFACES` += REVIEW.md, entofile.md; `STALE_DEFAULT_FORMAT_PHRASES` += 4 variants; +regression test pinning that the historical sentences fire and the fixed files are clean. (The exact sentences are deliberately NOT quoted here — ISA.md is itself a scanned surface and verbatim quotes re-trip the scan; they live in the regression test.)
- **D5 (CODEOWNERS):** `@4d` (local macOS username) × 15 rules → `@docxology`; GitHub would have silently skipped every ownership rule after public cutover. `test_public_repo_settings_scaffold_exists` had PINNED the wrong handle (oracle encoded the defect) — updated + now asserts `"@4d" not in codeowners`.
- **D6 (test-oracle tightening):** 6 weak exception oracles given `match=` (summary_stats empty, manifest schema ×2 → `jsonschema.ValidationError` with value pins, expansion nonpositive, unknown ontology type, 0.3.0→0.2.0 nonce downgrade) so a different failure can no longer satisfy them.
- **D7 (hygiene):** dead `plaintext_ok` in `container.py` removed (behavior-identical: every failure path raises; `key_authenticated = bool(tracks)` + comment); scripts/README.md rewritten as full 14-script delegation table (was 4); scripts/AGENTS.md completed; TODO.md maintenance (public-CI-dry-run item closed — docs/public_ci_dry_run.md exists; completed-list updated); 2 uncited bib entries removed (soiland2016research, mkvresearch2023).
- **Reviewers' clean verdicts (verified, no action):** crypto/AEAD/zip/proof/padding/CLI all clean (src reviewer); no mock violations, no vacuous tests, all security gates two-sided (tests reviewer); manuscript claims accurate vs code incl. PADMÉ bucket honesty, tokens hydrated, 21/21 figures referenced (manuscript reviewer); no broken doc links or placeholder residue (docs reviewer).
- **FirstPrinciples (Challenge) residual — CLOSED same round (user-approved continuation):** `conformance_report.json` was the last side-file-trust rung at publication-cert time (same class R14-D2 closed for containers, R13 for tests). Closed via `conformance.run_live_conformance()` — fixtures are deterministic (fixed key/timestamp/nonce), so the certifying path regenerates them into a scratch dir and verifies in ONE call, ignoring the on-disk report entirely; `check_publication_readiness(live_tests=True)` now gates on `checks["conformance_live"]` (fail-closed on zero cases). Display path unchanged and does NOT claim the check ran. +2 tests: `test_run_live_conformance_derives_verdict_without_side_file`, `test_certifying_path_runs_live_conformance` (forged green conformance side file is irrelevant to the certifying verdict; key absent on display path). The certification chain is now uniformly live: tests, containers, conformance.
- **Advisor (Rule 2):** confirmed craft/verify split shape; demanded (1) craft-fails-closed regression test — already shipped; (2) positive-control discrimination — structurally present (report `ok` requires all real samples green AND control fired; a reject-everything verifier fails the positive arm) and strengthened by binding the control's rejection to the injected defect (`integrity == "unverified"` assertion); (3) mypy pin must be what CI runs — CI dry-run map gained `lint` lanes (`uvx ruff check`, `uv run --extra dev mypy src/` with the stub warning); (4) SBOM `paper.version == package version` test — REJECTED deliberately: pyproject `0.1.0` is the documented not-yet-promoted package version (TODO item), release label is the pinned source of truth. Craft-bug-garbage-zip residual: verify except deliberately omits BadZipFile so that path fails LOUD (crash), never `rejected:True`.
- **Cross-vendor (Rule 2a): NO SIGNAL — honestly reported, not laundered as pass.** Forge (GPT-5.4 via codex) hit the codex usage limit before producing any analysis (resets 18:31 PDT 2026-06-10); Cato shares the same codex path. Retry fully staged at `~/.claude/PAI/MEMORY/WORK/20260610-000000_entofile-r15-audit/` (prompt + pre-extracted diffs). The negative-control fix is therefore SINGLE-VENDOR-REVIEWED (tagged in REVIEW.md); re-run Forge when quota resets.
- **Gate (artifact):** `388 passed in 125.67s` / `Total coverage: 92.56%` / exit 0 (baseline 379/92.31%; +9 tests: 5 sbom, 3 negative-control/report-builder, 1 stale-phrase regression; the CODEOWNERS pin test was updated, not added). `uv run --extra dev mypy src/` → "Success: no issues found in 40 source files". `uvx ruff check src/ tests/ scripts/` → "All checks passed!". Wire format UNCHANGED (no container logic touched beyond dead-code removal; all 0.2.0–0.4.0 round-trip tests green).

### Round 14 (2026-06-09) — 0.4.0 comprehensive review: genuine cross-vendor + verifier-first RedTeam + Science + FirstPrinciples ("comprehensively review and deeply proceed with all improvements ... /RedTeam /Science /FirstPrinciples /workflows")

Scope: first comprehensive adversarial review against the CURRENT 0.4.0 surface (rounds 1–13 were largely 0.2.0-era). Baseline watched live this session: 375 passed / 92.25%. Co-actor (cutover automation) active on release/docs files → R15: I worked only in the crypto/oracle core (co-actor-untouched), spawned read-only auditors, re-probed live state each phase. A 6-vector verifier-first RedTeam workflow (read-only specialists → adversarial verification) plus a GENUINE Forge GPT-5.4 cross-vendor pass — the first real OpenAI-lineage audit for this project, finally unblocked now that codex quota reset (every prior round was Claude-family fallback). Three real items found, each reproduced-before-fix with a negative-control A/B, Forge-confirmed.

- **D1 (MED, NEW — SEALED byte_length header-bypass; the keystone, 13 Claude rounds missed it):** `_reconcile_byte_length` SKIPPED the byte_length↔plaintext check whenever `observability_level == SEALED` — but that level is read from the *unauthenticated* manifest header. Repro: pack AUDITABLE (real digests), rewrite the header to claim SEALED + `byte_length=999999` while KEEPING the real digests, drop proof → keyed `verify_container(require_integrity=True)` returned `ok:True, integrity:"key-authenticated"` advertising a false size. The R10/R11/R12 ledger had explicitly rationalized "byte_length SEALED-skip-is-correct" — the shared Anthropic-family blind spot. Fix (`src/container.py:_reconcile_byte_length`): at SEALED, bind `byte_length` to the redaction SENTINEL (`== 0`, the value `observability.py` always writes) instead of skipping; non-zero ⇒ reject. A/B: forged lie now `ValueError: SEALED redaction requires byte_length 0`; legit SEALED (byte_length 0) still `key-authenticated` and unpacks. byte_length is a schema-REQUIRED int (so "absent" is rejected upstream → bidirectional per advisor). +`test_keyed_verify_rejects_sealed_header_byte_length_bypass`; updated `test_keyed_verify_cannot_be_downgraded_by_header_mutation` (it had pinned the old weaker behavior — now zeroes byte_length to model a well-formed SEALED claim, preserving the anti-downgrade intent). **Forge (genuine GPT-5.4) independently verified the fix correct AND complete: attack rejected, honest-SEALED + empty-track edges pass, no bypass.**
- **D2 (close the twice-deferred F1 residual — live crypto at the container gate):** `container_verification_report_ok` / `validate_all_outputs` read the on-disk `container_verification.json` (the "last side-file trust" deferred in R12 §195 and R13 §198). Repro: a forged `{ok:true, samples:[…], negative_control:{rejected:true}}` shell passes the gate with ZERO crypto run this session. FirstPrinciples: certifying the crypto core requires crypto to RUN at certification time — a side file is a cached claim, not proof. Fix: added a `live=` mode (`output_gates.container_verification_report_ok`, `validate_all_outputs(live_containers=)`, `verification_report.containers_verification_ok` default `live=True`, `analysis.validate_generated_outputs`) that re-derives via `build_container_verification_report` (real decrypt + negative control), IGNORING the side file; wired `live_containers=live_tests` into the `publication.py` certifying path (symmetric with R13's live-test re-derivation). A/B: forged file display=True → live=False (gate now bites); real repo live=True (1 sample + neg-control fired). **Footgun-closure (advisor + Forge both flagged the default `live=False`):** the result now carries `containers_live`, and the publication cert path REFUSES to certify when `live_tests` but `containers_live` is false — protection lives in the consumed-result, not in trusting the caller's flag. +`test_container_gate_live_ignores_lying_side_file`, `test_container_gate_live_rejects_forgery_without_real_crypto`, `test_validate_all_outputs_reports_containers_live_provenance`.
- **D3 (LOW-MED, doc honesty — PADMÉ length-hiding over-claim; confirmed by Forge + advisor):** the manuscript presented PADMÉ length-padding as a default-format length-hiding property. Repro: at the DEFAULT AUDITABLE level the manifest publishes exact `byte_length` in cleartext (42), fully nullifying PADMÉ for those containers; and even SEALED+0.4.0 does not hide length exactly (len40→member76, len60→member100: distinct PADMÉ buckets — hiding is bucket-granular, near-exact for small payloads). Honest fix (no code/wire change — TYPED/RESOLVED deliberately expose byte_length and do not claim hiding, per advisor): sharpened `00_abstract`, `08_limitations_and_threat_model` (lines 9/10/24/47) to state length is NEVER hidden exactly — non-sealed levels disclose it via the cleartext `byte_length` field, sealed export removes the field but the member size still reveals the PADMÉ bucket, unpadded compatibility formats leak exact length at every level. 43 manuscript honesty-guard tests still green.
- **RedTeam clean vectors (reproduced, no defect):** crypto-AEAD (cross-format downgrade incl. padded↔unpadded fails the GCM tag via AAD; cross-track relabel fails via HKDF track key; `_nonce` reachable only from conformance with a public key; tag truncation rejected), zip-ingestion (declared-size-lie bomb bounded by real decompression cap, aggregate cap, dup-member parser-differential, path-escape — exceptionally hardened), proof chain (forged-links/version rejected by `_links_match_manifest`), padding (`unpad_payload` malleable only OUTSIDE the GCM boundary — unreachable without the key), CLI/conformance (genkey O_EXCL/0600, BadZipFile caught, `--allow-unverified` weakens safely). Forge full-surface sweep: no other unauthenticated-header-gates-a-security-check beyond the now-fixed SEALED case; `key_authenticated` is always derived from the decrypt attempt, never a manifest field.
- **Advisor (Rule 2, E5 HARD):** confirmed sentinel-0 > field-absent (absence can't be authenticated; sentinel lives in the checked region + bidirectional enforcement via schema-required), flagged the `live_containers=False` footgun (→ closed via `containers_live` result-carried assertion), and caught that sealed export does not achieve EXACT hiding even with PADMÉ (→ D3 sharpened to bucket-granular-never-exact). Ruled docs-fix (not redacting byte_length at TYPED/RESOLVED) correct — those levels don't promise hiding.
- **Gate:** baseline 375/92.25% → **379 passed / 92.31%** (full `pytest --cov=src`, 135s, exit 0), ruff + mypy clean on all changed src (also fixed a pre-existing `publication.py` union-attr mypy error in `_read_yaml` paper handling, untouched by the feature work). Wire format UNCHANGED (no 0.2.0/0.3.0/0.3.1/0.4.0 container round-trip affected). Note: manuscript PDF should be re-rendered at cutover to carry the D3 honesty edits (prose-only; guard tests green).

---

### Round 13 (2026-05-29) — RedTeam re-audit + close the deferred F1 residual ("comprehensively ... /RedTeam deeply and improve all")

Scope: close R12's explicitly-deferred F1 residual (publication.py trusts `test_results.json` as a side file) + re-RedTeam the hardened oracle. Advisor (E5 HARD) confirmed live-rerun > freshness-hashing (a forger recomputes a hash); Forge re-audit found 1 HIGH + residuals. 4 oracle fixes, each reproduced-before-fix.

- **F1 closed — live test re-derivation (the deepest, deferred from R12):** `check_publication_readiness(..., live_tests=True)` (the `--check` certifying path) now RE-RUNS pytest via `_run_live_test_summary` and ignores the side file. Parses structured **junitxml + coverage-json** (never stdout), requires `collected>0` (pytest exit-5 must not read as pass), fail-closed on timeout/parse-miss/wrong-interpreter, recursion-guarded by env var (`_LIVE_RUN_ENV`) so the nested suite's meta-tests skip. Repro: forged `{all_passed:true,coverage:99}` + live → `tests_passed:False, ok:False`. Verified end-to-end: `--check` re-ran 277 tests live (~24s, no recursion), `tests_source:live`, ok:true. Advisor's hard constraint met: **no path returns ok:true from the side file alone on the certifying path**; display path labels `tests_source:side-file`.
- **HIGH — sentinel escape (Forge):** `_na_valued_tokens` only flagged exact `"N/A"`, but `manuscript_variables.py` emits `""` (PAPER_SUBTITLE) and `"false"` (RESULT_CONTAINER_VERIFY_OK) — a failed-verify `"false"` rendered into prose and passed. Fix: case-insensitive unbound-sentinel set (n/a, none, null, nan, tbd, todo) + per-token boolean-blocker (`RESULT_CONTAINER_VERIFY_OK=="false"` blocks); `""`/`"true"` legitimately allowed (per-token, no false-reject — real output clean).
- **PDF-name mismatch (found via the live audit):** `combined_pdf` hardcoded `entofile_combined.pdf` but the standalone renderer emits `_combined_manuscript.pdf` → false-fail by invocation path. Fix: `_find_combined_pdf` accepts `*_combined.pdf` or `_combined_manuscript.pdf`, still substance-checked (`_is_real_pdf`: %PDF- magic + ≥1024 B).
- **Stale-evidence trust (same F1 class, found mid-round):** the `evidence_registry` check read a stale `validation_report.json` (10:56, predating my prose). Fix: `_evidence_issues` re-derives grounding LIVE via the infra registry when importable; else freshness-guards the side file (a report older than manuscript/claim_ledger is "stale", not clean). Root cause of the flagged `8`/`95%` was real ungrounding → grounded honestly by registering `bits-per-byte`=8 and `confidence-interval-level-percent`=95 in `data/claim_ledger.yaml` (provenance to crypto.py/benchmark_stats.py), NOT by weakening the shared infra matcher. Live evidence after fix: `[] clean`.
- **RedTeam clean vectors (Forge, reproduced):** R10/R11 fixes still reject (dup-JSON-key, dup-track-id read+write, proof correspondence, byte_length SEALED-skip-is-correct); AAD downgrade/relabel binding solid; `__main__.py` 0%-cov is a benign untested alias.
- **Honest residual (Forge, documented):** the hardened `container_verification_report_ok` is "3 keys not 1" but a substance-check over a side file is still a side file — fully closing it (like tests) means re-running crypto at gate time; deferred as the next layer. The negative control covers the stripped-digest threat, not GCM-tamper (proven separately by the key-based benchmark) — documented, not silent.
- **Gate:** 271 → **277 passed / 92.3%**, ruff+mypy clean, live `--check` ok:true / 7/7 / 0 blockers (tests_source:live, evidence live-clean), PDF 0 dangling. +6 live-rerun regression tests + sentinel/pdf-name controls. codex quota still blocked (2026-05-30 13:48) — Forge ran Claude-side, flagged as residual.

**Follow-up (deferred):** (1) re-run crypto live at the container gate (the last side-file trust); (2) codex/Cato OpenAI-lineage pass after quota reset.

---

### Round 12 (2026-05-29) — RedTeam VectorSpecialists, Phase-1A oracle attack ("/RedTeam deeply check again")

Scope: adversarial re-audit. PHASE 1A (attack the verifier first, mandatory at E4) deployed a verifier-specialist against the release/validation oracle (publication.py, output_gates.py, verification_report.py, the test gates) BEFORE any artifact attack. Verdict: **ORACLE-INCOMPLETE** — per the re-scope rule, fix the oracle first. 3 gaps reproduced-before-fix and closed; the planned artifact attack was correctly pre-empted (the oracle was the defect).

- **G1 (deepest — F1 oracle false-assurance):** `container_verification_report_ok` returned `True` on a forged `{ok:true, sample_count:0, samples:[]}` — the gate certifying the crypto core trusted a stale/hand-written side file with zero crypto behind it (verification_report.py explicitly does "no live rebuild"). Repro confirmed. Fix: gate now requires ≥1 sample, all samples `ok`, AND a fired `negative_control.rejected` — binding the pass to substance a real `build_container_verification_report` always carries but a shell does not.
- **G2:** `combined_pdf` check was bare `is_file()` — a 1-byte non-PDF passed while the ISA claimed "PDF zero dangling refs". Fix: `_is_real_pdf` requires the `%PDF-` magic + ≥1024 bytes.
- **G3:** a manuscript token RESOLVED to literal `"N/A"` was invisible to both gates (the unresolved-`{{TOKEN}}` regex only catches `{{}}` residue; the token-producer test checks key presence, not value). Fix: `_na_valued_tokens` flags any non-prose token whose value is `N/A` as a blocker. (Real output has zero such tokens — fix is safe, not a false-reject.)
- **Test contract corrected:** 2 existing output-gate tests asserted `containers_ok:True` on a bare `{ok:true}` shell — they were encoding the very gap. Updated `_write_minimal_outputs` to emit a substantive report (samples + negative_control), so the tests now verify the hardened contract.
- **RedTeam Q4 negative-controls landed as regression tests:** `test_container_gate_rejects_stale_ok_shell`, `test_container_gate_rejects_ok_without_negative_control`, `test_publication_rejects_fake_pdf`, `test_publication_flags_na_valued_token`.
- **Discipline:** every specialist finding treated as a conjecture and reproduced on disk before fixing (one reviewer claim, REPRO 3, was inconclusive on first run — re-verified properly). The verifier-specialist's strongest item (stale crypto side file) matched this project's own history (the original R1 keyless fail-open), confirming the F1 pattern.
- **Gate:** 267 → **271 passed / 92.87%**, ruff + mypy clean, real container gate passes on the regenerated substantive report, publication ok:true / 0 blockers, PDF 36pp zero dangling. The stricter gates do NOT false-reject the honest project (verified: no N/A tokens, real PDF passes, substantive report passes).

**Follow-up (deferred):** publication.py still reads `test_results.json`/coverage as trusted side files (G1's siblings, Assertions 1-2) — fully closing them means having the audit re-run pytest live or hash-bind the report to a gate run; deferred as a larger change. codex/Cato OpenAI-lineage cross-check still pending quota reset (2026-05-30 13:48).

---

### Round 11 (2026-05-29) — deep review #2 ("review again, continue to make all improvements")

Scope: continue the deep audit into the surfaces rounds 1-10 never examined (CLI, dashboard, verification-report gate) + the advisor's R10 parting flag (byte_length-vs-actual). 5 fixes, each reproduced-before-fix, regression-pinned. Wire format unchanged.

- **D1 (byte_length reconciliation, advisor R10 flag):** `byte_length` was schema-validated as an int but never reconciled against the decrypted plaintext length. Repro: a container with proof removed + `byte_length` rewritten 8→999999 verified `ok:True, key-authenticated` while advertising a false size. Fix: `_reconcile_byte_length` in the keyed `verify_container` loop + `unpack_container` — compares manifest `byte_length` to `len(plaintext)` (the one moment we hold authenticated truth), skipped only at SEALED (where redaction zeroes it), uses unpadded plaintext (0.3.1-safe). Verified at all 4 export levels + empty-payload edge.
- **D2 (HIGH, CLI genkey clobber):** `genkey -o existing.key` silently overwrote a live master key (rc=0), permanently destroying decrypt/verify for every container under it. Fix: `os.open(O_CREAT|O_EXCL, 0o600)` — refuses to clobber (rc=1, key untouched), `--force` to replace, atomic 0600 (also closed F2: chmod-failure-swallowed + non-atomic-mode window).
- **D3 (CLI traceback leak):** `verify`/`inspect` on a non-zip file raised uncaught `zipfile.BadZipFile` (an `Exception`, not `OSError`) → traceback to user. Fix: added `BadZipFile` to the CLI boundary's caught tuple → clean `error:` + exit 1.
- **D4 (HIGH, dashboard green-oracle blindness):** `dashboard.py` hardcoded `passed:True` for any invariant `kind != "equal"` — latent: the moment a tolerance (`close`) invariant is added (the `tol` field exists for it), the dashboard would report it passed unconditionally. Fix: `InvariantResult.passed` property evaluates equal/close and **raises on unknown kind** (single source of truth, no silent True).
- **D5 (verification-report shape-only gate):** `build_container_verification_report` proved good samples verify but never that a bad one is rejected (excluded `bad.ento.zip` by name). Fix: added a `_negative_control` that derives a digest-stripped container from a good sample and asserts keyless `require_integrity=True` REJECTS it; report `ok` now requires `negative_control.rejected` — binds rejection, not just acceptance.
- **Documented (not silently left):** SEALED export carries the manifest *header* (creator/created/format_version) in cleartext — per-track redaction doesn't touch it. Tightened manuscript §08 from the misleading "only manifest fields redact" to precisely state what SEALED does/doesn't hide.
- **Cross-vendor (Forge, Rule 2a):** codex/GPT-5.4 quota-exhausted until 2026-05-30 13:48 (hard usage-limit, NOT a config issue) — no genuine OpenAI-lineage opinion this round; Forge delivered the Claude-side fallback (same-lineage, carries shared-blind-spot risk). It surfaced F1/F3/F7 (→ D2/D3/D4) + F4 (→ D5) + F5 (→ doc). All reviewer findings treated as conjectures and reproduced before fixing; one of my own probes was a test bug (str-vs-Path) caught by reproduction.
- **Gate:** 257 → **267 passed / 93.16%**, ruff + mypy clean (pre-existing yaml only), PDF 36pp zero dangling, publication ok:true / 0 blockers. 12 new regression tests (CLI clobber/force/0600/non-zip, invariant passed-property + unknown-kind, byte_length lie + all-levels, report negative control).

**Follow-up (deferred):** re-run codex/Cato after 2026-05-30 13:48 for the genuine OpenAI-lineage cross-check on the CLI/dashboard/report changes (this round was Claude-family only).

---

### Round 10 (2026-05-29) — deep core review ("deeply review and improve completely")

Scope: deep-audit the security-critical CORE (crypto/proof/container/security) that 9 manuscript/figure/stats rounds never re-reviewed. Found + fixed **4 real defects**, each reproduced-before-fix, regression-pinned, every gap one the green suite was structurally blind to (built by the honest writer that can't produce malicious shapes). Wire format unchanged.

- **D1 (proof correspondence, self-found):** `verify_proof_export` accepted a hash-chain whose links described tracks NOT in the manifest, and a bogus `format_version` — it checked only the manifest digest + chain self-consistency. Repro: forged "evil"-track chain + `format_version=9.9.9` both returned `True`. Fix: `_links_match_manifest` (rebuild via `export_proof` + compare link tuples + `format_version` match). 3 tests (forged links, wrong version, reordered).
- **D2 (HIGH, Forge/codex-found):** `pack_container`/`pack_container_bytes` silently collapsed duplicate track IDs (encrypted dict keyed by id) → manifest lists 2, ZIP holds 1, and at redacted export levels the digest check is skipped so `verify(...require_integrity=True)` returned `ok:True, key-authenticated, track_count:2` with a track **silently lost**. Repro confirmed. Fix: reject duplicate ids in `validate_plain_tracks` (both pack paths).
- **D3 (CONCERN, Forge-found):** read-path schema validation ran on the *coerced* dataclass (`validate_manifest_dict(manifest.to_dict())`), laundering a JSON-string `byte_length` (`int()`-coerced) and unknown fields (dropped) past the schema. Fix: validate the RAW parsed JSON before `Manifest.from_dict`.
- **D4 (advisor-found, read-path completeness):** (a) crafted container with manifest tracks `[a,a,b]` (2 members) verified `ok:True, track_count:3` — the write-path D2 fix didn't cover crafted containers; added read-path manifest-track-uniqueness guard. (b) `json.loads` collapsed duplicate JSON keys last-wins before validation (parse-then-validate divergence one level below the schema); added `object_pairs_hook` rejecting duplicate keys. Plus an empty-proof **negative control** test proving the D1 correspondence check isn't vacuous (non-empty manifest + empty proof → `False`).
- **Advisor-probed & ruled NOT defects (documented, not silent):** manifest is honestly documented as unkeyed (adversarial integrity is key-based only — threat-model TM rows + 02c); `track_id="."` is non-escaping hygiene; empty-manifest+empty-proof vacuous-True is correct (digest still binds bytes); AAD downgrade/relabel binding verified solid (0.3.0→0.2.0, cross-track, 0.3.1→0.3.0 all fail the tag); `_nonce` test-knob has zero production call sites.
- **Docs/manuscript updated:** 02b + 02 now state `verify_proof_export`'s three checks (digest + chain + link↔track correspondence); `_verify_proof_if_present` docstring corrected.
- **Cross-vendor (Forge, Rule 2a):** codex/GPT-5.4 at high RAN (timed out at 300s wall-clock but its event-stream leads — D2 + D3 — were independently confirmed on disk; that IS the cross-vendor value). Verified the proof fix correct/complete, integrity ladder honest, AAD binding solid, coverage-gap lines benign. **Advisor (Rule 2, E5 HARD):** turned a "3 fixes done" into D4 — found the read-path dup-id gap + duplicate-JSON-key vector + demanded the empty-proof negative control; confirmed `validate_plain_tracks` was right for write but read needed its own guard.
- **Gate:** 248 → **257 passed / 93.0%** (coverage up), ruff + mypy clean (pre-existing yaml/experiment_config only), PDF 36pp zero dangling refs, publication audit ok:true / 0 blockers. 10 new regression tests across proof + container-security.

**Follow-up (deferred):** AAD/nonce identity-binding is a 0.3.0+ feature; 0.2.0's unkeyed-manifest model remains a documented limitation (not a silent gap). Re-run codex with a tighter pack-path-only prompt for its full write-up if desired.

---

### Round 9 (2026-05-29) — no-hardcoded-variables audit ("ensure no hard-coded variables in the manuscript, all properly validated and auto-injected")

Scope: audit every manuscript body section for literals that should be `{{TOKEN}}`-injected; confirm each is auto-injected + gate-enforced; harden the gate's blind spots. No wire/format change.

- **Found + fixed injection gap (ISC-R9a):** the hardened format-ladder versions `0.3.0`/`0.3.1` and the hardened `12`-byte nonce were bare literals across abstract/02c/03a/04/08 (only the default `{{FORMAT_VERSION}}` was tokenized). Added 6 crypto-derived tokens — `FORMAT_VERSION_HARDENED_FIRST`, `FORMAT_VERSION_LATEST`, `FORMAT_VERSIONS_HARDENED`, `FORMAT_VERSIONS_SUPPORTED`, `NONCE_BYTES_HARDENED`, `FORMAT_LATEST_PADS` — all from `crypto.SUPPORTED_FORMAT_VERSIONS`/`FORMAT_VERSION_LATEST`/`nonce_size_for`/`pads_payload`, **semantic-version sorted** (parse-to-int-tuple, so 0.3.10 > 0.3.2 — not string sort). Replaced every literal; PDF renders the ladder table correctly from tokens.
- **Spelled-out counts (ISC-R9b, both reviewers):** "four graded observability levels", "two opt-in hardened formats/successors", "one of three values" were derivable literals. Added `COUNT_OBSERVABILITY_LEVELS`/`COUNT_HARDENED_FORMATS`/`COUNT_SUPPORTED_FORMATS`/`COUNT_INTEGRITY_LEVELS` (len() of canonical sources). Added canonical `REPORTED_INTEGRITY_LEVELS` tuple to `container.py` (single source of truth for the 3 reported integrity values) so `COUNT_INTEGRITY_LEVELS` derives, not hardcodes.
- **Forward-safe guards (ISC-R9c):** replaced the enumerated version denylist in `test_manuscript_no_literal_metrics` with a **generic `\bX.Y.Z\b` pattern** (catches any future 0.3.2/0.4.0 — proven by mutation: injected both → guard red; reverted → green) + 12-byte pattern; added `test_manuscript_counts_are_injected_not_spelled_out` count-guard (proven: re-introducing "four graded observability" → red).
- **Triage (verified by Forge line-by-line):** legitimately-literal and correctly NOT tokenized — cipher names AES-256/SHA-256, observability enum row labels 0/1/2/3 in taxonomy tables, markdown list ordinals, LaTeX `\{0,1\}`/`1+H/n`, 95% CI, Draft-07, SP 800-38D, 4 KiB. The max-level "3" is consistently a token (`CONFIG_OBSERVABILITY_LEVEL_MAX`) where it means the metric and literal only where it's an enum-row label.
- **Two-way binding now complete:** `test_all_manuscript_tokens_are_generated` (every `{{TOKEN}}` has a producer) + literal guard (no known metric hardcoded) + generic version guard (forward-safe) + count guard (no stale cardinality).
- **Advisor (Rule 2):** triage correct; flagged GCM tag-length sibling (checked — no bare tag-length literal in prose) + semver-ordering latent bug (fixed: semantic sort + reasoning) + count-rot (fixed). **Cross-vendor (Forge, Rule 2a):** CONCERNS → all remediated; proved the denylist gap (0.3.2/0.4.0 slipped) and count gap by mutation, both now closed. codex/GPT-5.4 still quota-blocked (resets 2026-05-30 13:48) — OpenAI-lineage second opinion deferred, honestly reported.
- **Gate:** 248 passed / 92.86%, ruff+mypy clean (pre-existing experiment_config fallback + yaml stub only; no new errors), PDF zero dangling refs, counts + ladder render correctly. Zero bare X.Y.Z version literals in any body section.

**Follow-up (deferred):** re-run codex/Cato after 2026-05-30 13:48 PT for OpenAI-lineage confirmation.

---

### Round 8 (2026-05-29) — statistics + visualizations + manuscript ("deeply ... visualizations and statistics and manuscript")

Scope: add a dispersion-statistics layer (the benchmark's n=3 repetitions enable variance/CI the manuscript never surfaced), a statistics-bearing figure, and the manuscript writing to carry them honestly. Wire format 0.2.0 unchanged.

- **Statistics layer (ISC-R8a):** `src/benchmark_stats.py::summary_stats` → mean / sample-SD(n-1) / CV / SEM / two-sided 95% **Student-t** CI via a hardcoded t-table (stdlib only, no scipy; df 1–10 then z=1.96 fallback). n==1 → zero-spread; exact metric → sd=cv=0; empty → ValueError (fail loud). + `base_condition`/`repetition_values`/`field_summary`. Forge re-derived the t-table vs scipy (<0.0005 error) and confirmed mean±t·SEM correct.
- **Visualization (ISC-R8b):** new figure #13 `fig:throughput_dispersion` — per-repetition points + mean + 95% CI band (band floor **clamped at 0 for display**, legend reports true bounds), inset n/SD/CV. `data_derived=False` (plots timing). R14 figure-count pins swept 12→13 (test_figures, figure_registry.md, methods.md, claim_ledger.yaml+.md) + determinism timing-set now 6.
- **Manuscript (ISC-R8c):** new "Statistical dispersion and reliability" subsection (03a) + "Statistical methods" note (05) + abstract reports n/CV alongside mean. All numbers via new `RESULT_THROUGHPUT_N/SD/CV/CI95_LO/HI` tokens. PDF 36pp, **zero dangling refs**.
- **Tests (ISC-R8d):** `test_benchmark_statistics.py` (9: hand-computed n=3, t-not-z, CI-brackets-mean, zero-variance control, empty-raises), token-presence+CI-invariant, and `test_manuscript_statistics_honesty.py` (run-specific-claim guard + 7-synonym meta-test proving the guard bites). 235→**245 tests / 92.84%**.
- **Self-caught defect (the round's keystone):** first dispersion prose hardcoded "the CI lower bound is unphysical/negative" + "interval is wide" + "is high-variance" — TRUE for a high-CV run (57%), FALSE for a low-CV run (this run 4.2%); timing is re-measured every run. The honesty guard (hardened after Forge/advisor flagged regex gaps) caught all surviving magnitude/sign/width verdicts; prose rewritten to describe the *method* conditionally, never a run's shape. LESSON: reader-side guard must be stricter than the write-time denylist + prove it bites on the next synonym (memory `gotcha-config-knob-consumption-not-naming`, `feedback-shape-tests-dont-bind-truth`).
- **Advisor (Rule 2, E5 HARD):** flagged normality-untestable-at-n3 (added to methods note), "fixed one instance of a class" (closed: guard generalized + synonym meta-test), CI-brackets-mean near-tautology (acknowledged as smoke-only; load-bearing tests are hand-computed t + zero-variance control).
- **Cross-vendor (Forge, Rule 2a): CONCERNS → all remediated.** Found 2 surviving run-specific magnitude verdicts (abstract + experimental-setup "is high-variance") contradicting the 4.2%-CV run + the guard's regex gaps that let them through — both fixed and re-verified (PDF grep: 0 surviving verdicts). Confirmed: t-CI math correct, clamp display-only (legend true bounds), no test theater (independent hand constants), data_derived=False correct, R14 pins consistent. **codex/GPT-5.4 still quota-blocked (it is 2026-05-29; resets 05-30 13:48) — OpenAI-lineage second opinion NOT obtained, honestly reported, no silent fallback.** Cato deferred with codex.
- **Gate:** 245 passed / 92.84%, ruff+mypy clean (pre-existing yaml-stub only), publication audit ok:true / 7/7 / 0 blockers (test_results.json reproduced live).

**Follow-up (deferred):** re-run codex/Cato after 2026-05-30 13:48 PT for the OpenAI-lineage cross-check on the statistics layer + honesty guard.

---

### Round 7 (2026-05-29) — E5 comprehensive closure ("comprehensively proceed")

Scope: bind the formalisms to executable tests, prove figure determinism, close the never-run publication/HTML gates, adversarially verify. Wire format 0.2.0 unchanged.

- **Equation↔code fidelity (ISC-R7a):** new `tests/test_equation_code_fidelity.py` — 8 tests binding all 6 manuscript equations to code behaviour (track_key HKDF label, track_member nonce‖tag‖ciphertext + length-preservation, expansion_law H+n bytes, integrity_levels 3 distinct branches incl. fail-closed, observability_monotone real serialized sizes 661<875<1136<1328, container_map heterogeneous). **Non-vacuity PROVEN:** mutating `TAG_SIZE` 16→17 turned 3 tests RED; restore → 8 green (mutation probe, then reverted).
- **Equation count-guard (ISC-R7b):** `test_equation_set_is_exactly_the_bound_set` pins the manuscript equation set == the 6-name fidelity-bound set, so a 7th equation cannot ship unbound (advisor ask).
- **Figure determinism contract (ISC-R7c):** external A/B byte-identity probe found exactly the 5 timing figures vary run-to-run, 7 data-derived figures byte-stable. Codified as `FigureSpec.data_derived` (exposed in registry JSON via `_registry_entry`); `tests/test_figure_determinism.py` asserts the 5-figure split + regenerates each data figure twice with an interleaved unrelated render (global-state-leakage probe) + byte-identity. Forge verified no `data_derived=True` figure reads a timing column (`pack_seconds`/`unpack_seconds`/`pack_throughput_mib_s`).
- **Publication readiness (ISC-R7d):** `audit_publication_readiness.py --check` → **ok:true, 7/7 checks, 0 blockers**; `test_results.json` produced from a *live* coverage run this session (reproduced, not a stale file). HTML render produced (17 files). Note: pre-existing `test_results.json` trusted-side-file fail-open in `publication.py` is a known self-referential residual (Forge CONCERN), not introduced here.
- **Gate:** `pytest --cov=src --cov-fail-under=90` → **220 passed / 92.95%**, exit 0; ruff check+format clean; mypy clean except pre-existing `yaml` import-stub. PDF 34–35pp, **zero dangling refs**, equations numbered.
- **Advisor (Rule 2, E5 HARD):** flagged vacuous-pass risk (closed by mutation probe), determinism-as-escape-hatch (closed: per-figure column audit + classification test), equation count completeness (closed by count-guard), reproduce-don't-trust on test_results.json (closed: live reproduce). Confirmed timing-figure exemption is honest.
- **Cross-vendor (Forge, Rule 2a):** **PASS (with CONCERNS)** — independently reproduced 220/92.95%/ok:true; confirmed all 8 fidelity tests genuinely binding (not theater), 3 distinct integrity branches, real monotone sizes, no data_derived misclassification, no equation drift. Minor CONCERN: track_key test shares the HKDF primitive (mitigated by `test_crypto_vectors.py`). **codex/GPT-5.4 engine quota-blocked until 2026-05-30 13:48 PT — OpenAI-lineage second opinion did NOT run (honestly reported, no silent fallback); Forge compensated with full on-disk audit.** Cato (E5 mandatory) deferred with Forge — re-run both after quota reset for the second-lineage confirmation.

**Follow-up (deferred):** (1) re-run codex/Cato cross-vendor after 2026-05-30 13:48 PT for OpenAI-lineage confirmation; (2) optionally harden `publication.py` to re-derive test_results from a live run rather than trusting the side file.

---

### Round 6 (2026-05-29) — viz depth + config surface + formalisms + tests

Scope: deeper visualizations, bigger configurability surface, validation/tests, writing, formalisms with autoreference. Wire format 0.2.0 **unchanged**.

- **Deeper visualization (ISC-R6a):** new figure #12 `fig:expansion_law` — measured per-track ratios overlaid on the closed-form `r(n)=1+H/n` curve; every point lands on the model (max |residual| = 3.3e-7, shown as an in-axes badge). Visually verified at `wide` size. R14 figure-count pins swept 11→12: `tests/test_figures.py`, `docs/figure_registry.md`, `docs/methods.md`, `data/claim_ledger.yaml` (+ new binding test).
- **Config surface (ISC-R6b):** 6 new `experiment.viz` knobs — `palette` (3 named colorblind-safe sets), `heatmap_cmap` (5-cmap whitelist), `annotate_values`, `line_width`, `marker_size`, `scatter_size` — all threaded through `viz_theme` accessors into real plot calls. Unknown experiment/viz keys now raise `ConfigError` (fail-closed, names offender + valid set); palette/cmap validated against whitelists.
- **Validation/tests (ISC-R6c):** `test_experiment_config_surface.py` (no-dead-knob inventory + **per-knob behavioral consumption** proving each knob changes rendered output, not just round-trips + unknown-key/palette/cmap rejection), `test_expansion_law.py` (closed form + measured-data-to-float-precision + negative control), `test_equation_crossrefs.py` (every eq def referenced, every ref defined, unique), `test_figure_crossrefs.py` hardened to require an image definition per figure (not just a reference). 182→208 tests, 92.86%→**92.95%**.
- **Formalisms with autoreference (ISC-R6d):** new `manuscript/02d_formal_model.md` with 6 LaTeX equations (`{#eq:container_map, track_key, track_member, expansion_law, integrity_levels, observability_monotone}`), all resolved via pandoc-crossref `[@eq:]` (verified v0.3.24 on PATH; PDF renders "eq. 4 in sec. 7", **zero dangling `??`**). 34-page PDF.
- **Cross-vendor (Forge, Rule 2a) — CONCERNS, all remediated:**
  - **CRITICAL `line_width` dead knob** — `apply_rcparams` set `lines.linewidth` but every plot passed explicit `linewidth=2.0`, overriding it. FIXED: added `line_width()` accessor, swept all 5 hardcoded sites; end-to-end probe confirms config 1.0→7.0 changes rendered Line2D width; added `test_line_width_knob_changes_rendered_lines` (bites without the fix).
  - stale `figure-count: 11` ledger cell (unbound) → bumped to 12 + bound to `len(FIGURE_SPECS)` by test.
  - `eq:observability_monotone` theorem-styled-but-empirical → reworded to a schema-dependent observed property naming the `ento:opaque` sentinel condition.
  - "visual proof" over-claim → "empirical confirmation" (H is spec-fixed, not fitted); scoped to single-track/uncompressed 0.2.0, noting 0.3.1 PADMÉ departs.
  - codex engine hit usage limit → Forge audited directly on disk (no silent fallback); GPT-5.4 second-lineage cross-check deferred to 2026-05-30.
- **Advisor (Rule 2, E4 HARD):** confirmed format-freeze honest; flagged the same "identity vs fit" scoping (closed: H spec-derived + negative control bites) and "set-equality ≠ consumption" (closed: per-knob behavioral tests added).
- **Gate:** `pytest --cov=src --cov-fail-under=90` → **208 passed / 92.95%**, exit 0; ruff check+format clean; mypy clean except pre-existing `yaml` import-stub (untouched, not a regression).

---

### Round 5 (2026-05-29) — presentation/quality pass ("greatly improve")

Scope: title + acronym, author, figures, captions, prose, file description. Wire format and all crypto **unchanged** (0.2.0 frozen; INV-1..5 preserved).

- **Title + acronym (ISC-R5a):** `manuscript/config.yaml` title → "ENTO: an ENcrypted, Typed, Omnitrack container format for multimodal research data"; acronym defined in abstract/intro/README/architecture/faq. PDF title page renders it (pdftotext line 1) — presentation-only, on-disk `FORMAT_VERSION="0.2.0"` unchanged (honest, advisor-confirmed).
- **Author (ISC-R5b):** Daniel Ari Friedman / Active Inference Institute / ORCID 0000-0001-6232-9096 (ISO 7064 checksum valid, advisor-verified) / gmail. Renders on title page + reproducibility section.
- **Figures + captions (ISC-R5c):** all 11 `FigureSpec` summaries rewritten richer (interpretation, not just description); plots gained measured-value annotations — heatmap cell values (luminance-aware text), tamper 100%-stacked bar with centered count/rate, crypto_overhead per-bar byte totals + left legend, unpack latency labels, overview suptitle. `figures.py`/`figure_plotters.py`/`viz_theme.py` (`reserve_top` kwarg). Visually verified 4 figures; values trace to data (Forge-confirmed header+body=ciphertext_bytes, tamper detected/total consistent).
- **Prose (ISC-R5d):** abstract/intro/methodology expanded — acronym definition, ZIP-layout tree diagram, per-track binary-header byte diagram (token-driven, cannot drift from frozen layout), worked CLI example. Security-overclaim sweep clean (no tamper-proof/non-repudiation/unforgeable).
- **Worked CLI example (ISC-R5e):** run end-to-end from clean tmpdir — `genkey`→32B 0600 key, `pack --observability 3`→zip, `verify -k`→`ok=True integrity=key-authenticated`, `unpack`→3 tracks. Flags match `src/cli.py` (no phantom `-d`).
- **FAQ correction (ISC-R5f):** stale "stdlib-only crypto" Q replaced with accurate "audited `cryptography` library" answer; verified against `crypto_gcm.py`/`crypto.py` (AESGCM + library HKDF on data path).
- **Gate (ISC-R5g):** `pytest --cov=src --cov-fail-under=90` → **182 passed / 92.94%**, exit 0 (was 182/92.86 baseline). PDF `entofile_combined.pdf` **32 pages** (was 28), 4-pass+bibtex, **zero `??` dangling refs**.
- **Advisor (Rule 2, E4 HARD):** ran — confirmed format-freeze honest, ORCID valid; flagged CLI-example execution + prose over-claim sweep (both closed above) + DOI-versioning for any re-publication (deferred: local-only working copy, not re-published in this task).
- **Cross-vendor (Forge GPT-5.4, read-only, Rule 2a):** **PASS** — independently reproduced 182/92.95%, verified all 7 change-items on disk, no phantom flag, no red captions, no bare literals, acronym honest, FAQ correction accurate (incl. HKDF).

**Follow-up (superseded):** this historical note assumed any re-publication
would remain on 0.2.0. The current 0.4 release candidate instead uses 0.4.0 as
the default wire format and should receive release metadata consistent with that
current contract.

---

### Round 1–4 (security hardening)

Baseline → final: **142 tests / 92.05%** → **153 tests / 92.41%** (full `pytest --cov=src --cov-fail-under=90`, exit 0). ruff check + format (line-length 120, repo standard) clean on all changed files; changed-src mypy clean (only pre-existing `ontology.py:65` remains, untouched).

- ISC-1/18 (F1): `test_forged_container_is_not_reported_key_authenticated` + live repro — forged container (corrupt+blanked+forged-proof) keyless → `integrity:"unverified"`; `require_integrity=True` → `ok:False`. **CLI** `verify -i evil.zip` now `exit 1` (was 0): stderr `{"event":"verify_failed","ok":false,"integrity":"unverified"}`.
- ISC-2/4/5: `test_keyed_verify_authenticates_intact_container` (key→`key-authenticated`), `test_keyless_intact_container_is_digest_only` (legit AUDITABLE keyless→`digest-only`,`ok:true`).
- ISC-3/6: `test_blanked_digests_no_key_fails_require_integrity` — blanked digests keyless→`unverified`,`ciphertext_digests_present:false`; `require_integrity`→`ok:false`.
- No-downgrade (advisor): `test_keyed_verify_cannot_be_downgraded_by_header_mutation` — key + blanked digests + `observability_level=0` → still `key-authenticated`; key + corrupted ciphertext → `ValueError: authentication tag mismatch` (fail closed). Live probe: integrity derived from decrypt attempt, never from a header field.
- ISC-7 (F4): `test_safe_read_member_bounds_actual_decompressed_bytes`; live probe — `read(max=1024)` on a 300 MiB-declared member: 0.1 ms, 0.1 MiB peak (bounded *during* decompression).
- ISC-8: `test_validate_zip_archive_rejects_aggregate_overflow` — declared aggregate > 512 MiB → `ValueError ... aggregate limit`.
- ISC-9 (F8): `test_hkdf_production_empty_salt_path_is_pinned` + existing `test_crypto_vectors.py`; Forge independently re-derived RFC 5869 HKDF-SHA256, 64 vectors, 0 mismatches. Library raises at >255×32 octets (unreachable; ENTO derives only 32).
- ISC-10 (F5): `test_decrypt_does_not_mask_non_crypto_errors` — tamper→`authentication tag mismatch`; shape error→its own `nonce must be 16 bytes` (not masked).
- ISC-11/12/13: threat-model "Integrity model" + "Nonce and AAD" sections; TM-002/TM-003/MITRE rows corrected; `docs/security.md` integrity-basis + ZIP-limits table; `docs/claim_ledger.md` integrity caveat.
- ISC-14/15/16/17: 153 green / 92.41%; ruff+format clean (changed files); changed-src mypy clean; all fixtures + observability levels round-trip (existing suite green).

**Cross-vendor (Forge GPT-5.4, read-only):** CONCERNS → 3 findings all fixed: (1) HIGH CLI call-site fail-open (`cmd_verify` now `require_integrity=not --allow-unverified`), (2) `proof_consistent` presence-alias removed, (3) stale "HMAC" doc lines corrected. Forge independently confirmed HKDF byte-identity, GCM-authenticates-every-track, and `safe_read_member` bound.

**Advisor (Inference.ts):** wire-freeze + document = correct; flagged the key-present downgrade question (verified closed above) and label precision (docstring/threat-model now scope `key-authenticated` to plaintext + track_id, not header fields). Noted `--auto-state` loaded a stale unrelated session — artifacts above are the real tokens for this work.

---

## Completed cycle — 2026-07-15 — shared-boundary synchronization

The historical rounds above remain immutable evidence. This section is the active
0.4.0 synchronization and research contract. The current worktree started with
main equal to origin/main, but with an intentional hardening batch awaiting review,
static cleanup, and landing. Existing wire profiles remain unchanged; additive
forward-format work is recorded in the active cycle below.

### Current goal

Reconcile the local main checkout with origin/main, finish and test the shared
paths, structured-data, error, and test-result boundaries, refresh the project
ledger, and land only regenerated evidence. Advance the research agenda without
turning design hypotheses into interoperability or security claims.

### Criteria and anti-criteria

- [x] ISC-19: main synchronization is fast-forward-only and final main...origin/main is 0/0.
- [x] ISC-20: the complete Ruff command is clean.
- [x] ISC-21: the complete mypy command is clean.
- [x] ISC-22: the live test gate passes with coverage at or above 90 percent.
- [x] ISC-23: fresh analysis reports tamper detection 1.0 and validates all outputs.
- [x] ISC-24: freshly generated conformance fixtures verify 7/7.
- [x] ISC-25: figure layout QA verifies every registered figure.
- [x] ISC-26: the release manifest is regenerated and has no required missing entries.
- [x] ISC-27: public error imports, the ConfigError alias, multi-root paths, and structured readers are covered by tests.
- [x] ISC-28: ISA, TODO, tasks.yaml, docs, experiment_plan.yaml, and release metadata describe the same current state.
- [x] ISC-29: every research question has three competing hypotheses, a control, metrics, falsification, and stopping rules.
- [x] ISC-30 anti-criterion: no local metadata is presented as proof that public endpoints are live.
- [x] ISC-31 anti-criterion: no force-push, wire-format mutation, unreviewed mixed staging, or side-file-only certification.

### Canonical gate sequence

The certifying sequence is: lint; mypy; scripts/run_tests.py; fresh analysis;
conformance generation and verification; figure layout; manuscript variables;
SBOM and release bundle; no-mock and unresolved-token checks; certifying
publication readiness; separate live public endpoint probe; documentation and
ledger consistency; diff check; clean status; and main/origin parity.

Generated reports are evidence, not inputs to skip the generating command. A
report is fresh only when the command that owns it completed successfully in the
current checkout. Local readiness is therefore distinct from external public-
promotion readiness, which requires endpoint evidence recorded separately.

### Architecture contract

- ProjectPaths is the single path value for project roots, output roots, reports,
  conformance fixtures, release artifacts, and manuscript integration.
- Structured readers reject duplicate JSON keys, non-mapping roots, missing required
  files, and symlinked inputs; atomic writers refuse symlink replacement.
- Domain exceptions are exported from src, retain ValueError compatibility where
  existing callers depend on it, and distinguish policy, integrity, configuration,
  pipeline, and artifact failures.
- Facades and existing 0.2.0–0.4.0 vectors remain stable. Larger container,
  publication, conformance, and figure splits require seam tests before migration.

### Research contract

The source of truth is experiment_plan.yaml plus docs/research/agenda.md. The
agenda covers independent conformance and schema negotiation; bounded-memory
streaming; observability leakage; cryptographic vectors and padding; KMS/HSM
custody; signed manifests, SBOM, provenance, and reproducible builds; and related
ecosystem exports. Each cycle must state sample or repetition rationale, controls,
exact metrics, falsification criteria, stopping rules, and limits on what results
prove. No related-format export may be described as equivalent without an
independent implementation result.

### Current-cycle decisions

- The repo-specific Python/uv workflow overrides generic language defaults because
  it is part of the project contract.
- Direct synchronization is authorized, but only with fetch, review, fast-forward,
  conflict-aware replay, validation, commit, push, and final parity checks; force
  push is prohibited.
- All existing local hunks are presumed intentional only until every hunk is
  reviewed and classified. Implementation, tests, and ledger changes are staged
  as separate review groups.
- The requested Forge cross-vendor pass was unavailable because the environment
  reported codex CLI not found at ~/.bun/bin/codex. Inline RedTeam review and
  repository evidence are the substitution; no cross-vendor pass is claimed.
- Public endpoint failure remains an explicit blocker and is never inferred away
  from local metadata or a cached release report.

### Current-cycle verification record

The current working tree has passed 448 tests at 90.38 percent coverage,
Ruff, mypy, fresh analysis with 2,400 rows and tamper rate 1.0, conformance
8/8, figure layout 21/21, manuscript hydration, package build/install/import
smoke, equation-fidelity, no-mock, and repository consistency checks. The
display-only local publication gate is green. The certifying live publication
gate was also attempted, but its pytest child exceeded the 600-second bound
under shared-host contention and failed closed; this is an infrastructure
verification blocker, not evidence of a test failure. No certifying live-gate
pass or clean-head release readiness is claimed until that command is rerun.
The live public endpoint probe returned HTTP 200 for GitHub, DOI, and Zenodo;
the metadata checker correctly reports source-dirty blockers while this tree is
uncommitted. Final clean status and main/origin parity remain landing checks.

## Current cycle — 2026-07-15 — opt-in 0.5.0 profile

This is the active format, documentation, and manuscript cycle. It preserves the
stable 0.4.0 writer default and every 0.2.0-0.4.0 compatibility vector while
adding one explicit forward profile. No release claim is made from generated
side files alone; all evidence below must be regenerated on the final head.

### Problem

The 0.4.0 AEAD contract binds the format label and track identifier, but the
manifest context that interprets a track remains outside the GCM associated data.
A public party can therefore rewrite unkeyed interpretation metadata and recompute
public digests/proof bytes. Keyed verification still protects ciphertext, but the
format has no profile that authenticates the exported interpretation context.

### Vision

ENTO has a conservative, opt-in profile whose track tags bind the exact exported
manifest view, with a fixed vector, a redaction-level matrix, fail-closed parsing,
and documentation that distinguishes keyed authenticity from public consistency.
The project can then study cross-language interoperability and signing without
pretending that a local Python implementation is already a standard.

### Out of Scope

- Changing the stable 0.4.0 default or mutating the 0.2.0-0.4.0 wire contracts.
- Streaming, random access, KMS/HSM custody, external signatures, SBOM provenance,
  or reproducible package builds; these remain research questions and deployment
  controls.
- Claiming RFC 8785/JCS or independent-language interoperability from the current
  canonicalization profile.
- Treating a public `manifest_binding`, proof chain, or digest as origin proof.

### Principles

- Keep the default boring: forward behavior is explicit via `--format 0.5.0`.
- Authenticate the exported view actually emitted, not an unseen internal view.
- Keep the circular ciphertext-digest field outside the binding; GCM authenticates
  bytes and the digest remains a separate unkeyed corruption check.
- Reject malformed, non-finite, duplicate-key, missing-binding, stale-binding,
  and incompatible-version inputs before plaintext release.
- Encode every security and scientific limitation in tests, docs, and the agenda.

### Constraints

- `format_version` remains version-dispatched and unknown values fail closed.
- 0.5.0 uses the existing ZIP/member layout, 12-byte nonce, AES-256-GCM,
  per-track HKDF key, and PADMÉ body encoding.
- A 0.5.0 binding is lowercase SHA-256 over sorted compact UTF-8 JSON of the
  emitted manifest projection; strings are NFC-normalized, non-finite numbers are
  rejected, and integral floats are emitted as integers.
- Export-level changes for 0.5.0 require repacking because the selected view is
  authenticated as GCM context.
- The project continues to use its Python/uv contract and thin scripts over `src`.

### Goal

Implement and document the 0.5.0 authenticated-manifest-context profile, update
the manuscript's formal/security model and forward-format claims, add a complete
research protocol for validation, regenerate the certifying artifact surface, and
land the result on synchronized `main` without force-pushing.

### Criteria and anti-criteria

- [x] ISC-32: default 0.4.0 and all 0.2.0-0.4.0 vectors remain unchanged.
- [x] ISC-33: 0.5.0 pack, unpack, inspect, verify, and byte-pack paths share one
  tested preparation/validation boundary.
- [x] ISC-34: canonical binding and fixed AEAD vectors pass; manifest mutation,
  rebinding, relabeling, missing/invalid binding, and empty-container controls fail.
- [x] ISC-35: all observability export levels bind the exact emitted view, and the
  returned pack manifest equals the manifest on disk.
- [ ] ISC-36: Ruff, mypy, full pytest/coverage, analysis, conformance, figure QA,
  manuscript hydration, package smoke, and release-bundle gates pass freshly.
- [x] ISC-37: format, security, architecture, migration, operator, threat-model,
  related-format, and manuscript docs agree on default/forward/compatibility state.
- [x] ISC-38: research agenda RQ-1 through RQ-8 are machine-readable and specify
  competing hypotheses, controls, metrics, falsification, stopping, and limits.
- [x] ISC-39 anti-criterion: no public digest is described as a signature or proof
  of origin, and no independent interoperability claim is made prematurely.
- [x] ISC-40 anti-criterion: no stale 0.2.0/0.4.0 default wording remains in active
  format guidance, and no generated report substitutes for its owning command.
- [ ] ISC-41 anti-criterion: no mixed unreviewed staging, force-push, or dirty-head
  release certification is accepted.

### Test Strategy

| surface | required control | evidence |
| --- | --- | --- |
| Canonicalization | fixed bytes, Unicode NFC equivalence, integral-float equivalence, non-finite rejection | unit/vector tests |
| Binding | changed creator, descriptor, export view, stale/missing/wrong binding, relabel/downgrade | manifest and container negative tests |
| AEAD | fixed key/nonce/tag/ciphertext and rebound-manifest failure | crypto vector and keyed unpack tests |
| Compatibility | existing legacy vector suite and version matrix | 0.2.0-0.4.0 tests/conformance |
| Pipeline | fresh analysis, conformance, figure, manuscript, SBOM, release, publication gates | owning scripts and reports |
| Documentation | token, claim-ledger, taskboard, no-mock, unresolved-token, and link consistency | repository checks |

### Features

| feature | status | seam |
| --- | --- | --- |
| `manifest_binding` canonical projection | implemented | `src/manifest_binding.py` |
| 0.5.0 version/AAD dispatch | implemented | `src/crypto.py`, `src/track.py` |
| exported-view pack orchestration | implemented | `src/container.py`, `src/observability.py` |
| conditional schema + fail-closed readers | implemented | `data/ento_manifest_schema.json`, `src/manifest.py` |
| vectors and negative controls | implemented | `tests/test_format_0_5_0.py` |
| format/manuscript/research documentation | implemented | `docs/`, `manuscript/`, `experiment_plan.yaml` |
| regenerated release evidence and synchronized landing | pending | gate sequence below |

### Decisions

- Keep `FORMAT_VERSION` and package version at the stable 0.4.0 contract; expose
  `FORMAT_VERSION_NEXT = "0.5.0"` as explicit opt-in.
- Bind the exported projection and exclude only `sha256_ciphertext`, because the
  digest is computed after encryption and would create circular state; document
  this as redundant unkeyed metadata rather than hidden authentication.
- Use a strict ENTO canonicalization profile now and preregister cross-language
  parity before claiming JCS or interoperability.
- Return the emitted/redacted manifest from pack APIs so public return values and
  on-disk bytes cannot disagree at 0.5.0 export levels.
- Treat two independent read-only review passes as adversarial design input; they
  found the provisional-validation, legacy-field, canonicalization, return-value,
  and rebound-test seams now covered by remediation/tests. No independent runtime
  implementation is claimed.

### Changelog

- Added the 0.5.0 forward profile, conditional manifest field, canonical binding,
  version-aware AAD, and fixed vector.
- Added export-level binding tests and explicit negative controls for mutation,
  rebinding, relabeling, empty containers, wrong/missing/legacy bindings, and
  redundant ciphertext-digest behavior.
- Updated root/project docs, migration/security/threat-model material, manuscript
  formalism and limitations, claim ledger, release inputs, TODO, taskboard, and
  preregistered RQ-8.
- Reviewer finding: provisional binding validation must target the emitted view,
  not the full internal manifest. Remediated by validating the filtered manifest
  at the ZIP boundary and returning that same view.

### Verification

Verification is partially complete on the current working tree. The canonical
sequence for the final clean-head certification is:

```text
uv run ruff check --no-cache src/ scripts/ tests/
uv run --extra dev mypy --no-incremental src/
uv run python scripts/run_tests.py
uv run python scripts/ento_analysis.py
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
uv run python scripts/check_figure_layout.py
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/export_sbom.py
uv run python scripts/build_release_bundle.py
uv run python scripts/audit_publication_readiness.py --check
uv run python scripts/check_public_promotion_metadata.py --check --live-public-endpoints
```

The final record must state exact test/coverage counts, analysis row/tamper
results, conformance and figure counts, local readiness, live endpoint results,
`git diff --check`, clean status, and `main...origin/main`. Endpoint failure is
an explicit external-public-promotion blocker.
