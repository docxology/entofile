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

Generated cases cover valid `0.2.0`, `0.3.0`, `0.3.1`, and `0.4.0` containers plus
ciphertext tamper, duplicate ZIP member, and path-escape rejection cases.

The verifier writes `output/reports/conformance_report.json` and checks that
keyed `verify`, keyless `verify`, and `unpack` behavior match the manifest's
expected outcomes. The report does not repeat the fixed test key.
