# FAQ — entofile

## What is ENTO?

**EN**crypted, **T**yped, **O**mnitrack (stable default format **0.4.0**, opt-in **0.5.0**) — a flat ZIP container holding many independently typed tracks, each sealed with per-track AES-256-GCM, plus graded observability levels and optional hash-chained proof export. "Omnitrack" means one archive carries arbitrarily many heterogeneous tracks side by side.

## Which cryptography library is used?

The reference implementation encrypts and decrypts with the audited [`cryptography`](https://cryptography.io) library's AES-256-GCM, and derives per-track keys with its vetted HKDF-SHA256 (byte-identical to the earlier hand-rolled derivation, locked by `data/test_vectors/hkdf_regression.json`). There is no custom cipher code on the data path.

## Where do commits go?

Private repo for the 0.4 RC working tree: `projects/working/entofile` (inside the private projects checkout). The template renderer resolves it with `--project working/entofile`.
The public repository is [github.com/docxology/entofile](https://github.com/docxology/entofile); the maintainer's monorepo working tree remains the development source of truth.

## How are manuscript numbers kept accurate?

`{{TOKEN}}` placeholders resolved from `src/manuscript_variables.py` reading benchmark CSV and fixture hashes.

## What observability level should I use?

- **3 (auditable)** — full digests for reproducibility
- **0 (sealed)** — minimal metadata; proof export omitted

## Missing spectrogram.bin?

Regenerate from committed fixture or restore from git; CLI pack with `require_all=True` fails if missing.

## How do I add a track type?

Extend `src/ontology.py`, schema, fixtures, tests, and manuscript ontology section.
