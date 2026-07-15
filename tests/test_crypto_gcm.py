"""Tests for AES-256-GCM backend."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crypto import FORMAT_VERSION, decrypt_payload, encrypt_payload, nonce_size_for
from src.crypto_gcm import decrypt_payload as gcm_decrypt
from src.crypto_gcm import encrypt_payload as gcm_encrypt


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
    nonce_out, tag, ciphertext = gcm_encrypt(key, plaintext, _nonce=nonce)
    assert nonce_out == nonce
    assert tag == expected_tag
    assert ciphertext == expected_ct
    assert gcm_decrypt(key, nonce, tag, ciphertext) == plaintext


def test_gcm_tag_mismatch_fails_closed() -> None:
    key = bytes(32)
    nonce, tag, ciphertext = gcm_encrypt(key, b"payload")
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        gcm_decrypt(key, nonce, tag[:-1] + bytes([tag[-1] ^ 0xFF]), ciphertext)


def test_facade_uses_gcm_for_v02() -> None:
    key = bytes.fromhex("603deb1015ca71be2b73aef0857d77811f352c073b6108d71d59185466726408")
    nonce, tag, ciphertext = encrypt_payload(
        key, b"test", format_version="0.4.0", track_id="alpha"
    )
    assert (
        decrypt_payload(
            key, nonce, tag, ciphertext, format_version="0.4.0", track_id="alpha"
        )
        == b"test"
    )


def test_deterministic_nonce_reproduces_ciphertext() -> None:
    key = bytes(32)
    plaintext = b"same plaintext bytes"
    nonce = bytes(nonce_size_for(FORMAT_VERSION))
    _, tag_a, ct_a = encrypt_payload(
        key, plaintext, _nonce=nonce, format_version="0.4.0", track_id="alpha"
    )
    _, tag_b, ct_b = encrypt_payload(
        key, plaintext, _nonce=nonce, format_version="0.4.0", track_id="alpha"
    )
    assert ct_a == ct_b
    assert tag_a == tag_b
