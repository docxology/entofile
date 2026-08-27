# src/ — ENTO reference implementation

Pure core modules (`crypto`, `track`, `manifest`, `container`, `ontology`, `observability`, `proof`) use only the standard library plus the declared crypto/schema dependencies (`cryptography`, `jsonschema`). Workflow modules (`analysis`, `figures`, `benchmarks`, `dashboard`, `manuscript_variables`) may import infrastructure helpers.

See [AGENTS.md](AGENTS.md) and [README.md](README.md).
