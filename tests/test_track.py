"""Tests for track binary encoding."""

from __future__ import annotations

from src.crypto import FORMAT_VERSION, NONCE_SIZE, TAG_SIZE, generate_master_key, pads_payload
from src.ontology import default_resolution
from src.track import decrypt_track, encrypt_track, parse_track_bytes
from src.models import PlainTrack
from src.padding import pad_payload


def test_header_layout_size() -> None:
    master = generate_master_key()
    plain = PlainTrack(
        track_id="eeg",
        track_type="ento:timeseries.eeg",
        payload=b"0123456789",
        resolution=default_resolution("ento:timeseries.eeg"),
    )
    enc = encrypt_track(master, plain)
    raw = enc.to_bytes()
    expected_payload = pad_payload(plain.payload) if pads_payload(FORMAT_VERSION) else plain.payload
    assert len(raw) == NONCE_SIZE + TAG_SIZE + len(expected_payload)
    parsed = parse_track_bytes("eeg", raw)
    assert parsed.nonce == enc.nonce
    assert decrypt_track(master, parsed, format_version=FORMAT_VERSION) == plain.payload


def test_nonce_unique_across_encryptions() -> None:
    master = generate_master_key()
    plain = PlainTrack("a", "ento:blockchain.proof", b"x", None)
    nonces = {encrypt_track(master, plain).nonce for _ in range(8)}
    assert len(nonces) == 8
