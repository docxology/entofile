# Limitations and threat model {#sec:limitations}

ENTO is a reference container for reproducible research bundles—not a full data-management platform or enterprise DRM system. This section states explicit limits and the adversary model the implementation addresses.

## Scope limits

- **No streaming partial decrypt**: tracks unpack as whole ZIP entries; HDF5/Zarr-style chunk random access is out of scope [@hdf5_tr; @zarr_v2].
- **No online policy engine**: unlike OpenTDF [@opentdf2024], decryption does not consult remote attribute authorities.
- **ZIP metadata leakage**: file names (`tracks/eeg.ento`) and compressed sizes remain visible at every level. Observability redaction applies only to per-*track* manifest fields (type, digests, resolution, `byte_length`), and not uniformly: `byte_length` is redacted (zeroed) **only at the sealed level**, whereas type/digests are redacted at lower levels too — so a non-sealed manifest still publishes `byte_length`. The manifest *header* — `creator`, `created` timestamp, and `format_version` — is carried in cleartext even at the sealed level, so it must not hold sensitive content (strip or generalize `creator`/`created` before sealed distribution if they are sensitive).
- **Plaintext length**: AES-GCM is length-preserving for the bytes supplied to encryption, so unpadded compatibility formats reveal exact plaintext length from member size. Default {{FORMAT_VERSION}} PADMÉ-pads the encrypted body, so the on-disk ciphertext member size reveals only a coarse bucket. This padding addresses the *member-size* channel only: at non-sealed observability levels (including the default AUDITABLE) the manifest still carries the per-track `byte_length` field in cleartext, which discloses exact plaintext length directly — fully nullifying PADMÉ for those containers. No export level hides length exactly. Sealed export redacts the `byte_length` field to zero, but the on-disk member size still reveals the PADMÉ *bucket* (coarse for large payloads, near-exact for small ones, e.g. distinct small lengths can fall in distinct buckets); and for unpadded compatibility formats the member size reveals exact length at every level. The strongest available length-hiding is therefore sealed export of a padded format, and even then only to bucket granularity.
- **Archival-system boundary**: OAIS repository responsibilities and PREMIS preservation metadata are external to the ENTO file format [@ccsds2024oais; @premis2015]. ENTO can be stored in those systems, but this repository does not implement appraisal, accession policy, preservation planning, rights management, repository certification, or long-term media migration.
- **Evidence provenance**: release outputs are real executions of the repository pipeline, but benchmark and conformance inputs include deterministic fixtures, a synthetic throughput stress track, and deterministic test vectors. See [`docs/evidence_provenance.md`](../docs/evidence_provenance.md).
- **Format ladder**: {{FORMAT_VERSION}} is the stable default on-disk contract. The opt-in {{FORMAT_VERSION_NEXT}} profile adds authenticated exported-manifest context; compatibility formats {{FORMAT_VERSIONS_COMPATIBILITY}} remain version-dispatched and readable/writable alongside it. Older experimental ciphertext layouts are out of scope for this release.

## Threat model

| Adversary capability | Mitigation | Residual risk |
| --- | --- | --- |
| Tamper ciphertext or tags | AES-256-GCM authenticates on key-based unpack/verify (the integrity anchor) [@nistfips197; @dworkin2007gcm; @mcgrew2004gcm] | Keyless digest check detects accidental corruption only |
| Swap manifest after export | Key-based decrypt mismatch; {{FORMAT_VERSION_NEXT}} manifest binding; `verify_proof_export` consistency check [@rfc8785; @merkle1988digital; @haber1991timestamp] | Unkeyed proof and public binding are forgeable; sign externally for origin |
| Misreport verification assurance | `verify` reports `key-authenticated`/`digest-only`/`unverified` and fails closed by default | `--allow-unverified` opt-out is the operator's risk |
| Escape output path via track id | IDs `[a-z0-9._-]+`; `safe_output_path` | Path traversal remains the class being excluded [@cwe22] |
| ZIP bomb / extra members | Actual-byte read bound + aggregate budget; member-set equality; duplicate-name rejection | Data-amplification limits are tunable per deployment [@cwe409] |
| Infer plaintext length from track size | Sealed export zeroes manifest `byte_length`; **{{FORMAT_VERSION}} PADMÉ-pads** the ciphertext member | Bucket size remains visible; the cleartext manifest `byte_length` reveals exact length at every non-sealed level (so PADMÉ length-hiding applies only under sealed export); unpadded compatibility formats also reveal exact length from member size |
| Downgrade hardened format | {{FORMAT_VERSION}} and AAD-bound compatibility formats bind `format_version` in associated data | Legacy no-AAD compatibility relies on track-key binding and external policy |
| Guess master key | 256-bit key; per-track HKDF separation | Key storage outside ENTO scope |
| Learn types at sealed export | Level 0 strips type URIs and hashes | Track filenames may hint content |
| Replay old manifest | Not addressed | External timestamping |

Full AppSec table and MITRE ATT&CK mapping: `docs/entofile-threat-model.md`. Operational checklist: [@sec:security_verification].

For the planned public repository, the same boundary applies: GitHub release
signatures, SBOM attestations, KMS/HSM key custody, and SOC routing can strengthen
deployment assurance, but they are not properties of an `.ento.zip` file unless
the operator adds those controls around it. NIST key-management guidance and
supply-chain-risk guidance are therefore cited as deployment requirements, not
as claims that this offline reference repository already implements a vault,
release attestation service, or provenance control plane [@nistsp80057pt1r5;
@nist2022sp800161r1].

## Security hardening and format evolution

The reference implementation layers three honesty- and hardening-oriented guarantees on the {{FORMAT_VERSION}} default:

1. **Honest verification.** Keyless verification is corruption-detection only; the manifest digests and hash-chained proof are unkeyed and forgeable by anyone who controls the bytes. Adversarial integrity comes solely from AES-256-GCM authentication under the master key. `verify` surfaces this distinction in its `integrity` field and fails closed on unverifiable input ([@sec:security_verification]).
2. **Format {{FORMAT_VERSION}}** uses the SP 800-38D-standard {{NONCE_BYTES}}-byte nonce and binds `format_version` and the track id as AEAD associated data [@rfc5116; @dworkin2007gcm], so a format downgrade or cross-track relabel fails authentication. The opt-in {{FORMAT_VERSION_NEXT}} profile additionally binds the canonical exported manifest context; a public binding is not an origin signature. This is also why nonce uniqueness is a hard invariant rather than a performance detail: repeated GCM nonces enable practical forgery and confidentiality failures [@joux2006forbidden; @bock2016nonce].
3. **Default PADMÉ padding** [@nikitin2019purb] length-prefixes each plaintext and pads it to a coarse bucket before encryption, so the on-disk ciphertext size reveals only the bucket (overhead O(log log L)), not the exact length. This mitigates the plaintext-length side-channel for deployments where length analysis is in scope; it hides length to bucket granularity, not perfectly. Padding addresses the ciphertext member-size channel only, and only to bucket granularity (never exact): the manifest `byte_length` field still publishes exact length at non-sealed observability levels, and even sealed export leaves the padded member size revealing the bucket. The strongest length-hiding is sealed export of a padded format, bounded to bucket granularity.

If an operator cannot rely on fresh random nonces per per-track key, a
nonce-misuse-resistant AEAD such as AES-GCM-SIV is a future-format candidate, not
an ENTO {{FORMAT_VERSION}} behavior [@rfc8452].

## Nation-state pillar status

| Pillar | Status |
| --- | --- |
| Verify-before-use (ZTA) | `verify` CLI + `container_verification.json` gate, aligned with zero-trust verification principles [@nist2020zerotrust] |
| Cryptography | GCM default {{FORMAT_VERSION}} plus compatibility formats {{FORMAT_VERSIONS_COMPATIBILITY}}; PQC standards inform external transport/signing rather than this symmetric file envelope [@nistfips197; @nistfips1804; @dworkin2007gcm; @nist2024mlkem; @nist2024mldsa] |
| Supply chain | Optional CycloneDX SBOM (`scripts/export_sbom.py`); external signing/provenance should use NIST C-SCRM, SLSA/Sigstore, COSE, or in-toto-style release controls [@cyclonedx2026spec; @nist2022sp800161r1; @slsa2024levels; @sigstore2026cosign; @rfc9052; @torresarias2019intoto] |
| Detection | Structured verify failure JSON; deployment SOC mapping can use MITRE ATT&CK review coverage [@mitre2026attack] |

See `docs/nation_state_roadmap.md` for HSM, signing, and audit integrations.

## Key handling

Master keys are {{MASTER_KEY_BYTES}} random bytes from `genkey`. The CLI sets mode `0600` on Unix when writing key files. Run `verify` before `unpack` on third-party archives. Escrow, cryptoperiods, access control, and HSM/KMS policies are deployment concerns governed outside ENTO's file format [@nistsp80057pt1r5] (`docs/security.md`).

## Non-goals

CADF audit streams [@cadf2013], FAIR repository automation [@wilkinson2016fair], OAIS/PREMIS preservation operations [@ccsds2024oais; @premis2015], and RO-Crate aggregation [@rocrate2024; @soilandreyes2022rocrate] are complementary--ENTO specifies the encrypted track envelope they might wrap.

Future work may add chunked tracks, external KMS hooks, and formal interoperability tests without changing the {{FORMAT_VERSION}} on-disk contract.
