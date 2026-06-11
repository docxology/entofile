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
        encrypt_payload(key, b"x", _nonce=b"short", track_id="t")


def test_encrypt_rejects_bad_track_key_length() -> None:
    with pytest.raises(ValueError, match="track key must be 32 bytes"):
        encrypt_payload(b"too-short", b"x", track_id="t")


def test_decrypt_rejects_bad_track_key_and_tag_length() -> None:
    from src.crypto import decrypt_payload

    key = derive_track_key(generate_master_key(), "t")
    nonce, tag, ct = encrypt_payload(key, b"payload", format_version="0.2.0")
    with pytest.raises(ValueError, match="track key must be 32 bytes"):
        decrypt_payload(b"short", nonce, tag, ct, format_version="0.2.0")
    with pytest.raises(ValueError, match="tag must be 16 bytes"):
        decrypt_payload(key, nonce, tag[:-1], ct, format_version="0.2.0")
