# Security Policy

ENTO is currently prepared in the private `projects/working/entofile` checkout.
The planned public home after release readiness is
`https://github.com/docxology/entofile`.

## Supported Scope

The 0.4 paper release candidate documents ENTO format `0.4.0` as the default
wire format: AES-256-GCM with 12-byte nonces, format/track associated data, and
PADME length padding. Formats `0.2.0`, `0.3.0`, and `0.3.1` remain supported
compatibility formats for explicit read/write testing. Security reports should
identify the affected format version, command, and whether the issue is in
container parsing, cryptography, documentation, generated artifacts, or the
release process.

## Reporting

Do not open public issues for active vulnerabilities or exploit details. Until
the public repository is promoted, send coordinated-disclosure reports to the
corresponding author listed in `manuscript/config.yaml`.

After promotion to `docxology/entofile`, prefer GitHub Security Advisories when
available. Public issues are appropriate for hardening requests, documentation
clarifications, and non-sensitive bugs.

## Useful Report Material

- Minimal reproducer container or generation steps, when it is safe to share.
- ENTO command, flags, and format version.
- Expected versus observed `verify`, `inspect`, or `unpack` behavior.
- Whether `--json-output` or `--telemetry-jsonl` was enabled.
- Relevant output from `scripts/verify_conformance_fixtures.py`.

Never include production master keys, plaintext research data, or private
participant metadata in a report.
