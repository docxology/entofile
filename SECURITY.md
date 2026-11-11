# Security Policy

ENTO is published at `https://github.com/docxology/entofile`; the maintainer's
`projects/working/entofile` working tree remains the development source.

## Supported Scope

The supported release runs on Python 3.15 and accepts ENTO format `0.5.0` only:
AES-256-GCM with 12-byte nonces, mandatory PADME length padding, and an
authenticated exported-manifest context in each track's AAD. Every other wire
version is rejected. Security reports should identify the command and whether
the issue is in container parsing, cryptography, documentation, generated
artifacts, or the release process.

## Reporting

Do not open public issues for active vulnerabilities or exploit details. Use
[GitHub Security Advisories](https://github.com/docxology/entofile/security/advisories/new)
for private coordinated disclosure, or email the corresponding author listed in
`docs/manuscript/config.yaml`. Public issues are appropriate for hardening
requests, documentation clarifications, and non-sensitive bugs.

## Useful Report Material

- Minimal reproducer container or generation steps, when it is safe to share.
- ENTO command, flags, and format version.
- Expected versus observed `verify`, `inspect`, or `unpack` behavior.
- Whether `--json-output` or `--telemetry-jsonl` was enabled.
- Relevant output from `scripts/verify_conformance_fixtures.py`.

Never include production master keys, plaintext research data, or private
participant metadata in a report.
