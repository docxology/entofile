"""Public encrypt/decrypt API tests for the default ENTO AES-256-GCM format."""

from __future__ import annotations

import pytest

from src.crypto import (
    CRYPTO_BACKEND,
    FORMAT_VERSION,
    crypto_backend_for_format,
    decrypt_payload,
    encrypt_payload,
    generate_master_key,
)


def test_crypto_backend_for_format_mapping() -> None:
    assert crypto_backend_for_format(FORMAT_VERSION) == CRYPTO_BACKEND


def test_encrypt_decrypt_round_trip_v04_compatibility() -> None:
    key = generate_master_key()
    plaintext = b"round trip payload for gcm"
    nonce, tag, ciphertext = encrypt_payload(
        key, plaintext, format_version="0.4.0", track_id="alpha"
    )
    assert (
        decrypt_payload(
            key, nonce, tag, ciphertext, format_version="0.4.0", track_id="alpha"
        )
        == plaintext
    )


def test_unsupported_format_version_encrypt() -> None:
    key = generate_master_key()
    with pytest.raises(ValueError, match="unsupported format_version"):
        encrypt_payload(key, b"x", format_version="0.1.0")


def test_unsupported_format_version_decrypt() -> None:
    key = generate_master_key()
    nonce, tag, ciphertext = encrypt_payload(
        key, b"x", format_version="0.4.0", track_id="alpha"
    )
    with pytest.raises(ValueError, match="unsupported format_version"):
        decrypt_payload(key, nonce, tag, ciphertext, format_version="9.9.9")


def test_decrypt_tag_mismatch_fails() -> None:
    key = generate_master_key()
    nonce, tag, ciphertext = encrypt_payload(
        key, b"x", format_version="0.4.0", track_id="alpha"
    )
    bad_tag = tag[:-1] + bytes([tag[-1] ^ 0xFF])
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        decrypt_payload(
            key,
            nonce,
            bad_tag,
            ciphertext,
            format_version="0.4.0",
            track_id="alpha",
        )
