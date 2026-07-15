# Scope and related work {#sec:scope}

ENTO intentionally scopes out streaming servers, network transport, and ledger-specific proof verification. It specifies the stable default on-disk layout for **{{FORMAT_VERSION}}**, an opt-in authenticated-context profile **{{FORMAT_VERSION_NEXT}}**, schema-valid supported format values ({{FORMAT_VERSIONS_SUPPORTED}}), and a reference Python implementation with offline verify and unpack.

## Related formats

**HDF5 and Zarr** [@hdf5_tr; @zarr_v2] excel at array chunking and cloud partial reads; ENTO adds per-track authenticated encryption and ontology URIs in exchange for whole-file ZIP semantics.

**EPUB and Matroska** [@epub31; @matroska2024] package typed media streams with container-level metadata; ENTO borrows stream typing but targets research payloads and observability redaction rather than playback.

**OAIS and PREMIS** [@ccsds2024oais; @premis2015] operate above ENTO's file-format layer. OAIS describes archive responsibilities and information packages; PREMIS describes preservation metadata for objects, events, rights, and agents. ENTO is not an archival repository, a preservation-metadata data dictionary, or a certification scheme. Its release claim is narrower: a self-contained encrypted track envelope whose manifest and binary member layout are inspectable and testable.

**RO-Crate, BagIt, and Frictionless Data Package** [@rocrate2024; @soilandreyes2022rocrate; @bagit2018; @frictionless2024] provide preservation-, transfer-, and tabular-oriented packaging with metadata and checksum manifests. ENTO complements them: an ENTO file can sit inside a BagIt payload, be described as an RO-Crate entity, or carry exported tabular resources while keeping ciphertext semantics local to `.ento` tracks.

**OpenTDF and document DRM stacks** [@opentdf2024] emphasize policy-bound decryption; ENTO is an offline CLI with audited GCM (`{{CRYPTO_BACKEND_DEFAULT}}`), explicit observability levels, and reproducible open benchmarks. CADF [@cadf2013] addresses cloud audit events; ENTO proof export aligns with PROV-style derivation chains [@w3cprov2013; @w3cprovo2013] instead. External signatures and build provenance can use standard signing and supply-chain layers such as COSE, SLSA/Sigstore, or in-toto rather than changing the `.ento` ZIP internals [@rfc9052; @slsa2024levels; @sigstore2026cosign; @torresarias2019intoto].

Distilled comparisons and security norm references live in `docs/research/related_formats.md`.

## Positioning

The design juxtaposition is functional: ENTO is for externally signable, typed research bundles that remain enumerable in any ZIP tool while supporting graded manifest export. The container authenticates tracks under the master key; release identity and provenance require a signature layer outside the ZIP. ENTO does not replace FAIR repository infrastructure [@wilkinson2016fair], OAIS archive operations [@ccsds2024oais], or PREMIS preservation metadata [@premis2015], but supplies an encrypted track envelope those systems can catalog. Its `data/ento_track_header.ksy` file uses Kaitai Struct so the binary member layout is documented in a language-neutral parser specification [@kaitai2026].

Frictionless Data Package [@frictionless2024] targets tabular resource descriptors; ENTO track URIs serve a similar disambiguation role for heterogeneous binaries inside one archive. When migrating HDF5 [@hdf5_tr] exports, treat ENTO as an integrity wrapper around extracted arrays rather than an in-place array store—chunk addressing remains the responsibility of the source format.

| Layer | Primary obligation | ENTO relationship |
| --- | --- | --- |
| OAIS / PREMIS [@ccsds2024oais; @premis2015] | Archive responsibilities, preservation metadata, repository operations | External institutional and metadata layer; ENTO can be one content object inside it |
| RO-Crate / BagIt [@rocrate2024; @soilandreyes2022rocrate; @bagit2018] | Research-object description, transfer packaging, checksum manifests | Complementary packaging layer; ENTO can be payload or described entity |
| HDF5 / Zarr [@hdf5_tr; @zarr_v2] | Chunked array storage and partial reads | Source or destination for plaintext arrays; ENTO does not replace chunk addressing |
| OpenTDF [@opentdf2024] | Policy-bound decryption | Adjacent policy model; ENTO is offline and key-file based |
| ENTO {{FORMAT_VERSION}} | Per-track AEAD, typed manifest, observability redaction | Implemented file-format layer validated by this release candidate |

See [@sec:limitations] for threat-model boundaries and [@sec:benchmark_interpretation] for measured trade-offs between observability levels and manifest size.
