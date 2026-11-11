# Contributing

ENTO uses Python 3.15 and wire format `0.5.0` only. All reads and writes must
reject every other format version explicitly. Preserve the current CLI
stdout/stderr and exit behavior, and keep keyed `verify` before `unpack` as the
safe operator workflow.

## Local Checks

Run focused tests for the surface you touch, then run the project gate before a
release-candidate render:

```bash
uv sync --locked --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
./run.sh no-mocks
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
uv run --no-sync --locked --python 3.15 python scripts/pipeline/stage_03_render.py --project working/entofile
uv run --no-sync --locked --python 3.15 python scripts/pipeline/stage_04_validate.py --project working/entofile
```

## Security Changes

Security-sensitive changes need tests that cover the positive path and a fired
negative control. Avoid mock-based crypto, ZIP, or parser tests; use real small
fixtures and the deterministic conformance generator when possible.

Do not commit production keys, decrypted payloads, private research data, or
large generated artifacts. Conformance keys and nonces are fixed test vectors
only and are unsafe outside `data/conformance` or `output/conformance`.
