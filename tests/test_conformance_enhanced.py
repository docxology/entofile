"""Enhanced and extended conformance fixture checks."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from src import container, crypto
from src.conformance import (
    CONFORMANCE_KEY,
)
from src.errors import IntegrityError, ManifestError


def test_conformance_fixture_malformed_json_rejected(tmp_path: Path) -> None:
    """A container with syntax-invalid manifest JSON fails closed on verify and unpack."""
    bad_zip = tmp_path / "bad_syntax.ento.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("manifest.json", b"{ invalid json content ...")
        zf.writestr("tracks/alpha.ento", b"some bytes")

    with pytest.raises(ManifestError):
        container.verify_container(bad_zip, require_integrity=True)

    with pytest.raises(ManifestError):
        container.unpack_container(bad_zip, CONFORMANCE_KEY)


def test_conformance_fixture_uncanonical_padding_rejected(tmp_path: Path) -> None:
    """ENTO 0.5.0 strictly rejects invalid and non-canonical PADMÉ padding."""
    track_key = crypto.derive_track_key(CONFORMANCE_KEY, "alpha")

    # 0.5.0 payload with corrupt padding length
    bad_padded_plaintext = b"\x00\x00\x00\x05hello"  # claims 5 bytes but padding structure is corrupt
    manifest_binding = crypto.sha256_hex(b"test-binding")
    nonce, tag, ciphertext = crypto.encrypt_payload(
        track_key,
        bad_padded_plaintext,
        format_version="0.5.0",
        track_id="alpha",
        manifest_binding=manifest_binding,
    )
    # The AEAD decrypts successfully, but unpad_payload must reject non-canonical padding
    with pytest.raises((ValueError, IntegrityError)):
        from src.models import EncryptedTrack
        from src.track import decrypt_track

        enc = EncryptedTrack("alpha", nonce, tag, ciphertext)
        decrypt_track(CONFORMANCE_KEY, enc, format_version="0.5.0", manifest_binding=manifest_binding)
