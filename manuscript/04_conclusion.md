# Conclusion {#sec:conclusion}

ENTO demonstrates a narrow but useful point: a flat ZIP container [@zipappnote2024] can carry typed multimodal tracks, authenticated encryption on format {{FORMAT_VERSION}}, graded observability, and proof export without becoming a repository, policy engine, or hosted service. The benchmark pipeline integrates with registry-backed manuscript variables and claim-ledger tests so manuscript prose tracks measured outputs rather than stale summaries.

## Contributions

1. **Typed track ontology** — URI registry (`ento:timeseries.eeg`, `ento:genomics.vcf`, `ento:spectrogram`) with schema-validated resolution descriptors ([@sec:ontology_fixtures]).
2. **Per-track authenticated envelope** — Fixed header (`nonce || tag || ciphertext`) with HKDF-derived keys [@krawczyk2010hkdf]; AES-256-GCM on format {{FORMAT_VERSION}} ([@sec:methodology]).
3. **Observability levels 0–{{CONFIG_OBSERVABILITY_LEVEL_MAX}}** — Export-time manifest redaction without re-encryption ([@sec:proof_observability]).
4. **Proof export binding** — `manifest_sha256` chained to track digests for anchoring ([@sec:proof_observability]).
5. **Reproducible benchmarks** — {{RESULT_BENCHMARK_ROWS}} CSV rows with {{RESULT_TAMPER_DETECTED_COUNT}} tamper detections at rate {{RESULT_TAMPER_DETECTION_RATE}}, wired to registry-backed manuscript variables and claim ledger tests.
6. **Security verification gate** — `container_verification.json`, structured CLI verify logging, and nation-state deployment checklist ([@sec:security_verification]).
7. **Honest verification and a hardened format ladder** — an `integrity` contract that reports key-authenticated versus keyless corruption-detection and fails closed by default, a default {{FORMAT_VERSION}} profile with associated-data binding and PADMÉ length-padding [@nikitin2019purb], and compatibility formats {{FORMAT_VERSIONS_COMPATIBILITY}} that remain readable beside it ([@sec:limitations]).

The remaining work is deliberately outside the container core: streaming partial decrypt, public-release artifact signing/provenance, KMS/HSM adapters, nonce-misuse-resistant future formats, and formal interoperability tests against HDF5 [@hdf5_tr] and RO-Crate [@rocrate2024]. Those additions can be layered around the {{FORMAT_VERSION}} ciphertext contract documented in `data/ento_track_header.ksy`, with supply-chain and key-custody controls following external guidance rather than being implied by the ZIP envelope itself [@nistsp80057pt1r5; @nist2022sp800161r1; @torresarias2019intoto; @rfc8452]. The planned public destination is `https://github.com/docxology/entofile`; the release candidate remains reproducible from the current `projects/working/entofile` tree until promotion.
