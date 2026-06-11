"""Tests for ENTO cryptography."""

from __future__ import annotations

import pytest

from src.crypto import (
    FORMAT_VERSION,
    MASTER_KEY_SIZE,
    TAG_SIZE,
    decrypt_payload,
    derive_track_key,
    encrypt_payload,
    generate_master_key,
    hkdf_sha256,
)


def test_hkdf_is_deterministic() -> None:
    key = b"k" * 32
    a = hkdf_sha256(key, 32, info=b"ento:track:eeg")
    b = hkdf_sha256(key, 32, info=b"ento:track:eeg")
    assert a == b
    assert len(a) == 32


def test_encrypt_decrypt_round_trip() -> None:
    master = generate_master_key()
    track_key = derive_track_key(master, "eeg")
    plaintext = b"hello ento container"
    nonce, tag, ciphertext = encrypt_payload(track_key, plaintext, track_id="eeg")
    recovered = decrypt_payload(
        track_key, nonce, tag, ciphertext, format_version=FORMAT_VERSION, track_id="eeg"
    )
    assert recovered == plaintext


def test_wrong_key_rejected() -> None:
    master = generate_master_key()
    track_key = derive_track_key(master, "eeg")
    wrong_key = derive_track_key(generate_master_key(), "eeg")
    nonce, tag, ciphertext = encrypt_payload(track_key, b"secret", track_id="eeg")
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        decrypt_payload(
            wrong_key, nonce, tag, ciphertext, format_version=FORMAT_VERSION, track_id="eeg"
        )


def test_tamper_detection() -> None:
    master = generate_master_key()
    track_key = derive_track_key(master, "vcf")
    nonce, tag, ciphertext = encrypt_payload(track_key, b"payload", track_id="vcf")
    corrupted = bytearray(ciphertext)
    corrupted[0] ^= 0xFF
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        decrypt_payload(
            track_key,
            nonce,
            tag,
            bytes(corrupted),
            format_version=FORMAT_VERSION,
            track_id="vcf",
        )


def test_master_key_length() -> None:
    assert len(generate_master_key()) == MASTER_KEY_SIZE


def test_tag_size() -> None:
    track_key = derive_track_key(generate_master_key(), "x")
    _, tag, _ = encrypt_payload(track_key, b"x", track_id="x")
    assert len(tag) == TAG_SIZE
