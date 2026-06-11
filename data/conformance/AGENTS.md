# AGENTS.md — data/conformance/

Generated ENTO conformance vectors live here only as a documented output target.

## Agent rules

- Do not hand-edit generated ZIP fixtures or manifests.
- Regenerate through `scripts/generate_conformance_fixtures.py` and verify with
  `scripts/verify_conformance_fixtures.py`.
- Fixed keys and nonces in this directory are public test vectors only; never
  reuse them for real data.
- Keep generated binary artifacts out of source control unless a task explicitly
  asks to refresh tracked fixtures.
