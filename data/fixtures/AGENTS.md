# AGENTS.md — data/fixtures/

Deterministic fixture tracks for ENTO pack, benchmark, and manuscript digest
examples.

## Agent rules

- Keep fixture bytes small, deterministic, and documented in `README.md`.
- If adding a fixture, update the table with file name, track id, and type URI.
- Load fixtures through `src/fixtures.py::load_fixture_tracks` instead of
  duplicating parsing logic in tests or scripts.
- Do not replace these with private or sensitive biological/user data.
