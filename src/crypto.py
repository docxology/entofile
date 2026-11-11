"""ENTO cryptography facade — HKDF key derivation and AES-256-GCM track encryption."""

from __future__ import annotations

import hashlib
import secrets
from pathlib import Path
from typing import Any, Final

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# ENTO 0.5.0 binds each track's AEAD to the canonical exported-manifest context.
FORMAT_VERSION: Final[str] = "0.5.0"
SUPPORTED_FORMAT_VERSIONS: Final[tuple[str, ...]] = (FORMAT_VERSION,)

NONCE_SIZE: Final[int] = 12
TAG_SIZE: Final[int] = 16
MASTER_KEY_SIZE: Final[int] = 32

CRYPTO_BACKEND: Final[str] = "aes-256-gcm"


def nonce_size_for(format_version: str) -> int:
    """Return the current format's GCM nonce length."""
    if format_version != FORMAT_VERSION:
        raise ValueError(f"unsupported format_version: {format_version!r}")
    return NONCE_SIZE


def pads_payload(format_version: str) -> bool:
    """Return whether the current format PADMÉ-pads plaintext."""
    if format_version != FORMAT_VERSION:
        raise ValueError(f"unsupported format_version: {format_version!r}")
    return True


def requires_manifest_binding(format_version: str) -> bool:
    """Return whether the current format requires exported-manifest binding."""
    if format_version != FORMAT_VERSION:
        raise ValueError(f"unsupported format_version: {format_version!r}")
    return True


def track_aad(
    format_version: str,
    track_id: str | None,
    *,
    manifest_binding: str | None = None,
) -> bytes:
    """Build current manifest-context and track associated data."""
    if format_version != FORMAT_VERSION:
        raise ValueError(f"unsupported format_version: {format_version!r}")
    if not track_id:
        raise ValueError("track_id is required to build 0.5.0 associated data")
    if not manifest_binding:
        raise ValueError("manifest_binding is required for 0.5.0 associated data")
    if len(manifest_binding) != 64 or any(
        character not in "0123456789abcdef" for character in manifest_binding
    ):
        raise ValueError("manifest_binding must be lowercase SHA-256 hex")
    return f"ento:{format_version}:manifest:{manifest_binding}:track:{track_id}".encode()


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
    (TM-005). The empty-salt → 32 zero bytes convention is part of the ENTO key
    derivation contract and is regression-locked by ``tests/test_crypto_vectors.py``.
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


def detect_hardware_acceleration() -> dict[str, Any]:
    """Inspect and report host CPU / cryptographic hardware acceleration features."""
    import platform

    has_aes_ni = False
    details: dict[str, Any] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "backend": CRYPTO_BACKEND,
        "backend_accelerated": True,
    }

    try:
        if Path("/proc/cpuinfo").is_file():
            cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore").lower()
            flags = [line for line in cpuinfo.splitlines() if line.startswith("flags") or line.startswith("features")]
            flag_text = " ".join(flags)
            has_aes_ni = "aes" in flag_text or "pmull" in flag_text or "armv8_ce" in flag_text
    except OSError:
        pass

    details["hardware_aes"] = has_aes_ni
    return details


def encrypt_payload(
    track_key: bytes,
    plaintext: bytes,
    *,
    _nonce: bytes | None = None,
    format_version: str = FORMAT_VERSION,
    track_id: str | None = None,
    manifest_binding: str | None = None,
) -> tuple[bytes, bytes, bytes]:
    """Encrypt plaintext with the current nonce size and manifest-context AAD.

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
