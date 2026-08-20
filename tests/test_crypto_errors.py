"""Tests for crypto edge cases."""

from __future__ import annotations

import pytest

from src.crypto import derive_track_key, encrypt_payload, generate_master_key


def test_derive_track_key_bad_length() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        derive_track_key(b"short", "id")


def test_encrypt_bad_nonce_length() -> None:
    key = derive_track_key(generate_master_key(), "t")
    with pytest.raises(ValueError, match="nonce"):
        encrypt_payload(key, b"x", _nonce=b"short", format_version="0.4.0", track_id="t")


def test_encrypt_rejects_bad_track_key_length() -> None:
    with pytest.raises(ValueError, match="track key must be 32 bytes"):
        encrypt_payload(b"too-short", b"x", format_version="0.4.0", track_id="t")


def test_decrypt_rejects_bad_track_key_and_tag_length() -> None:
    from src.crypto import decrypt_payload

    key = derive_track_key(generate_master_key(), "t")
    nonce, tag, ct = encrypt_payload(key, b"payload", format_version="0.2.0")
    with pytest.raises(ValueError, match="track key must be 32 bytes"):
        decrypt_payload(b"short", nonce, tag, ct, format_version="0.2.0")
    with pytest.raises(ValueError, match="tag must be 16 bytes"):
        decrypt_payload(key, nonce, tag[:-1], ct, format_version="0.2.0")


def test_crypto_pads_payload_and_manifest_binding_errors() -> None:
    from src import crypto

    with pytest.raises(ValueError, match="unsupported format_version"):
        crypto.pads_payload("9.9.9")
    with pytest.raises(ValueError, match="unsupported format_version"):
        crypto.requires_manifest_binding("9.9.9")
    with pytest.raises(ValueError, match="track_id is required"):
        crypto.track_aad("0.5.0", None, manifest_binding="a" * 64)
    with pytest.raises(ValueError, match="manifest_binding must be lowercase SHA-256 hex"):
        crypto.track_aad("0.5.0", "alpha", manifest_binding="invalid-hex")
