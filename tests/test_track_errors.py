"""Tests for track parse and format errors."""

from __future__ import annotations

import pytest

from src.crypto import FORMAT_VERSION, generate_master_key
from src.errors import IntegrityError
from src.models import PlainTrack
from src.track import decrypt_track, encrypt_track, parse_track_bytes

_BINDING = "a" * 64


def test_parse_track_bytes_too_short() -> None:
    with pytest.raises(IntegrityError, match="too short"):
        parse_track_bytes("x", b"\x00" * 10)


@pytest.mark.parametrize("format_version", ("0.2.0", "0.3.0", "0.3.1", "0.4.0"))
def test_track_helpers_reject_legacy_formats(format_version: str) -> None:
    master = generate_master_key()
    plain = PlainTrack("alpha", "ento:blockchain.proof", b"payload")
    with pytest.raises(ValueError, match="unsupported format_version"):
        encrypt_track(
            master,
            plain,
            format_version=format_version,
            manifest_binding=_BINDING,
        )

    encrypted = encrypt_track(
        master, plain, format_version=FORMAT_VERSION, manifest_binding=_BINDING
    )
    with pytest.raises(ValueError, match="unsupported format_version"):
        decrypt_track(
            master,
            encrypted,
            format_version=format_version,
            manifest_binding=_BINDING,
        )
    with pytest.raises(ValueError, match="unsupported format_version"):
        parse_track_bytes("alpha", encrypted.to_bytes(), format_version=format_version)
