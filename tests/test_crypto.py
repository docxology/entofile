"""Tests for ENTO 0.5.0 cryptography."""

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
from src.errors import IntegrityError

_BINDING = "a" * 64


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
    nonce, tag, ciphertext = encrypt_payload(
        track_key,
        plaintext,
        format_version=FORMAT_VERSION,
        track_id="eeg",
        manifest_binding=_BINDING,
    )
    recovered = decrypt_payload(
        track_key,
        nonce,
        tag,
        ciphertext,
        format_version=FORMAT_VERSION,
        track_id="eeg",
        manifest_binding=_BINDING,
    )
    assert recovered == plaintext


def test_wrong_key_rejected() -> None:
    master = generate_master_key()
    track_key = derive_track_key(master, "eeg")
    wrong_key = derive_track_key(generate_master_key(), "eeg")
    nonce, tag, ciphertext = encrypt_payload(
        track_key,
        b"secret",
        format_version=FORMAT_VERSION,
        track_id="eeg",
        manifest_binding=_BINDING,
    )
    with pytest.raises(IntegrityError, match="authentication tag mismatch"):
        decrypt_payload(
            wrong_key,
            nonce,
            tag,
            ciphertext,
            format_version=FORMAT_VERSION,
            track_id="eeg",
            manifest_binding=_BINDING,
        )


def test_tamper_detection() -> None:
    master = generate_master_key()
    track_key = derive_track_key(master, "vcf")
    nonce, tag, ciphertext = encrypt_payload(
        track_key,
        b"payload",
        format_version=FORMAT_VERSION,
        track_id="vcf",
        manifest_binding=_BINDING,
    )
    corrupted = bytearray(ciphertext)
    corrupted[0] ^= 0xFF
    with pytest.raises(IntegrityError, match="authentication tag mismatch"):
        decrypt_payload(
            track_key,
            nonce,
            tag,
            bytes(corrupted),
            format_version=FORMAT_VERSION,
            track_id="vcf",
            manifest_binding=_BINDING,
        )


def test_master_key_length() -> None:
    assert len(generate_master_key()) == MASTER_KEY_SIZE


def test_tag_size() -> None:
    track_key = derive_track_key(generate_master_key(), "x")
    _, tag, _ = encrypt_payload(
        track_key,
        b"x",
        format_version=FORMAT_VERSION,
        track_id="x",
        manifest_binding=_BINDING,
    )
    assert len(tag) == TAG_SIZE
