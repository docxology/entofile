# Contributing

ENTO changes should preserve the current compatibility boundary unless a
proposal explicitly targets a future breaking release:

- Default writes use format `0.4.0`.
- `0.2.0`, `0.3.0`, and `0.3.1` remain compatibility formats.
- Existing CLI stdout/stderr and exit behavior remain compatible.
- Keyed `verify` before `unpack` is the safe operator workflow.

## Local Checks

Run focused tests for the surface you touch, then run the project gate before a
release-candidate render:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
grep -r "unittest.mock\\|MagicMock\\|@patch" tests/ || echo "Clean"
uv run python scripts/ento_analysis.py
uv run python scripts/generate_conformance_fixtures.py
uv run python scripts/verify_conformance_fixtures.py
uv run python scripts/check_figure_layout.py
uv run python scripts/check_public_promotion_metadata.py --check
uv run python scripts/build_release_bundle.py
```

Render from the sibling template checkout:

```bash
cd <template-checkout>
uv run python scripts/03_render_pdf.py --project working/entofile
uv run python scripts/04_validate_output.py --project working/entofile
```

## Security Changes

Security-sensitive changes need tests that cover the positive path and a fired
negative control. Avoid mock-based crypto, ZIP, or parser tests; use real small
fixtures and the deterministic conformance generator when possible.

Do not commit production keys, decrypted payloads, private research data, or
large generated artifacts. Conformance keys and nonces are fixed test vectors
only and are unsafe outside `data/conformance` or `output/conformance`.
