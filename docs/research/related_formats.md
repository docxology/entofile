# Related formats and security norms

Research notes distilled for ENTO manuscript prose: default format 0.4.0 plus
compatibility formats 0.2.0, 0.3.0, and 0.3.1. Sources verified against public
specifications and DOIs listed in `manuscript/references.bib`.

The opt-in 0.5.0 profile adds authenticated exported-manifest context to each
track's GCM associated data. It is a forward ENTO profile, not an equivalence
claim with any ecosystem below; interoperability remains governed by the
preregistered agenda in [`agenda.md`](agenda.md).

## Research data containers

**OAIS and PREMIS** [@ccsds2024oais; @premis2015] are preservation-system references rather than file envelopes. OAIS frames archive responsibilities and information packages; PREMIS defines preservation metadata around objects, events, rights, and agents. ENTO should therefore be described as a content object those systems can store, transfer, describe, or cite--not as an archival repository, preservation-metadata standard, or repository-certification substitute.

**RO-Crate** [@rocrate2024; @soilandreyes2022rocrate] packages a dataset as a directory tree with a JSON-LD `@graph` describing entities and files. It excels at FAIR [@wilkinson2016fair] metadata and workflow provenance but does not specify per-file authenticated encryption or a fixed ciphertext header.

**BagIt** [@bagit2018] is a checksum-manifest envelope (`bagit.txt`, `manifest-*.txt`, `data/`) used by digital preservation systems. Integrity is manifest-level; payloads remain plaintext unless an outer layer encrypts the bag.

**Frictionless Data Package** [@frictionless2024] couples a `datapackage.json` descriptor with tabular resources. Schema validation is resource-centric; multimodal typed streams and observability redaction are out of scope.

ENTO adopts ZIP [@zipappnote2024] as the transport envelope (like BagIt’s flat files) but adds a Draft-07 JSON Schema manifest [@jsonschema2020], ontology URIs per track, and per-track AES-256-GCM as documented in `data/ento_track_header.ksy`, whose declarative binary layout follows the Kaitai Struct ecosystem [@kaitai2026].

## Array and multimodal stores

**HDF5** [@hdf5_tr] and **Zarr** [@zarr_v2] optimize chunked n-dimensional arrays and partial cloud reads. Encryption appears via filter pipelines or codec extensions rather than a uniform track header. ENTO trades chunk-level random access for whole-track AEAD semantics suitable for modest research bundles.

**Matroska/MKV** [@matroska2024; @mkvresearch2023] models typed bitstreams (`TrackEntry`, codec IDs, timestamps). **EPUB** [@epub31] packages publication assets in OCF ZIP with OPF metadata. Both inform ENTO’s stream typing (`ento:timeseries.eeg`, etc.) but target playback or reading systems rather than graded manifest export for audit.

## Policy-bound and audit formats

**OpenTDF** [@opentdf2024] binds decryption to policy attributes (TDF headers, key wrapping). ENTO stays stdlib-first: observability levels redact manifest fields without a remote policy engine. The juxtaposition is intentional—ENTO documents what is visible at each export level rather than enforcing enterprise DRM workflows.

**CADF** [@cadf2013] standardizes cloud audit event records. ENTO’s optional `proof/chain.json` export [@w3cprov2013; @w3cprovo2013] offers hash-chained track digests for anchoring in the Merkle/Haber-Stornetta lineage [@merkle1988digital; @haber1991timestamp]; it does not emit CADF events.

## Cryptographic norms

Per-track keys derive via HKDF-SHA256 [@krawczyk2010hkdf; @nistfips1804]
with domain-separated `info` strings. Payload encryption uses AES-256-GCM
[@nistfips197; @rfc5116; @dworkin2007gcm; @mcgrew2004gcm] with a 96-bit nonce,
associated data, and a 128-bit authentication tag in the default 0.4.0 format,
consistent with fail-closed guidance in [@ferguson2010cryptography]. The release
notes explicitly keep nonce uniqueness in scope because GCM nonce reuse admits
practical forgery attacks [@joux2006forbidden; @bock2016nonce]. AES-GCM-SIV is
the relevant standards-track nonce-misuse-resistant AEAD to evaluate for a
future ENTO profile if deployments cannot make fresh-nonce assumptions, but it
is not implemented in the 0.4.0 default profile [@rfc8452].

## Reproducibility and supply-chain norms

The manuscript's reproducibility language follows the practical computational
research rule that scripts, inputs, parameters, and outputs should be inspectable
and rerunnable [@sandve2013reproducible; @wilson2017goodenough]. It does not
claim an external artifact badge, but the PDF/HTML, benchmark CSV, figure
registry, and release manifest are organized around availability,
functionality, and reusability distinctions used by ACM artifact review
[@acm2024artifactbadging].

Public releases need a separate supply-chain envelope around ENTO artifacts:
NIST C-SCRM, SLSA/Sigstore, in-toto, and COSE are cited as external provenance
and signing mechanisms, not as properties of an `.ento.zip` archive
[@nist2022sp800161r1; @slsa2024levels; @sigstore2026cosign; @torresarias2019intoto;
@rfc9052].

## Implications for ENTO format 0.4.0 and compatibility formats

| Concern | RO-Crate / BagIt / Frictionless | HDF5 / Zarr | MKV / EPUB | OpenTDF | ENTO |
| --- | --- | --- | --- | --- | --- |
| Preservation-system role | Metadata/transfer layer; not repository operations | Storage substrate | Publication/media package | Policy package | File envelope only; OAIS/PREMIS remain external |
| Typed multimodal tracks | Partial (files + roles) | Array-centric | Media-centric | Document-centric | URI registry + resolution |
| Per-track AEAD | No | Optional filters | No | Policy-bound | Required header; default `0.4.0` binds format + track AAD; opt-in `0.5.0` also binds exported manifest context |
| Graded export | Metadata profiles | N/A | N/A | Policy attributes | Observability levels 0–3 |
| Length hiding | No | Chunk-dependent | No | Policy-dependent | Default `0.4.0` PADMÉ padding; `0.3.1` compatibility |
| Stdlib-oriented reference | N/A | N/A | N/A | No | Offline Python CLI with ZIP transport |

Future interoperability tests may export ENTO plaintext tracks into HDF5 or RO-Crate without changing the 0.4.0 on-disk ciphertext layout.
