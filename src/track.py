"""ENTO track binary encoding."""

from __future__ import annotations

from . import crypto, padding
from .crypto import FORMAT_VERSION
from .errors import IntegrityError
from .models import EncryptedTrack, PlainTrack


def encrypt_track(
    master_key: bytes,
    track: PlainTrack,
    *,
    format_version: str = FORMAT_VERSION,
    manifest_binding: str | None = None,
) -> EncryptedTrack:
    """Encrypt a plaintext track with per-track derived key.

    For 0.3.0+ the track_id and format_version are bound as AEAD associated data;
    0.3.1, 0.4.0, and 0.5.0 additionally PADMÉ-pad the plaintext. Format 0.5.0
    also requires the exported manifest binding."""
    track_key = crypto.derive_track_key(master_key, track.track_id)
    plaintext = padding.pad_payload(track.payload) if crypto.pads_payload(format_version) else track.payload
    nonce, tag, ciphertext = crypto.encrypt_payload(
        track_key,
        plaintext,
        format_version=format_version,
        track_id=track.track_id,
        manifest_binding=manifest_binding,
    )
    return EncryptedTrack(
        track_id=track.track_id,
        nonce=nonce,
        tag=tag,
        ciphertext=ciphertext,
    )


def decrypt_track(
    master_key: bytes,
    encrypted: EncryptedTrack,
    *,
    format_version: str,
    manifest_binding: str | None = None,
) -> bytes:
    """Decrypt and authenticate a track payload (un-padding padded formats)."""
    track_key = crypto.derive_track_key(master_key, encrypted.track_id)
    plaintext = crypto.decrypt_payload(
        track_key,
        encrypted.nonce,
        encrypted.tag,
        encrypted.ciphertext,
        format_version=format_version,
        track_id=encrypted.track_id,
        manifest_binding=manifest_binding,
    )
    return padding.unpad_payload(plaintext) if crypto.pads_payload(format_version) else plaintext


def parse_track_bytes(
    track_id: str,
    data: bytes,
    *,
    format_version: str = FORMAT_VERSION,
) -> EncryptedTrack:
    """Parse nonce + tag(16) + ciphertext from raw bytes (nonce length is format-aware)."""
    nonce_size = crypto.nonce_size_for(format_version)
    min_size = nonce_size + crypto.TAG_SIZE
    if len(data) < min_size:
        raise IntegrityError("track payload too short")
    nonce = data[:nonce_size]
    tag = data[nonce_size : nonce_size + crypto.TAG_SIZE]
    ciphertext = data[nonce_size + crypto.TAG_SIZE :]
    return EncryptedTrack(track_id=track_id, nonce=nonce, tag=tag, ciphertext=ciphertext)
