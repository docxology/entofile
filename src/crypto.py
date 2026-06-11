"""ENTO cryptography facade — HKDF key derivation and AES-256-GCM track encryption."""

from __future__ import annotations

import hashlib
import secrets
from typing import Final

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# 0.4.0 is the paper-0.4 release-candidate default: standard 12-byte GCM nonce,
# AAD binding of format_version+track_id, and PADMÉ length padding. Legacy 0.2.0
# (16-byte nonce, no AAD), 0.3.0 (12-byte nonce + AAD), and 0.3.1 (0.3.0 +
# padding) remain explicit compatibility formats.
FORMAT_VERSION: Final[str] = "0.4.0"
FORMAT_VERSION_LATEST: Final[str] = "0.4.0"
SUPPORTED_FORMAT_VERSIONS: Final[tuple[str, ...]] = (
    "0.2.0",
    "0.3.0",
    "0.3.1",
    "0.4.0",
)

# Default 0.4.0 nonce size. Per-format sizes live in _NONCE_SIZE_BY_FORMAT so
# legacy containers parse with their original nonce length.
NONCE_SIZE: Final[int] = 12
_NONCE_SIZE_BY_FORMAT: Final[dict[str, int]] = {
    "0.2.0": 16,
    "0.3.0": 12,
    "0.3.1": 12,
    "0.4.0": 12,
}
# Formats that PADMÉ-pad the plaintext before encryption (length-hiding).
_PADDED_FORMATS: Final[frozenset[str]] = frozenset({"0.3.1", "0.4.0"})
TAG_SIZE: Final[int] = 16
MASTER_KEY_SIZE: Final[int] = 32

CRYPTO_BACKEND: Final[str] = "aes-256-gcm"


def nonce_size_for(format_version: str) -> int:
    """Return the GCM nonce length for a format version."""
    try:
        return _NONCE_SIZE_BY_FORMAT[format_version]
    except KeyError:
        raise ValueError(f"unsupported format_version: {format_version!r}") from None


def pads_payload(format_version: str) -> bool:
    """Whether this format PADMÉ-pads the plaintext before encryption."""
    if format_version not in SUPPORTED_FORMAT_VERSIONS:
        raise ValueError(f"unsupported format_version: {format_version!r}")
    return format_version in _PADDED_FORMATS


def track_aad(format_version: str, track_id: str | None) -> bytes | None:
    """Associated data authenticated by the AEAD (but not encrypted).

    0.2.0 bound no AAD (track context came only from the HKDF key-derivation label).
    0.3.0, 0.3.1, and 0.4.0 bind ``format_version`` and ``track_id`` so neither a
    format downgrade (incl. a padded↔unpadded swap) nor a cross-track relabel can
    pass authentication.
    Returns ``None`` for 0.2.0.
    """
    if format_version == "0.2.0":
        return None
    if format_version in ("0.3.0", "0.3.1", "0.4.0"):
        if not track_id:
            raise ValueError(f"track_id is required to build {format_version} associated data")
        return f"ento:{format_version}:track:{track_id}".encode()
    raise ValueError(f"unsupported format_version: {format_version!r}")


def generate_master_key() -> bytes:
    """Return a fresh 32-byte master key."""
    return secrets.token_bytes(MASTER_KEY_SIZE)


def sha256_hex(data: bytes) -> str:
    """Return lowercase hex SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def hkdf_sha256(ikm: bytes, length: int, *, info: bytes = b"", salt: bytes = b"") -> bytes:
    """HKDF-SHA256 (RFC 5869) via the vetted ``cryptography`` HKDF.

    Delegates to the audited library primitive rather than a hand-rolled
    HMAC loop, shrinking the custom-crypto surface flagged by the threat model
    (TM-005). The empty-salt → 32 zero bytes convention is the ENTO 0.2.0
    default; output is byte-identical to the prior implementation and is
    regression-locked by ``tests/test_crypto_vectors.py``.
    """
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt or b"\x00" * 32,
        info=info,
    ).derive(ikm)


def derive_track_key(master_key: bytes, track_id: str) -> bytes:
    """Derive a 32-byte per-track key from the master key."""
    if len(master_key) != MASTER_KEY_SIZE:
        raise ValueError("master key must be 32 bytes")
    info = f"ento:track:{track_id}".encode()
    return hkdf_sha256(master_key, MASTER_KEY_SIZE, info=info)


def crypto_backend_for_format(format_version: str) -> str:
    """Map manifest format version to encryption suite name."""
    if format_version in SUPPORTED_FORMAT_VERSIONS:
        return CRYPTO_BACKEND
    raise ValueError(f"unsupported format_version: {format_version!r}")


def encrypt_payload(
    track_key: bytes,
    plaintext: bytes,
    *,
    _nonce: bytes | None = None,
    format_version: str = FORMAT_VERSION,
    track_id: str | None = None,
) -> tuple[bytes, bytes, bytes]:
    """Encrypt plaintext for the ENTO GCM format (version-aware nonce + AAD).

    ``_nonce`` is a private test-vector-only knob — see the DANGER note in
    ``crypto_gcm.encrypt_payload``; production callers leave it unset."""
    if format_version not in SUPPORTED_FORMAT_VERSIONS:
        raise ValueError(f"unsupported format_version: {format_version!r}")
    from . import crypto_gcm

    return crypto_gcm.encrypt_payload(
        track_key,
        plaintext,
        _nonce=_nonce,
        nonce_size=nonce_size_for(format_version),
        aad=track_aad(format_version, track_id),
    )


def decrypt_payload(
    track_key: bytes,
    nonce: bytes,
    tag: bytes,
    ciphertext: bytes,
    *,
    format_version: str,
    track_id: str | None = None,
) -> bytes:
    """Decrypt and authenticate a track payload for the ENTO GCM format."""
    if format_version not in SUPPORTED_FORMAT_VERSIONS:
        raise ValueError(f"unsupported format_version: {format_version!r}")
    from . import crypto_gcm

    return crypto_gcm.decrypt_payload(
        track_key,
        nonce,
        tag,
        ciphertext,
        nonce_size=nonce_size_for(format_version),
        aad=track_aad(format_version, track_id),
    )
