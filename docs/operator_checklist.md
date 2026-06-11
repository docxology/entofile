# ENTO Operator Checklist

Use this checklist for local containers and release smoke tests. The safe default
is always: inspect metadata, verify integrity, then unpack.

## Standard Workflow

1. Generate or provision a 32-byte master key:

   ```bash
   uv run python scripts/ento_cli.py genkey -o master.key
   ```

2. Pack fixture tracks with the current default wire format:

   ```bash
   uv run python scripts/ento_cli.py pack -k master.key -o sample.ento.zip
   ```

3. Inspect manifest metadata without treating it as integrity evidence:

   ```bash
   uv run python scripts/ento_cli.py inspect -i sample.ento.zip
   ```

4. Verify before release or unpack. Prefer keyed verification:

   ```bash
   uv run python scripts/ento_cli.py verify -i sample.ento.zip -k master.key
   ```

5. Unpack only after verification succeeds:

   ```bash
   uv run python scripts/ento_cli.py unpack -i sample.ento.zip -k master.key -o unpacked/
   ```

6. Export a proof chain when a separate audit artifact is useful:

   ```bash
   uv run python scripts/ento_cli.py proof -i sample.ento.zip -o proof.chain.json
   ```

## Integrity Levels

| Result | Meaning | Operator use |
| --- | --- | --- |
| `key-authenticated` | Track bytes decrypted under AES-GCM and plaintext digests matched when present | Required before trusting third-party data |
| `digest-only` | Ciphertext digests matched without a key | Accidental corruption check only |
| `unverified` | No key and missing digest material | Treat as structural inspection, not integrity |

`inspect` is keyless metadata viewing. `verify` without `-k` can prove only
digest-only integrity when ciphertext digests are present. `unpack` repeats
verification and decrypts before writing plaintext, but operational procedures
should still run explicit keyed `verify` first so failures are logged and
reviewable before any output directory is populated.

## Format Selection

- default / `--format 0.4.0`: 12-byte nonce, AAD binding, and PADME length padding.
- `--format 0.2.0`: legacy compatibility baseline from the earlier paper line.
- `--format 0.3.0`: compatibility 12-byte nonce plus AAD binding for
  `format_version` and `track_id`.
- `--format 0.3.1`: compatibility `0.3.0` plus PADME length padding.

Use the default `0.4.0` for sealed exports where exact plaintext length is sensitive.

## Automation Sidecars

All subcommands accept:

```bash
--json-output path/to/result.json
--telemetry-jsonl path/to/events.jsonl
```

These sidecars do not change human stdout/stderr. They intentionally exclude key
material and plaintext bytes.
