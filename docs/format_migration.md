# Format Migration Guidance

ENTO release `0.5.0` makes authenticated exported-manifest context the default
without changing the ZIP or track binary layout. Existing `0.4.0` containers
remain readable and writable as an explicit compatibility profile, as do
`0.2.0`, `0.3.0`, and `0.3.1`.

## Choosing a Format

| Format | Use when | Tradeoff |
| --- | --- | --- |
| `0.5.0` | New containers and readers that support authenticated exported-manifest context | Binding is public and external signatures are still required |
| `0.4.0` | A consumer has not yet adopted manifest-context binding | Previous AAD contract; PADME bucket size and ZIP metadata remain visible |
| `0.3.1` | You need the pre-0.4 padded compatibility profile | Same crypto profile as 0.4.0 but older version label/AAD |
| `0.3.0` | You need AAD binding without length padding | Exact plaintext length remains visible |
| `0.2.0` | You need 16-byte nonce/no-AAD compatibility | No AAD binding and exact plaintext length remains visible |

## Operator Rules

- Existing `0.2.0`/`0.3.0`/`0.3.1` containers remain readable.
- New containers write `0.5.0` unless `pack --format` selects compatibility.
- `pack --format 0.4.0` opts into the previous versioned AAD contract.
- Use `0.5.0` for sealed or low-entropy payloads where exact length could reveal
  sensitive information; PADMÉ still exposes a bucket and non-sealed manifests
  expose `byte_length`.
- Treat the paper release label and wire format string as separate fields.

## Compatibility Boundary

`verify` and `unpack` dispatch from `manifest.format_version`. A `0.5.0`
container must carry a valid `manifest_binding`; keyed readers bind that digest
into every track's GCM AAD. A container
whose bytes are relabeled to a different AAD-bound format fails GCM
authentication because AAD binds the version and track id. Origin authentication
still requires an external signature over the container or release bundle.
