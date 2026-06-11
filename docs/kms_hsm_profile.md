# KMS/HSM Deployment Profile

ENTO does not manage production keys. Deployments that need institutional key
custody should define this profile outside the reference implementation.

## Minimum Profile

- Master keys are generated and stored in KMS/HSM custody.
- Operators receive envelope-wrapped data keys or short-lived decrypt grants.
- Key access is logged with subject, purpose, dataset id, and ticket/change id.
- Rotation policy defines key retirement and container re-encryption triggers.
- Recovery policy defines break-glass approval and post-use audit.

## ENTO Boundary

The CLI expects a 32-byte master key file today. A production wrapper can fetch
that key material into a short-lived local file or memory-backed filesystem, run
`verify`/`unpack`, and remove it after use. The ENTO container format does not
currently encode KMS key ids or wrapped keys.
