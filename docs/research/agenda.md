# ENTO Research Agenda

This agenda is the current research source of truth for the 0.5.0 release
and its authenticated-manifest-context default. It
separates claims that the reference implementation can establish from
deployment, interoperability, and publication claims that require new
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

The machine-readable companion is [`agenda.yaml`](agenda.yaml). `experiment_plan.yaml`
remains the template-compatible design overlay for benchmark conditions and figures;
the YAML agenda owns preregistration metadata, research-question hypotheses, and
stopping rules.

## Workstreams

### RQ-1 — Independent conformance

Question: Can an independent implementation reproduce the ENTO 0.5.0 wire
contract and reject the same hostile inputs?

Owner: DAF. Control: the published 0.5.0 vectors and the current Python
reference verifier. Repetition rationale: one complete matrix plus three
independent implementations or implementation runs. Limits: a passing matrix
does not prove arbitrary payload or schema-extension interoperability.

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

Owner: DAF. Control: the current whole-track ZIP pack/unpack path with
verify-before-release tests. Repetition rationale: at least three sizes across
three repetitions, with one hostile mutation per failure class. Limits: memory
results are host-specific and do not establish distributed-service behavior.

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
Stop rule: stop immediately on a verify-before-release violation.

### RQ-3 — Leakage and observability

Question: What information remains visible at each format and observability level?

Owner: DAF. Control: matched plaintexts in all supported formats and all four
export levels. Repetition rationale: at least 30 matched size/content pairs per
format and level, observed three times. Limits: archive-only measurements do not
model side channels, traffic analysis, or operator metadata.

Competing hypotheses:

- H3-A: 0.5.0 reduces exact-length leakage to PADMÉ bucket leakage while keeping
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
Stop rule: downgrade the claim to the measured leakage boundary.

### RQ-4 — Cryptographic interoperability

Question: Are the cryptographic primitives, nonce rules, AAD, and canonical
padding independently reproducible and safely constrained?

Owner: DAF. Control: pinned RFC/NIST vectors plus the ENTO 0.4.0/0.5.0 vectors,
with legacy verdicts replayed unchanged. Repetition rationale: three independent
implementations or language bindings must reproduce every fixed vector. Limits:
vector parity does not prove nonce custody, random-source quality, or production
key management.

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
Falsification: any vector, nonce, downgrade, or canonical-padding mismatch.
Stop rule: freeze profile claims until the mismatch is resolved.

### RQ-5 — Custody and recovery boundary

Question: What production wrapper is required around the 32-byte local master-key
interface?

Owner: DAF. Control: the current local 32-byte master-key file boundary with no
provider credentials in the repository. Repetition rationale: three rotation and
three recovery drills per custody design, including denied-access and cleanup
failure cases. Limits: a design study cannot certify a vendor, facility, policy,
or compliance boundary.

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
Falsification: any unlogged key access, unrecoverable rotation, or unsafe cleanup
path. Stop rule: keep custody outside the reference implementation until controls
pass.

### RQ-6 — Supply-chain and release provenance

Question: Can release artifacts be reproduced, inventoried, signed, and verified
outside the working checkout?

Owner: DAF. Control: the current local release manifest, SBOM, uv.lock, and
generated manuscript/artifact set. Repetition rationale: two clean builds in
separate environments plus one independent checksum/provenance verification.
Limits: local builds do not establish public registry availability, signature
trust, or CI isolation.

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
Falsification: any unexplained checksum or provenance verification failure.
Stop rule: do not claim reproducible release artifacts until clean-clone parity
passes.

### RQ-7 — Related-format interoperability

Question: Which exports make ENTO useful alongside RO-Crate, BagIt, HDF5, and Zarr
without misrepresenting ENTO as a replacement?

Owner: DAF. Control: an ENTO-only baseline that preserves the original encrypted
container bytes. Repetition rationale: at least three representative multimodal
datasets per target ecosystem and three adapter repetitions. Limits: successful
export/import does not establish semantic equivalence with any target ecosystem.

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
Falsification: any unreported data, digest, or metadata loss in a round trip.
Stop rule: document the loss boundary before adding an extension.

### RQ-8 — 0.5.0 default-migration validation

Question: Does making 0.5.0 the default prevent metadata reinterpretation while
preserving redaction behavior and the earlier wire contracts?

Competing hypotheses:

- H8-A: binding the canonical exported manifest projection into every track's
  GCM AAD rejects creator, timestamp, observability, ordering, descriptor, and
  rebound-manifest mutations under a supplied key.
- H8-B: the binding improves interpretation integrity but introduces
  canonicalization or compatibility failures that are not present in 0.4.0.
- H8-C: even a correct public binding cannot establish origin; an external
  signature over the container or release bundle remains necessary.

Control: 0.4.0 containers with format-plus-track AAD but no manifest-context
binding, plus fixed 0.2.0/0.3.0/0.3.1 vectors.

Experiment: enumerate all four observability levels and each authenticated
manifest field class; mutate each field once with the old binding, then
recompute the public binding while retaining the original ciphertext. Run the
fixed vector in independent implementations and compare canonical bytes,
bindings, tags, decrypt verdicts, and legacy verdicts.

Metrics: keyed mutation rejection rate, rebound-manifest rejection rate,
redaction-level binding parity, independent vector byte parity, legacy verdict
parity, canonicalization divergence count, and median pack overhead bytes.
Generate at least three independent containers per level and field class; use
three implementation repetitions before any interoperability claim.

Falsification: any keyed mutation accepted, any level that cannot round-trip,
any legacy verdict change, or any unexplained canonicalization divergence.
Stopping rule: stop on the first such result and freeze profile claims until
the discrepancy is classified and resolved.

Limits: this cycle can show metadata-context authentication under a supplied
key. It cannot prove origin, signature validity, KMS/HSM custody, streaming
safety, or equivalence with RO-Crate, BagIt, HDF5, Zarr, or another ecosystem.

## Output contract

Each completed workstream produces a versioned protocol, raw inputs, generated
outputs, a machine-readable result, a negative-control result, and a concise
claim update in `docs/claim_ledger.md` or an explicit deferral. Numeric manuscript
claims must enter through generated tokens; exploratory results remain labeled as
such until replicated.
