# Proof export and observability {#sec:proof_observability}

Two mechanisms govern what a recipient sees without re-encrypting track ciphertext: **observability levels** filter exported manifests; **proof export** optionally emits a hash chain over track digests. The default authenticated-context profile binds the selected exported view into each track tag, so changing its observability view requires a fresh pack operation.

## Observability redaction

Internal pack always writes a full auditable manifest. Export applies `src/observability.py::filter_manifest` at the requested level (0 through {{CONFIG_OBSERVABILITY_LEVEL_MAX}}):

| Level | Name | Visible fields |
| --- | --- | --- |
| 0 | sealed | Track ids, byte lengths |
| 1 | typed | + type URIs |
| 2 | resolved | + resolution descriptors |
| 3 | auditable | + SHA-256 digests |

Benchmark manifest sizes for the EEG fixture (bytes, averaged across repetitions):

| Level | Manifest bytes |
| --- | --- |
| 0 | {{RESULT_MANIFEST_BYTES_L0}} |
| 1 | {{RESULT_MANIFEST_BYTES_L1}} |
| 2 | {{RESULT_MANIFEST_BYTES_L2}} |
| 3 | {{RESULT_MANIFEST_BYTES_L3}} |

[@fig:observability_manifest_size] plots the same sweep. CLI `--observability` controls export redaction only; stored ciphertext is unchanged. Level 0 is appropriate when filenames alone would leak too much context; level {{CONFIG_OBSERVABILITY_LEVEL_MAX}} supports reproducibility checks against fixture digests in [@sec:ontology_fixtures].

## Proof chain

`src/proof.py` builds `proof/chain.json` with a deliberately minimal, unsigned
hash-chain construction. It is conceptually adjacent to Merkle hash-linked
authentication and Haber--Stornetta timestamping [@merkle1988digital;
@haber1991timestamp], but it is not a ledger or a signature scheme:

1. `manifest_sha256` over the exact exported manifest JSON bytes
2. Per-track links hashing `(track_id, sha256_plaintext, previous_hash)` with SHA-256 [@nistfips1804]

Hash-over-JSON schemes need a stable byte representation. ENTO uses the exact
bytes emitted by `manifest_to_json` (`sort_keys=True`, fixed indentation,
trailing newline) as the proof binding. The JCS specification is the relevant
canonicalization standard for broader JSON interoperability, but ENTO does not
implement or claim JCS compliance in this release [@rfc8785].

`verify_proof_export(proof, manifest_json)` performs three checks—it recomputes the manifest digest, walks the hash chain, and confirms the links correspond one-to-one (by `track_id` and `sha256_plaintext`, in order) to the manifest's tracks with a matching `format_version`. Tampering with `manifest.json` after export fails the digest binding; a chain whose links describe a different track set than the manifest fails the correspondence check even when the individual link hashes are internally consistent.

The CLI exposes `verify -i container.ento.zip` for keyless checks (schema, ZIP member set, ciphertext digests, proof when present). Supply `-k master.key` to confirm plaintext digests without writing output files. Unpack repeats the same gate before decryption.

At observability level **sealed** (0), proof export is omitted: there is insufficient public metadata to anchor without revealing types or digests.

## PROV alignment

Proof links are compatible with W3C PROV entity-activity patterns and PROV-O
vocabulary alignment [@w3cprov2013; @w3cprovo2013]: each link records a
derivation step over track content digests without mandating a particular ledger
implementation.
