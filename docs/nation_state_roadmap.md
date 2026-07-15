# Nation-state hardening roadmap — entofile 0.4 RC

ENTO is an offline research-container reference implementation, not a hosted service.
The 0.4 paper release candidate therefore treats nation-state posture as a
deployment matrix: what the repo enforces, what the manuscript documents honestly, and
what a high-assurance operator must add outside the repo.

Baseline operations: [`security.md`](security.md). AppSec model:
[`entofile-threat-model.md`](entofile-threat-model.md). Red-team ledger:
[`redteam_publish_0.4.md`](redteam_publish_0.4.md).

## Pillar status

| NationStateSecurity pillar | Repository-enforced controls | Partial / documented controls | External / residual controls |
| --- | --- | --- | --- |
| Zero trust / verify before use | `verify_container`, CLI `verify`, verify-before-unpack path, duplicate-member and member-set gates | `container_verification.json` is keyless and therefore digest-only; manuscript distinguishes assurance levels | Operators must run keyed verify before trusting third-party containers; no network ZTA plane exists in this offline CLI |
| Cryptographic discipline | `cryptography` AES-256-GCM, HKDF-SHA256, format dispatch, pinned HKDF/GCM vectors, default `0.4.0` AAD binding and PADMÉ padding [@nistfips197; @nistfips1804; @rfc5116; @dworkin2007gcm; @mcgrew2004gcm; @krawczyk2010hkdf; @nikitin2019purb] | Legacy `0.2.0` remains readable with 16-byte nonce/no AAD; bucket-size leakage remains in padded formats; nonce reuse remains catastrophic if CSPRNG assumptions fail [@joux2006forbidden; @bock2016nonce] | FIPS-validated module selection, HSM/KMS custody, key rotation, PQC transport/signing, and nonce-misuse-resistant future formats remain deployment or future-format controls [@nistsp80057pt1r5; @nist2024mlkem; @nist2024mldsa; @rfc8452] |
| Supply chain integrity | `uv.lock`, no-mock tests, artifact manifest, claim ledger, CycloneDX SBOM export | SBOM exists as local artifact; release provenance is described but not emitted by this repo | Sign source, SBOM, PDF, and packages with Sigstore/cosign or equivalent; target SLSA Build L3+ and in-toto-style provenance in public CI [@nist2022sp800161r1; @torresarias2019intoto] |
| Detection and telemetry | Structured CLI verify failure JSON, validation reports, adversarial security tests | ATT&CK mapping is review coverage, not live detection coverage | Forward verify/audit events to SIEM; add detection-as-code, runbooks, MTTD/MTTR ownership |
| Identity and key handling | `genkey` CSPRNG, 32-byte key check, Unix `0600`, keys never embedded in ENTO ZIPs | Local file permissions reduce accidental exposure only | Enforce FIDO2/JIT on operator hosts, KMS/HSM storage, audited key use, cryptoperiods, rotation, and break-glass policy [@nistsp80057pt1r5] |
| Data protection | Per-track AEAD, observability filters, proof omission at sealed level, default PADMÉ support in `0.4.0` | ZIP names and padded member sizes remain visible; `0.2.0`/`0.3.0` leak exact plaintext length | Classify datasets; avoid unpadded compatibility formats for length-sensitive sealed exports; add DLP/retention outside repo |
| Operational resilience | Full pytest/coverage gate, tamper gate, artifact validation, deterministic benchmark fingerprint | Rendered outputs and reports can be regenerated from the working tree | Signed backups, restore drills, artifact escrow, disaster-recovery ownership |
| Secure SDLC | Threat model, RedTeam ledger, claim-ledger tests, figure/caption gates, warning hygiene | Local tests provide evidence but not public CI policy | Branch protection, CODEOWNERS for crypto/build paths, SCA/secret scans, signed commits, vulnerability response process |

## Format posture

- Default write format is **0.4.0**: 12-byte GCM nonce, AEAD AAD binding of
  `format_version` and `track_id`, and PADMÉ length-padding.
- Compatibility formats remain **0.2.0** (16-byte nonce, no AAD), **0.3.0**
  (12-byte nonce + AAD), and **0.3.1** (0.3.0 plus PADMÉ length-padding).
- The 0.4 manuscript release documents that default ENTO `format_version`
  **0.4.0** while keeping prior formats under explicit version dispatch.

## Standards alignment

| Standard / framework | ENTO interpretation |
| --- | --- |
| NIST SP 800-207 | Local zero-trust analogue is verify-before-unpack with no implicit trust in ZIP bytes. |
| NIST SP 800-218 SSDF | Tests, threat model, claim ledger, and release gates provide the project-level secure-SDLC evidence. |
| NIST SP 800-57 Part 1 | Master-key generation is repo-local; cryptoperiods, custody, escrow, rotation, and KMS/HSM policy remain operator controls. |
| NIST SP 800-161 | Public-release dependency, artifact, and provenance risk management must be implemented by CI/release operations, not inferred from the `.ento` file. |
| NIST SP 800-38D | GCM is the authenticated-encryption primitive; 0.3.x uses the standard 96-bit nonce profile. |
| FIPS 203 / FIPS 204 | PQC KEM/signature standards are relevant to external transport and signing, not the offline container's symmetric envelope. |
| SLSA v1.0 / in-toto / COSE | Current repo does not emit build provenance; release automation should target SLSA Build L3 or better and can use in-toto-style attestations; COSE is an external compact signing/provenance option, not an ENTO container feature [@torresarias2019intoto; @rfc9052]. |
| Sigstore / CycloneDX / SPDX | SBOM export exists as a local artifact; signatures/provenance remain external release controls. |
| MITRE ATT&CK | Threat model maps offline CLI abuse paths to ATT&CK techniques for review coverage, not FedRAMP control inheritance. |

## Planned public-release control split

When the project is promoted toward `https://github.com/docxology/entofile`,
the repository should keep the same division of responsibility:

| Artifact | Repo-local evidence | Public-release addition |
| --- | --- | --- |
| Source tree | Tests, claim ledger, threat model, RedTeam ledger | Branch protection, CODEOWNERS, signed commits or signed release tags |
| Python package artifacts | Not produced by the 0.4 manuscript RC | Reproducible build job, SLSA provenance, package signature, vulnerability scan |
| Manuscript PDF/HTML | Template render and output validator | Signed release attachment and checksum in release notes |
| SBOM | `output/reports/sbom.cyclonedx.json` | Signed SBOM attestation and dependency vulnerability snapshot |
| ENTO containers | Keyed `verify`/`unpack`; default `0.4.0` PADMÉ bucketed length hiding | Operator KMS/HSM policy and external timestamp/signature for origin |

## Detection hooks

The offline reference implementation cannot provide a SOC, but it should make
operator telemetry easy to route:

| Event | Source | Suggested downstream mapping |
| --- | --- | --- |
| Verification failure | CLI stderr JSON / `verify_container` result | MITRE T1565.001 stored data manipulation |
| Duplicate ZIP member | `validate_zip_member_names` / archive validation | Archive smuggling or parser differential attempt |
| ZIP size/member limit exceeded | `validate_zip_archive`, `safe_read_member` | Endpoint denial of service attempt (T1499) |
| Keyless `unverified` result | `verify_container.integrity` | Policy violation when keyed assurance is required |
| Legacy unpadded sealed export for length-sensitive data | release/operator checklist | Data-handling exception requiring default `0.4.0` or external approval |

## 0.4 RC release checklist

```bash
uv run python scripts/run_tests.py
uv run python scripts/ento_analysis.py
uv run python scripts/export_sbom.py
uv run python scripts/z_generate_manuscript_variables.py
cd <template-checkout>
uv run python scripts/03_render_pdf.py --project working/entofile
uv run python scripts/04_validate_output.py --project working/entofile
```

## Out of scope for this repo

- Network daemon controls such as mTLS, device posture, or FIDO2 enrollment.
- FedRAMP/ISO/PCI/HIPAA control implementation for an operator's environment.
- PQC key exchange for transport channels; ENTO containers are local files.
- In-repo HSM/KMS, Sigstore admission policy, release transparency log monitoring,
  and SOC ingestion.
