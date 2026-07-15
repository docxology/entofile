"""ENTO AES-256-GCM via the ``cryptography`` package.

Version-aware AEAD core. The nonce length and associated-data are supplied by the
caller (``src/crypto.py`` derives them from ``format_version``): 0.2.0 uses a
16-byte nonce and no AAD; 0.3.0+ uses the standard 12-byte GCM nonce and binds
``format_version`` + ``track_id`` as associated data.
"""

from __future__ import annotations

import secrets
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import IntegrityError

NONCE_SIZE: Final[int] = 16
TAG_SIZE: Final[int] = 16


def encrypt_payload(
    track_key: bytes,
    plaintext: bytes,
    *,
    _nonce: bytes | None = None,
    nonce_size: int = NONCE_SIZE,
    aad: bytes | None = None,
) -> tuple[bytes, bytes, bytes]:
    """Encrypt with AES-256-GCM; return (nonce, tag, ciphertext) in ENTO wire layout.

    DANGER: ``_nonce`` is a private, keyword-only knob for deterministic test
    vectors ONLY (the leading underscore marks it internal so production code that
    reaches for it is an obvious red flag). Supplying a fixed nonce that repeats for
    the same ``track_key`` is catastrophic for AES-GCM — it leaks the plaintext XOR
    of the two messages and the GHASH subkey, enabling tag forgery. Production
    callers MUST leave it unset so a fresh CSPRNG nonce is drawn per encryption
    (``encrypt_track`` always does)."""
    if len(track_key) != 32:
        raise ValueError("track key must be 32 bytes")
    nonce = _nonce if _nonce is not None else secrets.token_bytes(nonce_size)
    if len(nonce) != nonce_size:
        raise ValueError(f"nonce must be {nonce_size} bytes")
    combined = AESGCM(track_key).encrypt(nonce, plaintext, aad)
    if len(combined) < TAG_SIZE:
        raise ValueError("GCM output too short")
    tag = combined[-TAG_SIZE:]
    ciphertext = combined[:-TAG_SIZE]
    return nonce, tag, ciphertext


def decrypt_payload(
    track_key: bytes,
    nonce: bytes,
    tag: bytes,
    ciphertext: bytes,
    *,
    nonce_size: int = NONCE_SIZE,
    aad: bytes | None = None,
) -> bytes:
    """Decrypt AES-256-GCM payload. Raises ValueError on auth failure."""
    if len(track_key) != 32:
        raise ValueError("track key must be 32 bytes")
    if len(nonce) != nonce_size:
        raise ValueError(f"nonce must be {nonce_size} bytes")
    if len(tag) != TAG_SIZE:
        raise ValueError("tag must be 16 bytes")
    try:
        return AESGCM(track_key).decrypt(nonce, ciphertext + tag, aad)
    except InvalidTag as exc:
        # Only an AEAD authentication failure is reported as a tag mismatch;
        # other exceptions (e.g. argument-shape bugs) propagate undisguised.
        raise IntegrityError("authentication tag mismatch") from exc
