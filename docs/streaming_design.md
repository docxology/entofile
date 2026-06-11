# Streaming Pack/Unpack Design Note

Streaming support is deferred. A future design must preserve verify-before-
release semantics while handling large multimodal tracks.

## Constraints

- Do not write plaintext outside the selected output directory.
- Do not release unauthenticated plaintext before the relevant AEAD tag has
  verified.
- Keep manifest schema compatibility explicit.
- Preserve duplicate-member, path, and size-limit checks before extraction.

## Candidate Direction

- Pack: stream plaintext into an authenticated encrypted track writer and commit
  the manifest only after all digests and byte counts are known.
- Unpack: decrypt to a temporary file, authenticate, validate digest/length, then
  atomically move into the output directory.
- Verify: support metadata and ciphertext checks without requiring plaintext
  materialization unless a key is supplied.
