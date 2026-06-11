# Format Migration Guidance

ENTO paper release `0.4` promotes the default ENTO wire format to `0.4.0`.
Older `0.2.0`, `0.3.0`, and `0.3.1` containers remain readable and writable as
explicit compatibility formats.

## Choosing a Format

| Format | Use when | Tradeoff |
| --- | --- | --- |
| `0.4.0` | You want the current default release-candidate profile | PADME bucket size and ZIP metadata remain visible |
| `0.3.1` | You need the pre-0.4 padded compatibility profile | Same crypto profile as 0.4.0 but older version label/AAD |
| `0.3.0` | You need AAD binding without length padding | Exact plaintext length remains visible |
| `0.2.0` | You need 16-byte nonce/no-AAD compatibility | No AAD binding and exact plaintext length remains visible |

## Operator Rules

- Existing `0.2.0`/`0.3.0`/`0.3.1` containers remain readable.
- New containers write `0.4.0` unless `pack --format` is supplied.
- Use the default `0.4.0` for sealed or low-entropy payloads where exact length
  could reveal sensitive information.
- Treat paper release `0.4` and wire format `0.4.0` as related but distinct fields.

## Compatibility Boundary

`verify` and `unpack` dispatch from `manifest.format_version`. A container
whose bytes are relabeled to a different AAD-bound format fails GCM
authentication because AAD binds the version and track id. Origin authentication
still requires an external signature over the container or release bundle.
