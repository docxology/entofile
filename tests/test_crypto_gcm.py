"""Tests for the AES-256-GCM backend and current crypto facade."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crypto import FORMAT_VERSION, decrypt_payload, encrypt_payload, nonce_size_for
from src.crypto_gcm import decrypt_payload as gcm_decrypt
from src.crypto_gcm import encrypt_payload as gcm_encrypt
from src.errors import IntegrityError

_BINDING = "a" * 64


def _load_vector(name: str) -> dict[str, object]:
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "test_vectors" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_gcm_regression_vector() -> None:
    vector = _load_vector("aes256_gcm_regression.json")
    key = bytes.fromhex(str(vector["key_hex"]))
    nonce = bytes.fromhex(str(vector["nonce_hex"]))
    plaintext = bytes.fromhex(str(vector["plaintext_hex"]))
    expected_ct = bytes.fromhex(str(vector["ciphertext_hex"]))
    expected_tag = bytes.fromhex(str(vector["tag_hex"]))
    nonce_out, tag, ciphertext = gcm_encrypt(key, plaintext, _nonce=nonce, nonce_size=16)
    assert nonce_out == nonce
    assert tag == expected_tag
    assert ciphertext == expected_ct
    assert gcm_decrypt(key, nonce, tag, ciphertext, nonce_size=16) == plaintext


def test_gcm_default_nonce_is_12_bytes() -> None:
    nonce, _, _ = gcm_encrypt(bytes(32), b"payload")
    assert len(nonce) == 12


def test_gcm_tag_mismatch_fails_closed() -> None:
    key = bytes(32)
    nonce, tag, ciphertext = gcm_encrypt(key, b"payload")
    with pytest.raises(IntegrityError, match="authentication tag mismatch"):
        gcm_decrypt(key, nonce, tag[:-1] + bytes([tag[-1] ^ 0xFF]), ciphertext)


def test_facade_uses_gcm_for_current_format() -> None:
    key = bytes.fromhex("603deb1015ca71be2b73aef0857d77811f352c073b6108d71d59185466726408")
    nonce, tag, ciphertext = encrypt_payload(
        key,
        b"test",
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
        == b"test"
    )


def test_deterministic_nonce_reproduces_ciphertext() -> None:
    key = bytes(32)
    plaintext = b"same plaintext bytes"
    nonce = bytes(nonce_size_for(FORMAT_VERSION))
    _, tag_a, ciphertext_a = encrypt_payload(
        key,
        plaintext,
        _nonce=nonce,
        format_version=FORMAT_VERSION,
        track_id="alpha",
        manifest_binding=_BINDING,
    )
    _, tag_b, ciphertext_b = encrypt_payload(
        key,
        plaintext,
        _nonce=nonce,
        format_version=FORMAT_VERSION,
        track_id="alpha",
        manifest_binding=_BINDING,
    )
    assert ciphertext_a == ciphertext_b
    assert tag_a == tag_b
