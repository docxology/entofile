# RedTeam migration ledger — ENTO 0.5.0 default

This ledger records the adversarial review for the 0.5.0 default migration. The
older `redteam_publish_0.4.md` remains a historical record of the prior default
cutover; it is not current release guidance.

## Boundary

The migration changes the default writer and release labels. It does not change
the binary track layout, AES-256-GCM primitive, HKDF track-key derivation, PADMÉ
encoding, or the explicit read/write compatibility contract for 0.2.0-0.4.0.

## Findings and controls

| ID | Adversarial question | Control | Status |
| --- | --- | --- | --- |
| RT-05-001 | Could a default pack silently emit 0.4.0? | `FORMAT_VERSION` assertion, default pack round trip, CLI telemetry, release-manifest wire-version check | fixed and tested |
| RT-05-002 | Could moving the default break an older reader? | Explicit 0.4.0 round trips, pinned 0.4.0 vector, full legacy version matrix | fixed and tested |
| RT-05-003 | Could 0.5.0 metadata binding be bypassed by a rebound manifest? | Mutation, rebound, relabel, missing-binding, canonicalization, and export-level negative controls | fixed and tested |
| RT-05-004 | Could an empty default container be mislabeled as keyed integrity? | Preserve fail-closed empty-container rejection and document the no-AEAD-anchor boundary | fixed and tested |
| RT-05-005 | Could docs, manuscript, package metadata, and generated reports disagree? | Token generation, claim ledger, public-promotion, taskboard, release-bundle, and unresolved-token gates | verified by final pipeline |
| RT-05-006 | Could local publication evidence be mistaken for public promotion? | Separate certifying local gate from live endpoint probe; endpoint failure remains a blocker | verified by final pipeline |
| RT-05-007 | Could 0.5.0 be overclaimed as origin authentication or interoperability? | Active docs state GCM/key boundary, external-signature requirement, and preregistered research limits | fixed and tested |

## Release decision

The migration is releasable only when the current source passes the complete
cache-free static, test, analysis, conformance, figure, manuscript, package,
publication, public-endpoint, documentation, and git-parity sequence recorded in
`ISA.md`. A clean local release is not evidence that a new DOI/public repository
deposit has occurred.
