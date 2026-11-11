"""Tests for crypto edge cases."""

from __future__ import annotations

import pytest

from src import crypto
from src.crypto import (
    FORMAT_VERSION,
    derive_track_key,
    encrypt_payload,
    generate_master_key,
)

_BINDING = "a" * 64


def test_derive_track_key_bad_length() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        derive_track_key(b"short", "id")


def test_encrypt_bad_nonce_length() -> None:
    key = derive_track_key(generate_master_key(), "t")
    with pytest.raises(ValueError, match="nonce"):
        encrypt_payload(
            key,
            b"x",
            _nonce=b"short",
            format_version=FORMAT_VERSION,
            track_id="t",
            manifest_binding=_BINDING,
        )


def test_encrypt_rejects_bad_track_key_length() -> None:
    with pytest.raises(ValueError, match="track key must be 32 bytes"):
        encrypt_payload(
            b"too-short",
            b"x",
            format_version=FORMAT_VERSION,
            track_id="t",
            manifest_binding=_BINDING,
        )


def test_decrypt_rejects_bad_track_key_and_tag_length() -> None:
    from src.crypto import decrypt_payload

    key = derive_track_key(generate_master_key(), "t")
    nonce, tag, ciphertext = encrypt_payload(
        key,
        b"payload",
        format_version=FORMAT_VERSION,
        track_id="t",
        manifest_binding=_BINDING,
    )
    with pytest.raises(ValueError, match="track key must be 32 bytes"):
        decrypt_payload(
            b"short",
            nonce,
            tag,
            ciphertext,
            format_version=FORMAT_VERSION,
            track_id="t",
            manifest_binding=_BINDING,
        )
    with pytest.raises(ValueError, match="tag must be 16 bytes"):
        decrypt_payload(
            key,
            nonce,
            tag[:-1],
            ciphertext,
            format_version=FORMAT_VERSION,
            track_id="t",
            manifest_binding=_BINDING,
        )


@pytest.mark.parametrize("format_version", ("0.2.0", "0.3.0", "0.3.1", "0.4.0"))
def test_legacy_format_rejected_by_crypto_helpers(format_version: str) -> None:
    helpers = (
        crypto.nonce_size_for,
        crypto.pads_payload,
        crypto.requires_manifest_binding,
        crypto.crypto_backend_for_format,
    )
    for helper in helpers:
        with pytest.raises(ValueError, match="unsupported format_version"):
            helper(format_version)
    with pytest.raises(ValueError, match="unsupported format_version"):
        crypto.track_aad(format_version, "alpha", manifest_binding=_BINDING)


def test_crypto_current_format_validation_errors() -> None:
    with pytest.raises(ValueError, match="unsupported format_version"):
        crypto.pads_payload("9.9.9")
    with pytest.raises(ValueError, match="unsupported format_version"):
        crypto.requires_manifest_binding("9.9.9")
    with pytest.raises(ValueError, match="track_id is required"):
        crypto.track_aad(FORMAT_VERSION, None, manifest_binding=_BINDING)
    with pytest.raises(ValueError, match="manifest_binding must be lowercase SHA-256 hex"):
        crypto.track_aad(FORMAT_VERSION, "alpha", manifest_binding="invalid-hex")
