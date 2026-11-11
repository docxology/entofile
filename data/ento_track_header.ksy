meta:
  id: ento_track_header
  file-extension: ento
  endian: be
  doc: |
    ENTO 0.5.0 per-track blob: nonce(12) || tag(16) || ciphertext.
    The tag is the AES-256-GCM authentication tag (AEAD), with the exported
    manifest binding and track ID in the associated data.
    crypto_suite: aes-256-gcm.
seq:
  - id: nonce
    size: 12
  - id: tag
    size: 16
    doc: AES-256-GCM authentication tag
  - id: ciphertext
    size-eos: true
