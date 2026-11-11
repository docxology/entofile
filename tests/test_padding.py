"""Version-independent PADMÉ padding tests."""

from __future__ import annotations

import pytest

from src import padding
from src.errors import IntegrityError


def test_padme_is_non_shrinking_and_low_overhead() -> None:
    for length in (0, 1, 2, 7, 8, 9, 20, 100, 1000, 4096, 65536):
        assert padding.padme(length) >= length
    assert padding.padme(4096) == 4096
    assert padding.padme(4097) == 4352
    assert padding.padme(1000) == 1024


def test_pad_unpad_round_trips_across_sizes() -> None:
    for length in (0, 1, 2, 15, 16, 81, 88, 255, 4096):
        payload = bytes((index * 7) % 256 for index in range(length))
        assert padding.unpad_payload(padding.pad_payload(payload)) == payload


def test_pad_payload_deterministic_vector() -> None:
    """Pin the padded body so the scheme cannot drift."""
    padded = padding.pad_payload(b"abc")
    assert padded == b"\x00\x00\x00\x00\x00\x00\x00\x03abc\x00"
    assert len(padded) == 12


def test_unpad_rejects_corrupt_length_prefix() -> None:
    with pytest.raises(IntegrityError, match="too short"):
        padding.unpad_payload(b"\x00\x00\x00")
    with pytest.raises(IntegrityError, match="exceeds available bytes"):
        padding.unpad_payload(b"\x00\x00\x00\x00\x00\x00\x00\xff" + b"only-a-few")


def test_unpad_rejects_noncanonical_padding() -> None:
    corrupted = bytearray(padding.pad_payload(b"abc"))
    corrupted[-1] = 1
    with pytest.raises(IntegrityError, match="non-zero padding"):
        padding.unpad_payload(bytes(corrupted))
    with pytest.raises(IntegrityError, match="non-canonical length"):
        padding.unpad_payload(padding.pad_payload(b"abc") + b"\0")
