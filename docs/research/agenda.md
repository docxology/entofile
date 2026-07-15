# ENTO Research Agenda

This agenda is the current research source of truth after the 0.4.0 release
candidate. It separates claims that the reference implementation can establish
from deployment, interoperability, and publication claims that require new
experiments or external controls.

## Protocol contract

- Owner: DAF.
- Lock the hypothesis set, controls, metrics, repetition budget, and stopping
  rules before collecting data.
- Every cycle contains at least three competing hypotheses; a single preferred
  explanation is confirmation bias, not an experiment.
- Use deterministic fixtures and the benchmark data fingerprint for structural
  claims. Treat wall-clock timings as measured, volatile observations.
- Record protocol deviations, failed hypotheses, and negative controls in the
  experiment record.
- Do not claim production custody, public provenance, independent
  interoperability, or statistical superiority from the Python reference
  implementation alone.

## Workstreams

### RQ-1 — Independent conformance

Question: Can an independent implementation reproduce the ENTO 0.4.0 wire
contract and reject the same hostile inputs?

Competing hypotheses:

- H1-A: the language-neutral schema, vectors, and fixtures are sufficient for a
  second implementation to reproduce all positive and negative outcomes.
- H1-B: hidden Python behavior or undocumented ordering details prevent clean
  reproduction.
- H1-C: the current fixture matrix is too small to expose cross-language
  ambiguities.

Experiment: publish canonical JSON vectors, fixture hashes, expected outcomes,
and a second implementation; compare pack/decrypt/verify behavior across all
formats, malformed JSON, duplicate members, path escapes, and schema versions.

Metrics: case-level outcome parity, byte-level vector parity, rejected-hostile-
input parity, and unexplained divergence count.

Falsification: any unexplained byte or verdict divergence after protocol review.
Stop rule: stop the compatibility claim until every divergence is classified.

### RQ-2 — Streaming safety

Question: Can large multimodal tracks be processed without releasing
unauthenticated plaintext or exceeding bounded memory?

Competing hypotheses:

- H2-A: temporary authenticated files plus atomic promotion preserve the current
  verify-before-release contract with bounded memory.
- H2-B: true streaming requires a new authenticated chunk format.
- H2-C: the current ZIP/member policy is the limiting factor, not encryption.

Experiment: prototype pack, verify, and unpack paths at increasing track sizes;
inject truncation, tag, digest, path, and decompression failures.

Metrics: peak resident memory, time to first plaintext byte, bytes released before
authentication, throughput, temporary-disk usage, and failure cleanup success.

Falsification: any unauthenticated plaintext release or cleanup failure after a
hostile-input run.

### RQ-3 — Leakage and observability

Question: What information remains visible at each format and observability level?

Competing hypotheses:

- H3-A: 0.4.0 reduces exact-length leakage to PADMÉ bucket leakage while keeping
  the documented manifest redactions.
- H3-B: ZIP names, member sizes, or ordering reveal materially more than the
  current documentation states.
- H3-C: observability level is an insufficient abstraction for deployment policy.

Experiment: generate matched plaintexts with controlled content, sizes, track
  counts, and metadata; compare archive bytes, ZIP metadata, manifests, and
  proof exports across all formats and levels.

Metrics: observable field inventory, distinguishable-size classes, bucket width,
  manifest byte deltas, and attacker classification accuracy.

Falsification: any documented privacy claim contradicted by a deterministic
  observer using only permitted archive bytes.

### RQ-4 — Cryptographic interoperability

Question: Are the cryptographic primitives, nonce rules, AAD, and canonical
  padding independently reproducible and safely constrained?

Competing hypotheses:

- H4-A: standard HKDF/AES-GCM vectors plus ENTO-specific vectors fully specify the
  current profiles.
- H4-B: the wire description omits an edge needed by an independent implementer.
- H4-C: nonce-management assumptions are the dominant deployment risk and require
  an alternate profile rather than more prose.

Experiment: add RFC/NIST known-answer vectors, cross-language vectors, nonce
  uniqueness checks, downgrade tests, canonical-padding negatives, and profile
  review for nonce-misuse-resistant alternatives.

Metrics: vector parity, duplicate nonce count, downgrade rejection rate, and
  unresolved specification questions.

### RQ-5 — Custody and recovery boundary

Question: What production wrapper is required around the 32-byte local master-key
  interface?

Competing hypotheses:

- H5-A: a short-lived KMS/HSM adapter can preserve the current container API while
  adding audited key access and rotation.
- H5-B: wrapped data keys and key identifiers must become a new wire-format field.
- H5-C: recovery and break-glass policy dominate the technical adapter design.

Experiment: threat-model and prototype a wrapper with access logs, rotation,
  re-encryption triggers, recovery approval, and failure cleanup; do not place
  provider credentials in the reference repository.

Metrics: key exposure duration, audit completeness, rotation blast radius,
  recovery time, and operator-error paths.

### RQ-6 — Supply-chain and release provenance

Question: Can release artifacts be reproduced, inventoried, signed, and verified
outside the working checkout?

Competing hypotheses:

- H6-A: the existing release manifest and SBOM are sufficient inputs for external
  signing and provenance generation.
- H6-B: reproducible package/PDF generation requires environment pinning beyond
  `uv.lock` and current scripts.
- H6-C: the critical missing control is independent verification, not signing.

Experiment: build from a clean clone in two environments, compare checksums,
  generate SBOM/provenance, sign externally, and verify in a clean environment.

Metrics: checksum parity, artifact completeness, provenance verification result,
  dependency drift, and reproducibility failure classification.

### RQ-7 — Related-format interoperability

Question: Which exports make ENTO useful alongside RO-Crate, BagIt, HDF5, and Zarr
without misrepresenting ENTO as a replacement?

Competing hypotheses:

- H7-A: plaintext export/import adapters cover the most useful interoperability
  boundary while keeping ENTO ciphertext unchanged.
- H7-B: metadata mapping is lossy enough that a profile-specific extension is
  required.
- H7-C: interoperability is better served by documented external adapters than
  by adding format features.

Experiment: define representative multimodal datasets, map metadata and digests,
  round-trip through each target ecosystem, and document loss/identity behavior.

Metrics: field preservation, digest preservation, round-trip data equality,
  metadata loss, and adapter complexity.

## Output contract

Each completed workstream produces a versioned protocol, raw inputs, generated
outputs, a machine-readable result, a negative-control result, and a concise
claim update in `docs/claim_ledger.md` or an explicit deferral. Numeric manuscript
claims must enter through generated tokens; exploratory results remain labeled as
such until replicated.
