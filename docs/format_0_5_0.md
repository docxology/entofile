# ENTO 0.5.0 authenticated-manifest-context profile

ENTO `0.5.0` is an opt-in forward wire profile. The stable writer default
remains `0.4.0`, so existing applications do not silently change their emitted
bytes. Readers and writers support `0.2.0`, `0.3.0`, `0.3.1`, `0.4.0`, and
`0.5.0`; unknown versions fail closed.

The profile addresses a specific limitation in the earlier AAD contract:
`0.4.0` authenticates each track's format label and track id, but not the
manifest context that tells a reader how to interpret that track. `0.5.0`
binds the exported manifest context to every track's AES-256-GCM tag.

## Wire layout

The ZIP layout and per-track binary layout are unchanged:

```text
manifest.json
tracks/{track_id}.ento       # nonce || tag || ciphertext
proof/chain.json             # optional above SEALED observability
```

`0.5.0` uses a 12-byte GCM nonce, a 16-byte tag, and PADMÉ padding. It is not
a chunked or streaming format. The master key remains external to the ZIP and
per-track keys remain `HKDF-SHA256(master, info="ento:track:{track_id}")`.

## Manifest binding

The exported `manifest.json` contains a required `manifest_binding` field:

```json
"manifest_binding": "<64 lowercase hexadecimal SHA-256 characters>"
```

The binding is SHA-256 over a compact, sorted-key, UTF-8 JSON serialization of
the manifest projection below:

1. Include `format_version`, `created`, `creator`, `observability_level`, and
   the track array in its emitted order.
2. Include every track descriptor field except `sha256_ciphertext`.
3. Omit `manifest_binding` itself.
4. Serialize with `sort_keys=true`, separators `(',', ':')`, and
   `ensure_ascii=false`.

The reference canonicalization profile also normalizes strings to Unicode NFC,
rejects non-finite JSON numbers (`NaN`, `Infinity`, and `-Infinity`), and emits
integral floating-point values as integers. It is an ENTO profile, not a claim of
RFC 8785/JCS interoperability: cross-language byte parity is a preregistered
research question (RQ-1/RQ-4), and no independent implementation is certified
by this release.

The ciphertext digest is excluded because it is produced by encryption whose
AAD contains the binding. The ciphertext bytes are still authenticated by
GCM, and the emitted ciphertext digest remains an independent unkeyed
corruption check. Excluding the digest means changing only that redundant public
field does not change `manifest_binding`; keyed verification still rejects a
wrong non-empty digest, while a key-authenticated reader can verify the actual
ciphertext even when a redacted digest is empty. Excluding the digest does not
make a ciphertext substitution valid: keyed decryption authenticates the
original binding and track id.

The binding is computed from the *exported* view, not an unseen full internal
manifest. Therefore a sealed export has a binding over its opaque track
descriptors, while an auditable export has a binding over its full descriptors.
Changing the creator, timestamp, observability level, track type, resolution,
plaintext digest, byte length, track order, or redaction view changes the
binding.

Because the selected exported view is authenticated as GCM context, changing
the 0.5.0 export level is an explicit repack operation. The stable and
compatibility profiles retain their historical metadata-only redaction behavior;
that behavior is not silently generalized to 0.5.0.

## AEAD associated data

For track `i`, the 0.5.0 AAD is:

```text
ento:0.5.0:manifest:{manifest_binding}:track:{track_id}
```

Encryption is performed only after the binding is known. The implementation
uses a provisional manifest with ciphertext digests ignored by the projection,
computes the binding for the requested export level, encrypts every track with
that binding, and then emits the final manifest. This avoids circular state and
keeps `pack_container()` and `pack_container_bytes()` on one code path.

## Verification behavior

- Schema parsing requires `manifest_binding` for `0.5.0` and validates its
  lowercase-hex shape.
- Readers recompute the binding before member verification or plaintext
  release. A changed manifest with the old binding is rejected immediately.
- Keyed `verify`/`unpack` supplies the binding to GCM. An attacker who rewrites
  the manifest and recomputes the unkeyed binding still cannot authenticate the
  original ciphertext without the master key.
- Keyless verification can detect a stale or malformed binding, but the binding
  and ciphertext digests are public and recomputable. It remains
  `digest-only`, not adversarial origin authentication.
- External signatures over the container or release bundle remain necessary for
  origin, release identity, and supply-chain provenance.

## Compatibility and migration

Use `0.5.0` only when all participating readers implement the profile and the
metadata-authentication improvement is useful. Use stable `0.4.0` when a
consumer has not yet adopted the profile. Existing 0.2.0–0.4.0 containers keep
their original nonce, AAD, padding, and manifest semantics; they are not
retrofit or silently re-encrypted. A migration is an explicit unpack/repack
operation with a new key or nonce set, followed by independent verification.

The profile does not provide streaming, random access, KMS/HSM custody, release
signing, SBOM provenance, or equivalence with RO-Crate, BagIt, HDF5, Zarr, or
other ecosystems. Those are separate research questions in
[`research/agenda.md`](research/agenda.md).

## Implementation and vectors

The normative code seams are:

- `src/manifest_binding.py` — canonical projection, digest, and validation;
- `src/crypto.py` — version dispatch and 0.5.0 AAD;
- `src/container.py` — shared pack preparation and exported-view binding;
- `data/ento_manifest_schema.json` — conditional field requirement;
- `tests/test_format_0_5_0.py` — canonical bytes, AEAD vector, redaction matrix,
  manifest mutation, and rebound-manifest negative controls.

The fixed manifest-context vector has binding
`b8272d2c7ebba75fce8f095db20c7e2523b0bbd181663947bfd0379d6b6640b7`. The
corresponding fixed-key, fixed-nonce AEAD vector is pinned in the test suite;
the test vector is not a production nonce recommendation.
