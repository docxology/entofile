"""Tests for ENTO 0.5.0 track binary encoding."""

from __future__ import annotations

from src.crypto import FORMAT_VERSION, NONCE_SIZE, TAG_SIZE, generate_master_key
from src.models import PlainTrack
from src.ontology import default_resolution
from src.padding import pad_payload
from src.track import decrypt_track, encrypt_track, parse_track_bytes

_BINDING = "a" * 64


def test_header_layout_size() -> None:
    master = generate_master_key()
    plain = PlainTrack(
        track_id="eeg",
        track_type="ento:timeseries.eeg",
        payload=b"0123456789",
        resolution=default_resolution("ento:timeseries.eeg"),
    )
    encrypted = encrypt_track(
        master, plain, format_version=FORMAT_VERSION, manifest_binding=_BINDING
    )
    raw = encrypted.to_bytes()
    expected_payload = pad_payload(plain.payload)
    assert len(raw) == NONCE_SIZE + TAG_SIZE + len(expected_payload)
    parsed = parse_track_bytes("eeg", raw, format_version=FORMAT_VERSION)
    assert parsed.nonce == encrypted.nonce
    assert (
        decrypt_track(
            master,
            parsed,
            format_version=FORMAT_VERSION,
            manifest_binding=_BINDING,
        )
        == plain.payload
    )


def test_nonce_unique_across_encryptions() -> None:
    master = generate_master_key()
    plain = PlainTrack("a", "ento:blockchain.proof", b"x", None)
    nonces = {
        encrypt_track(
            master, plain, format_version=FORMAT_VERSION, manifest_binding=_BINDING
        ).nonce
        for _ in range(8)
    }
    assert len(nonces) == 8
