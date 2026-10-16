# Streaming Pack/Unpack Design Note

Streaming support is deferred. A future design must preserve verify-before-
release semantics while handling large multimodal tracks.

The existing `pack_container_stream` and `unpack_container_stream` APIs are
**buffered iterator adapters**, not constant-memory streaming implementations.
Packing retains plaintext tracks before encryption and rejects accumulation over
the per-member and aggregate archive budgets. Unpacking authenticates and buffers
all plaintext before exposing iterators. `chunk_size` must be positive; it controls
unpack slice sizes, not peak memory. Packing accepts the option for API symmetry
but consumes the caller's chunk sizes. Final packed archives are checked against
the same ingestion limits as readers and published atomically, so rejected input
does not truncate an existing destination.

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
