"""Public encrypt/decrypt API tests for ENTO 0.5.0 AES-256-GCM."""

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
from src.errors import IntegrityError

_BINDING = "a" * 64


def test_crypto_backend_for_format_mapping() -> None:
    assert crypto_backend_for_format(FORMAT_VERSION) == CRYPTO_BACKEND


def test_encrypt_decrypt_round_trip() -> None:
    key = generate_master_key()
    plaintext = b"round trip payload for gcm"
    nonce, tag, ciphertext = encrypt_payload(
        key,
        plaintext,
        format_version=FORMAT_VERSION,
        track_id="alpha",
        manifest_binding=_BINDING,
    )
    assert (
        decrypt_payload(
            key,
            nonce,
            tag,
            ciphertext,
            format_version=FORMAT_VERSION,
            track_id="alpha",
            manifest_binding=_BINDING,
        )
        == plaintext
    )


@pytest.mark.parametrize(
    "format_version", ("0.1.0", "0.2.0", "0.3.0", "0.3.1", "0.4.0", "9.9.9")
)
def test_unsupported_format_version_rejected(format_version: str) -> None:
    key = generate_master_key()
    with pytest.raises(ValueError, match="unsupported format_version"):
        encrypt_payload(
            key,
            b"x",
            format_version=format_version,
            track_id="alpha",
            manifest_binding=_BINDING,
        )
    with pytest.raises(ValueError, match="unsupported format_version"):
        decrypt_payload(
            key,
            bytes(12),
            bytes(16),
            b"ciphertext",
            format_version=format_version,
            track_id="alpha",
            manifest_binding=_BINDING,
        )


def test_decrypt_tag_mismatch_fails() -> None:
    key = generate_master_key()
    nonce, tag, ciphertext = encrypt_payload(
        key,
        b"x",
        format_version=FORMAT_VERSION,
        track_id="alpha",
        manifest_binding=_BINDING,
    )
    bad_tag = tag[:-1] + bytes([tag[-1] ^ 0xFF])
    with pytest.raises(IntegrityError, match="authentication tag mismatch"):
        decrypt_payload(
            key,
            nonce,
            bad_tag,
            ciphertext,
            format_version=FORMAT_VERSION,
            track_id="alpha",
            manifest_binding=_BINDING,
        )
