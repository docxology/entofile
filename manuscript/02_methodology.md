# Methodology {#sec:methodology}

The benchmark matrix, figure-filter contract, and visualization pipeline are documented in [`docs/methods.md`](../docs/methods.md).

The method starts from four hard constraints. First, an ENTO file is still ZIP:
member names, sizes, and central-directory metadata are inspectable before any
key is supplied. Second, AES-GCM is an AEAD primitive, so adversarial integrity
comes from successful keyed authentication, not from unkeyed JSON digests
[@rfc5116; @dworkin2007gcm; @mcgrew2004gcm]. Third, wall-clock benchmark columns
depend on host load and must be measured with dispersion rather than turned into
reproducibility anchors. Fourth, the paper release label and wire-format string
are distinct: paper {{PAPER_VERSION}} documents default wire format
{{FORMAT_VERSION}}, while {{FORMAT_VERSIONS_COMPATIBILITY}} remain compatibility
formats.

## Container layout

An ENTO file is an ordinary ZIP archive with a small, fixed set of members, so any ZIP tool can enumerate its contents even without the decryption key:

```
container.ento.zip
├── manifest.json          # typed index: format_version, observability_level, per-track metadata
├── tracks/
│   ├── eeg.ento           # one authenticated-encrypted member per track
│   ├── vcf.ento
│   └── spectrogram.ento
└── proof/
    └── chain.json         # optional hash chain (omitted at the sealed level)
```

`manifest.json` is the typed index a recipient reads first; each `tracks/{track_id}.ento` member is a self-describing authenticated-ciphertext blob; `proof/chain.json` is an optional integrity chain. The directory layout is deliberately flat — there is no central directory format beyond ZIP's own, so partial inspection degrades gracefully to "list the names."

### Per-track binary header

Every `.ento` member is the concatenation `nonce || tag || ciphertext`:

```
byte 0                {{NONCE_BYTES}}                 {{TRACK_HEADER_BYTES}}                         end
  │  AES-GCM nonce     │  AES-GCM auth tag  │   authenticated ciphertext     │
  └────────────────────┴────────────────────┴────────────────────────────────┘
       {{NONCE_BYTES}} bytes           {{TAG_BYTES}} bytes              variable length
```

The first {{NONCE_BYTES}} bytes are the AES-256-GCM nonce and the next {{TAG_BYTES}} bytes are the authentication tag for `format_version` **{{FORMAT_VERSION}}** (a fixed {{TRACK_HEADER_BYTES}}-byte header in total), followed by the ciphertext body. Under the default profile, that body is the PADMÉ-padded plaintext with an original-length prefix; compatibility formats without padding keep a length-preserving body. The canonical machine-readable definition is the Kaitai Struct spec in `data/ento_track_header.ksy`, using the `.ksy` declarative binary-format language [@kaitai2026]. Decryption recomputes and verifies the tag *before* releasing any plaintext — a corrupted or forged byte makes the whole track fail closed ([@sec:security_verification]). This layout fixes the version-aware ciphertext-expansion law {{FORMAT_DEFAULT_EXPANSION_MODEL}} ([@eq:expansion_law] in [@sec:formal_model]).

### Worked example

To build a container, `pack` derives a per-track key, encrypts each track, writes the `tracks/*.ento` members and a full internal `manifest.json`, redacts the manifest to the requested observability level, and (above the sealed level) appends `proof/chain.json`:

```bash
uv run python scripts/ento_cli.py genkey -o master.key
uv run python scripts/ento_cli.py pack -k master.key -o study.ento.zip \
    --observability {{CONFIG_OBSERVABILITY_LEVEL_MAX}}
uv run python scripts/ento_cli.py verify -i study.ento.zip -k master.key   # key-authenticated
uv run python scripts/ento_cli.py unpack -i study.ento.zip -k master.key -o ./out
```

The reference `pack` encrypts the project's typed fixture tracks (resolved through `src/ontology.py`; supply `--fixtures` to point at another set) and emits the ZIP container redacted to `--observability {{CONFIG_OBSERVABILITY_LEVEL_MAX}}` (auditable). The recipient runs `verify` before `unpack`; with the master key present, verification authenticates every track through the GCM tag rather than trusting any unkeyed manifest field ([@sec:security_verification]).

## Cryptography

The reference implementation in `src/crypto.py` derives per-track keys with
HKDF-SHA256 [@krawczyk2010hkdf; @nistfips1804] (`info =
"ento:track:{track_id}"`). HKDF is used here as a key-separation tool: one
master key enters the container workflow, but each track receives a distinct
subkey labelled by its track id. Master keys are {{MASTER_KEY_BYTES}} random
bytes from `genkey`. The default writer emits format {{FORMAT_VERSION}}; the
decrypt path is version-dispatched across {{COUNT_SUPPORTED_FORMATS}} supported
AES-256-GCM formats so default and compatibility containers remain readable. A
fresh nonce is drawn per encryption under each per-track key because GCM treats
the nonce like a one-time label for that key; reusing it can expose plaintext
relationships and enable forgeries [@joux2006forbidden; @bock2016nonce].
Nonce-misuse-resistant AEADs such as AES-GCM-SIV are a relevant future design
alternative for deployments that cannot bound nonce uniqueness operationally, but
they are not implemented in ENTO {{FORMAT_VERSION}} [@rfc8452].

| `format_version` | Encryption | Library |
| --- | --- | --- |
| {{FORMAT_VERSION}} (default) | AES-256-GCM with associated-data binding and PADMÉ padding [@nistfips197; @rfc5116; @dworkin2007gcm; @mcgrew2004gcm; @nikitin2019purb] | `cryptography` (`src/crypto_gcm.py`) |
| {{FORMAT_VERSIONS_COMPATIBILITY}} (compatibility) | Version-dispatched AES-256-GCM profiles, including no-AAD, AAD-bound, and PADMÉ-padded variants | `cryptography` (`src/crypto_gcm.py`) |

AEAD means the ciphertext and selected cleartext context are checked together.
For {{FORMAT_VERSION}}, the associated data is a small label containing the
format version and track id; it is not encrypted, but changing it causes the GCM
tag check to fail [@rfc5116; @dworkin2007gcm]. Decryption authenticates that tag
before releasing plaintext (fail closed) [@ferguson2010cryptography]. Unpack and
`verify` also compare SHA-256 plaintext and ciphertext digests when digest
fields are present [@nistfips1804], but those digests are unkeyed
corruption checks rather than substitutes for AEAD authentication.

## Container verification

The CLI exposes `verify -i container.ento.zip` for keyless integrity checks (schema, ZIP member set, ciphertext digests, proof binding). Supply `-k master.key` to confirm plaintext digests without writing output files. See [@sec:security_verification].

## Verification vectors

Pinned regression vectors in `data/test_vectors/` lock HKDF and GCM backends across refactors (`tests/test_crypto_vectors.py`, `tests/test_crypto_gcm.py`).

## Manifest schema

`manifest.json` validates against Draft-07 JSON Schema in `data/ento_manifest_schema.json`. The schema accepts the supported format set ({{FORMAT_VERSIONS_SUPPORTED}}); the default writer uses **{{FORMAT_VERSION}}** unless a compatibility format is selected explicitly. Required fields include `observability_level` and per-track `type`, `sha256_plaintext`, `sha256_ciphertext`, and `byte_length`. Format {{FORMAT_VERSION_NEXT}} additionally requires `manifest_binding`, computed from the exported view using ENTO's documented strict JSON profile. Proof export hashes the exact JSON bytes emitted by `manifest_to_json`; the JCS specification defines a general JSON canonicalization scheme, but ENTO does not claim JCS interoperability in this release [@rfc8785].

## Manifest footprint across tracks

![{{FIG_CAPTION_MANIFEST_MULTITRACK}}](../output/figures/manifest_multitrack.png){#fig:manifest_multitrack width={{FIGURE_WIDTH}}%}

[@fig:manifest_multitrack] shows how exported manifest size changes with observability level for each committed fixture track (`eeg`, `vcf`, `spectrogram`) under `small_tracks_r0`. For the stable and compatibility profiles, this redaction is metadata-only; the opt-in authenticated-context profile treats the selected view as AEAD context and requires repacking when the view changes.

![{{FIG_CAPTION_OBSERVABILITY_REDACTION_MATRIX}}](../output/figures/observability_redaction_matrix.png){#fig:observability_redaction_matrix width={{FIGURE_WIDTH}}%}

[@fig:observability_redaction_matrix] makes the field-level policy explicit: observability changes exported manifest fields, not the encrypted track members. It is therefore a metadata control layered beside, not instead of, AEAD verification.

## Ciphertext overhead

![{{FIG_CAPTION_CRYPTO_OVERHEAD}}](../output/figures/crypto_overhead.png){#fig:crypto_overhead width={{FIGURE_WIDTH}}%}

[@fig:crypto_overhead] decomposes per-track ciphertext bytes into the fixed {{TRACK_HEADER_BYTES}}-byte AEAD header and the remaining ciphertext body for `small_tracks_r0` at observability level {{CONFIG_OBSERVABILITY_LEVEL_MAX}}, aligning with the track layout in [@sec:methodology].

## Observability levels

| Level | Name | Exported manifest content |
| --- | --- | --- |
| 0 | sealed | Track ids and byte lengths only |
| 1 | typed | Adds track type URIs |
| 2 | resolved | Adds resolution descriptors |
| 3 | auditable | Full hashes and plaintext digests |

Filtering is centralized in `src/observability.py`; pack always writes a full internal manifest before export redaction at the requested level (up to {{CONFIG_OBSERVABILITY_LEVEL_MAX}}).

## Proof export

`src/proof.py` emits a hash-chained JSON structure over track plaintext digests, in the same broad lineage as Merkle hash-linked authentication and Haber--Stornetta timestamping [@merkle1988digital; @haber1991timestamp]. `verify_proof_export` recomputes `manifest_sha256` over exported manifest bytes, walks the chain, and verifies the links correspond to the manifest's tracks (see [@sec:proof_observability]).
