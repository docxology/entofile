# Security verification {#sec:security_verification}

ENTO separates **integrity verification** from **decryption**. Operators and CI should treat third-party `.ento.zip` archives as hostile until `verify` succeeds.

The verification model deliberately avoids a common false comfort: a parseable
ZIP and matching unkeyed digests are not the same as adversarial authenticity.
An attacker who can rewrite the archive can also rewrite unkeyed hashes. A
successful keyed AEAD check is different: the GCM tag can be recomputed only by a
party with the correct per-track key and associated-data inputs.
The repository can prove local parser discipline, keyed AEAD failure on tamper,
and artifact/render consistency. It cannot, by itself, prove who built a public
release, where the master key was stored, or whether an operator routed failures
to a SOC; those are external controls named rather than implied.

## Verify-before-unpack

The CLI subcommand `verify -i container.ento.zip` checks JSON Schema, ZIP member limits, exact member-set equality with the manifest, per-track ciphertext digests, and optional proof binding—without decrypting. Supply `-k master.key` to confirm plaintext SHA-256 fields when the export level includes them.

```bash
uv run python -m src.cli verify -i container.ento.zip
uv run python -m src.cli verify -i container.ento.zip -k master.key --require-proof
```

`unpack` repeats the same checks before writing plaintext. Failures emit a structured JSON audit line on stderr (event `ento.verify.failed`) for log aggregation.

## Integrity assurance levels

`verify` reports exactly what it established, never more. Its `integrity` field takes one of {{COUNT_INTEGRITY_LEVELS}} values:

- **key-authenticated** — every track decrypted under AES-256-GCM (master key supplied) and all plaintext digests matched. This is the only level that resists an adversary who controls the container bytes; it authenticates the track plaintext and the track identity (bound through per-track key derivation, and through AAD for AAD-bound formats), not the unkeyed manifest header fields.
- **digest-only** — no key supplied, but every ciphertext digest was present and matched. This detects *accidental* corruption only: the manifest digests and the hash-chained proof are unkeyed, so a motivated attacker who rewrites the archive can recompute them.
- **unverified** — no key, and at least one ciphertext digest was absent (a redacted or stripped manifest); nothing about the track bytes was checked.

`verify` fails closed by default—an `unverified` result exits non-zero unless `--allow-unverified` is given. The proof chain is a consistency structure binding a proof to a manifest, **not** an authentication of origin: adversarial integrity comes only from decrypting with the master key.

## ZIP ingestion limits

Reference defaults in `src/security.py` cap archive size, member count, per-member **actual decompressed** bytes (bounded at read time rather than trusting the attacker-declared `file_size`), and an aggregate decompressed budget; duplicate member names are rejected before the membership check so a second blob cannot ride inside a duplicated allowed name. Oversize or malformed archives raise `ValueError` before crypto runs. Tests build real ZIP fixtures under `tmp_path` (no monkeypatch).

## Tamper rejection outcomes

![{{FIG_CAPTION_TAMPER_DETECTION}}](../output/figures/tamper_detection.png){#fig:tamper_detection width={{FIGURE_WIDTH}}%}

[@fig:tamper_detection] reports tamper-injection outcomes across the full benchmark matrix as a stacked share of detected versus missed rejections. Benchmark validation requires tamper detection rate {{RESULT_TAMPER_DETECTION_RATE}} with status {{RESULT_BENCHMARK_VALIDATION_STATUS}} before release.

## Container verification report

The analysis pipeline writes `output/reports/container_verification.json` with per-sample `verify_container` outcomes. `validate_generated_outputs()` requires all entries `ok: true` alongside {{RESULT_TAMPER_DETECTED_COUNT}} tamper detections at rate {{RESULT_TAMPER_DETECTION_RATE}} in `benchmark_validation.json`.

Latest gate sample: {{RESULT_CONTAINER_VERIFY_SAMPLE}}. Aggregate status: {{RESULT_CONTAINER_VERIFY_OK}}.

## Cryptography and the format ladder

All formats use AES-256-GCM ({{CRYPTO_BACKEND_DEFAULT}}) via the audited `cryptography` library with HKDF-derived per-track keys. The default writer emits {{FORMAT_VERSION}}; {{COUNT_COMPATIBILITY_FORMATS}} compatibility formats ({{FORMAT_VERSIONS_COMPATIBILITY}}) are version-dispatched and remain readable/writable via `pack --format`. The opt-in forward profile {{FORMAT_VERSION_NEXT}} adds {{FORMAT_NEXT_BINDING_DESCRIPTION}}:

![{{FIG_CAPTION_FORMAT_LADDER}}](../output/figures/format_ladder.png){#fig:format_ladder width={{FIGURE_WIDTH}}%}

| `format_version` | Nonce | Associated data | Length-hiding |
| --- | --- | --- | --- |
| {{FORMAT_VERSION}} (default) | {{NONCE_BYTES}}-byte | binds `format_version` + track id | PADMÉ padding [@nikitin2019purb] |
| {{FORMAT_VERSIONS_COMPATIBILITY}} | version-dispatched | no-AAD through AAD-bound compatibility profiles | compatibility-dependent |
| {{FORMAT_VERSION_NEXT}} (opt-in) | {{NONCE_BYTES}}-byte | {{FORMAT_NEXT_AAD_TEMPLATE}} | PADMÉ padding [@nikitin2019purb] |

![{{FIG_CAPTION_FORMAT_COMPATIBILITY_MATRIX}}](../output/figures/format_compatibility_matrix.png){#fig:format_compatibility_matrix width={{FIGURE_WIDTH}}%}

![{{FIG_CAPTION_LENGTH_LEAKAGE_PROFILE}}](../output/figures/length_leakage_profile.png){#fig:length_leakage_profile width={{FIGURE_WIDTH}}%}

![{{FIG_CAPTION_CONFORMANCE_OUTCOMES}}](../output/figures/conformance_outcomes.png){#fig:conformance_outcomes width={{FIGURE_WIDTH}}%}

[@fig:format_ladder] and [@fig:format_compatibility_matrix] are the release-candidate guardrails: manuscript version {{PAPER_VERSION}} documents stable default wire format {{FORMAT_VERSION}}, the compatibility formats remain explicit rather than implicit, and {{FORMAT_VERSION_NEXT}} remains opt-in. Binding `format_version` in the associated data makes a format downgrade (including a padded↔unpadded swap) fail the GCM tag rather than mis-parse. The {{FORMAT_VERSION_NEXT}} binding additionally covers the canonical exported manifest context, so keyed verification rejects metadata reinterpretation; its public digest is not an origin signature. [@fig:length_leakage_profile] bounds the length claim: default padding hides exact length only to PADMÉ buckets, while ZIP names and bucketed sizes remain visible. [@fig:conformance_outcomes] connects the supported-format claim to deterministic known-good and known-bad fixtures. Pinned vectors: `data/test_vectors/hkdf_regression.json`, `aes256_gcm_regression.json`, and the fixed manifest-context vector in `tests/test_format_0_5_0.py`. See [@sec:methodology].

## Nation-state deployment checklist

![{{FIG_CAPTION_SECURITY_CONTROL_MATRIX}}](../output/figures/security_control_matrix.png){#fig:security_control_matrix width={{FIGURE_WIDTH}}%}

Production hardening beyond this reference implementation is documented in `docs/nation_state_roadmap.md` against NIST zero-trust, SSDF, key-management, and supply-chain-risk guidance, SLSA provenance levels, Sigstore signing, in-toto-style supply-chain attestations, CycloneDX SBOMs, MITRE ATT&CK detection mapping, and post-quantum standards work [@nist2020zerotrust; @nist2022ssdf; @nistsp80057pt1r5; @nist2022sp800161r1; @slsa2024levels; @sigstore2026cosign; @torresarias2019intoto; @cyclonedx2026spec; @mitre2026attack; @nist2024mlkem; @nist2024mldsa]. [@fig:security_control_matrix] marks what this repository enforces (ZIP limits, verify-before-unpack, schema gates, deterministic artifact checks), what is partial (telemetry and release documentation), and what remains external/residual (artifact signing policy, HSM/KMS custody, SOC routing). Manuscript release {{PAPER_VERSION}} documents format **{{FORMAT_VERSION}}** as the default on-disk contract, with {{FORMAT_VERSIONS_COMPATIBILITY}} retained as compatibility formats.
