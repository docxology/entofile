# ENTO Glossary

| Term | Meaning |
| --- | --- |
| Artifact manifest | Project-local inventory of stable generated outputs and SHA-256 digests. |
| Data fingerprint | SHA-256 over deterministic benchmark columns only; excludes wall-clock timing. |
| Digest-only integrity | Keyless verification where ciphertext digests match; useful for corruption detection but not adversarial authenticity. |
| Key-authenticated integrity | Verification with the master key, AES-GCM authentication, and plaintext digest checks when available. |
| Observability level | Manifest redaction setting from sealed `0` to auditable `3`. |
| Paper release label | Manuscript/version label such as `0.4`; related to but distinct from semver wire strings such as `0.4.0`. |
| Proof export | Unkeyed hash-chain JSON derived from the manifest; useful for reproducibility, not origin authentication. |
| Telemetry JSONL | Optional local event stream emitted by the CLI when `--telemetry-jsonl` is provided. |
| Wire format | On-disk ENTO container version, currently default `0.4.0` with compatibility support for `0.2.0`, `0.3.0`, and `0.3.1`. |

## Observability Levels

| Level | Name | Exported manifest posture |
| --- | --- | --- |
| `0` | sealed | Minimal ids and byte lengths; proof omitted |
| `1` | typed | Adds type URIs |
| `2` | resolved | Adds resolution descriptors |
| `3` | auditable | Adds SHA-256 digests and proof export |
