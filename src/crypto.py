"""ENTO cryptography facade — HKDF key derivation and AES-256-GCM track encryption."""

from __future__ import annotations

import hashlib
import secrets
from typing import Final

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# 0.5.0 is the current default profile. It keeps the 0.4.0 binary track layout
# while adding a canonical exported-manifest binding to each track's AEAD AAD.
# 0.4.0 remains an explicit compatibility profile, alongside the older formats.
FORMAT_VERSION: Final[str] = "0.5.0"
FORMAT_VERSION_LATEST: Final[str] = "0.5.0"
FORMAT_VERSION_PREVIOUS: Final[str] = "0.4.0"
# Kept as a source-compatible alias for clients that consumed the pre-0.5
# forward-profile constant. There is no unimplemented forward profile in 0.5.0.
FORMAT_VERSION_NEXT: Final[str] = FORMAT_VERSION
SUPPORTED_FORMAT_VERSIONS: Final[tuple[str, ...]] = (
    "0.2.0",
    "0.3.0",
    "0.3.1",
    "0.4.0",
    "0.5.0",
)

# Default 0.5.0 nonce size. Per-format sizes live in _NONCE_SIZE_BY_FORMAT so
# legacy containers parse with their original nonce length.
NONCE_SIZE: Final[int] = 12
_NONCE_SIZE_BY_FORMAT: Final[dict[str, int]] = {
    "0.2.0": 16,
    "0.3.0": 12,
    "0.3.1": 12,
    "0.4.0": 12,
    "0.5.0": 12,
}
# Formats that PADMÉ-pad the plaintext before encryption (length-hiding).
_PADDED_FORMATS: Final[frozenset[str]] = frozenset({"0.3.1", "0.4.0", "0.5.0"})
MANIFEST_BINDING_FORMATS: Final[frozenset[str]] = frozenset({"0.5.0"})
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


def requires_manifest_binding(format_version: str) -> bool:
    """Whether a format requires the canonical exported-manifest binding."""
    if format_version not in SUPPORTED_FORMAT_VERSIONS:
        raise ValueError(f"unsupported format_version: {format_version!r}")
    return format_version in MANIFEST_BINDING_FORMATS


def track_aad(
    format_version: str,
    track_id: str | None,
    *,
    manifest_binding: str | None = None,
) -> bytes | None:
    """Associated data authenticated by the AEAD (but not encrypted).

    0.2.0 bound no AAD (track context came only from the HKDF key-derivation label).
    0.3.0, 0.3.1, and 0.4.0 bind ``format_version`` and ``track_id``. 0.5.0
    additionally binds the canonical exported-manifest context digest, so a
    keyed reader authenticates the metadata it uses to interpret the tracks.
    Returns ``None`` for 0.2.0.
    """
    if format_version == "0.2.0":
        return None
    if format_version in ("0.3.0", "0.3.1", "0.4.0"):
        if not track_id:
            raise ValueError(f"track_id is required to build {format_version} associated data")
        return f"ento:{format_version}:track:{track_id}".encode()
    if format_version == "0.5.0":
        if not track_id:
            raise ValueError("track_id is required to build 0.5.0 associated data")
        if not manifest_binding:
            raise ValueError("manifest_binding is required for 0.5.0 associated data")
        if len(manifest_binding) != 64 or any(
            character not in "0123456789abcdef" for character in manifest_binding
        ):
            raise ValueError("manifest_binding must be lowercase SHA-256 hex")
        return f"ento:{format_version}:manifest:{manifest_binding}:track:{track_id}".encode()
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
    manifest_binding: str | None = None,
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
        aad=track_aad(
            format_version, track_id, manifest_binding=manifest_binding
        ),
    )


def decrypt_payload(
    track_key: bytes,
    nonce: bytes,
    tag: bytes,
    ciphertext: bytes,
    *,
    format_version: str,
    track_id: str | None = None,
    manifest_binding: str | None = None,
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
        aad=track_aad(
            format_version, track_id, manifest_binding=manifest_binding
        ),
    )
