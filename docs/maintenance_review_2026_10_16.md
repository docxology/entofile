# Maintenance review — October 16, 2026

This review addresses concrete runtime and data-preservation defects without
changing the ENTO wire formats or claiming publication readiness.

## Changes

- Restore Python 3.10 imports through the declared `tomli` compatibility dependency.
- Include the manifest schema, deterministic fixtures, and `py.typed` in wheels.
  Exercise installed-package encryption/decryption outside the checkout.
- Prevent JSON/JSONL sidecars from aliasing command files or overlapping fixture
  and extraction directories. Reject symlinks and multiply-linked destinations;
  check the opened telemetry descriptor before appending.
- Replace JSON sidecars atomically and report sidecar write failures without an
  uncaught traceback. Primary command completion is not rolled back on telemetry
  failure; the CLI returns a nonzero status.
- Write containers to sibling temporary files, enforce reader ZIP/manifest limits,
  and atomically publish only successfully validated archives. Preserve existing
  destinations on validation failure and reject symlinked destinations.
- Reject nonpositive streaming chunk sizes at API entry, bound stream accumulation,
  and document the iterator APIs honestly as buffered, not constant-memory I/O.
- Add regression tests for destination preservation, reader-limit boundaries,
  filesystem aliases, telemetry failures, and stream budgets.

## Local validation

- Canonical `scripts/run_tests.py`: 495 tests, 492 passed, three failed,
  no errors; 90.75% branch-aware source coverage (90% floor).
- The three failures are existing live-tree promotion checks. The release manifest
  reports missing `output/pdf/entofile_combined.pdf` and `output/web/index.html`;
  promotion also requires the template-generated transmission manifest.
- The prepublication rerun excluding exactly those three promotion checks passed
  all 492 remaining tests at 90.75% coverage. The final sidecar/automation subset
  also passed all 17 tests.
- Python 3.10: 26 targeted compatibility tests, all three package build/install
  tests, and 18 final sidecar/stream-adapter tests passed.
- Python 3.13: targeted filesystem, packaging, and container tests passed.
- Ruff, mypy, lockfile consistency, and `git diff --check` passed.
- Analysis, all eight conformance cases, figure layout, SBOM export, and standalone
  manuscript-variable generation passed. The release bundle was generated with
  missing rendered artifacts explicitly reported, not certified as release-ready.

## Remaining boundaries

True bounded-memory streaming, template-integrated rendering, origin signatures,
and external release certification are not delivered by this maintenance pass.
The initial publication preflight was blocked by an active GitVault bootstrap.
Commit and push operations must use the shared writer and migration guards after
that operation releases the lock; no publication may bypass those guards.
# Historical scope

This review records the standalone state on 2026-10-16. See
[publication validation on 2026-10-18](publication_validation_2026_10_18.md)
for the subsequent real render-dependent checks and external release boundary.
