# ENTO Conformance Fixtures

Binary conformance ZIPs are generated, not committed. Run:

```bash
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
```

The generator writes `output/conformance/conformance_manifest.json` plus small
known-good and known-bad containers. It uses a fixed public test key and fixed
test-vector nonces; these values exist only to make conformance vectors
deterministic and must never be reused for real data.

Generated cases cover exactly one valid `0.5.0` container plus the `bad-tamper`,
`bad-duplicate-member`, and `bad-path-escape` rejection cases. Every generated
manifest is bound, every good track uses a fixed 12-byte test nonce, and payload
padding is unconditional. Legacy wire versions are not generated.

The verifier writes `output/reports/conformance_report.json` and checks that
keyed `verify`, keyless `verify`, and `unpack` behavior match the manifest's
expected outcomes. The report does not repeat the fixed test key.
