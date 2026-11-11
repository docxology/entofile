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
    """PADMÉ-pad and encrypt a track with current manifest-context AAD."""
    track_key = crypto.derive_track_key(master_key, track.track_id)
    plaintext = padding.pad_payload(track.payload)
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
    """Decrypt, authenticate, and unpad a current-format track payload."""
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
    return padding.unpad_payload(plaintext)


def parse_track_bytes(
    track_id: str,
    data: bytes,
    *,
    format_version: str = FORMAT_VERSION,
) -> EncryptedTrack:
    """Parse current nonce + tag(16) + ciphertext from raw track bytes."""
    nonce_size = crypto.nonce_size_for(format_version)
    min_size = nonce_size + crypto.TAG_SIZE
    if len(data) < min_size:
        raise IntegrityError("track payload too short")
    nonce = data[:nonce_size]
    tag = data[nonce_size : nonce_size + crypto.TAG_SIZE]
    ciphertext = data[nonce_size + crypto.TAG_SIZE :]
    return EncryptedTrack(track_id=track_id, nonce=nonce, tag=tag, ciphertext=ciphertext)
