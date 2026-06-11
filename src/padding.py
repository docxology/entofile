"""PADMÉ length-padding for ENTO formats 0.3.1 and 0.4.0.

Hides exact plaintext length from a container-bytes observer by padding each track's
plaintext up to a coarse bucket before AES-GCM encryption, so the on-disk ciphertext
size reveals only the bucket. Scheme: PADMÉ (Nikitin, Barman, Lueks, Underwood,
Hubaux, Troncoso, "Reducing Metadata Leakage from Encrypted Files and Communication
with PURBs", PoPETs 2019) — overhead is bounded to O(log log L), far tighter than
power-of-two bucketing.

Wire layout of the padded plaintext (before GCM):
    pad_len(8 bytes, big-endian original length) || payload || zero-fill to padme(8 + len)
Decrypt recovers the original length from the prefix and slices it back out. The padding
scheme is selected by ``format_version`` (0.3.1 or 0.4.0), which is bound into the
AEAD associated data, so a downgrade to an unpadded format fails authentication rather
than mis-stripping.
"""

from __future__ import annotations

import struct
from typing import Final

_LENGTH_PREFIX: Final[int] = 8  # big-endian uint64 original payload length


def padme(length: int) -> int:
    """Return the PADMÉ padded length >= ``length`` (identity for length < 2)."""
    if length < 2:
        return length
    exponent = length.bit_length() - 1  # floor(log2(length))
    mantissa_bits = exponent.bit_length()  # floor(log2(exponent)) + 1
    low_bits = exponent - mantissa_bits
    if low_bits <= 0:
        return length
    mask = (1 << low_bits) - 1
    return (length + mask) & ~mask


def pad_payload(payload: bytes) -> bytes:
    """Length-prefix and PADMÉ-pad a plaintext payload."""
    body = struct.pack(">Q", len(payload)) + payload
    target = padme(len(body))
    return body + b"\x00" * (target - len(body))


def unpad_payload(padded: bytes) -> bytes:
    """Recover the original payload from a padded plaintext.

    Raises ValueError if the prefix is missing or claims more bytes than present
    (a corrupt/forged padding block)."""
    if len(padded) < _LENGTH_PREFIX:
        raise ValueError("padded payload too short for length prefix")
    (original_length,) = struct.unpack(">Q", padded[:_LENGTH_PREFIX])
    end = _LENGTH_PREFIX + original_length
    if end > len(padded):
        raise ValueError("padded payload length prefix exceeds available bytes")
    return padded[_LENGTH_PREFIX:end]
