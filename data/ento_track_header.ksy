meta:
  id: ento_track_header
  file-extension: ento
  endian: be
  doc: |
    ENTO default per-track blob: nonce(12) || tag(16) || ciphertext.
    format_version 0.4.0: tag is AES-256-GCM authentication tag (AEAD).
    compatibility format 0.2.0 uses a 16-byte nonce and is parsed by code dispatch.
    crypto_suite: aes-256-gcm.
seq:
  - id: nonce
    size: 12
  - id: tag
    size: 16
    doc: AES-256-GCM authentication tag
  - id: ciphertext
    size-eos: true
