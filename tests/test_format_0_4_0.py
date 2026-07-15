"""ENTO format 0.4.0 default profile.

0.4.0 is the paper-0.4 release-candidate wire default: 12-byte GCM nonce,
associated-data binding of (format_version, track_id), and PADME payload padding.
Legacy 0.2.0/0.3.0/0.3.1 remain readable/writable compatibility formats.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from src import container, crypto
from src.models import ObservabilityLevel, PlainTrack

_TRACK = PlainTrack(
    track_id="alpha",
    track_type="ento:blockchain.proof",
    payload=b"default-0.4.0-payload",
)


def test_0_4_0_is_default_and_latest() -> None:
    assert crypto.FORMAT_VERSION == "0.4.0"
    assert crypto.FORMAT_VERSION_LATEST == "0.4.0"
    assert crypto.SUPPORTED_FORMAT_VERSIONS == (
        "0.2.0", "0.3.0", "0.3.1", "0.4.0", "0.5.0"
    )
    assert crypto.nonce_size_for("0.4.0") == 12
    assert crypto.pads_payload("0.4.0") is True
    assert crypto.track_aad("0.4.0", "alpha") == b"ento:0.4.0:track:alpha"


def test_0_4_0_aead_deterministic_vector() -> None:
    """Pin the primitive 0.4.0 AEAD output for fixed key, nonce, and AAD."""
    track_key = crypto.derive_track_key(bytes(range(32)), "alpha")
    nonce = bytes.fromhex("0102030405060708090a0b0c")
    n, tag, ciphertext = crypto.encrypt_payload(
        track_key,
        b"ento-0.4.0-vector",
        _nonce=nonce,
        format_version="0.4.0",
        track_id="alpha",
    )
    assert n == nonce
    assert tag.hex() == "0a5e7c97d052d589b601cf4bc1a5f05b"
    assert ciphertext.hex() == "956d6a74edd45f865b2667a6d5bfe57e92"
    assert (
        crypto.decrypt_payload(
            track_key,
            n,
            tag,
            ciphertext,
            format_version="0.4.0",
            track_id="alpha",
        )
        == b"ento-0.4.0-vector"
    )


def test_pack_default_writes_0_4_0_and_round_trips(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    out = tmp_path / "default.ento.zip"
    manifest = container.pack_container(out, key, (_TRACK,))
    assert manifest.format_version == "0.4.0"
    inspected = container.inspect_container(out)
    assert inspected.format_version == "0.4.0"
    _, payloads = container.unpack_container(out, key)
    assert payloads["alpha"] == _TRACK.payload


def test_0_4_0_hides_exact_length_in_sealed_export(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    sizes: dict[int, int] = {}
    for n in (81, 88):
        blob = container.pack_container_bytes(
            key,
            (PlainTrack("alpha", "ento:blockchain.proof", bytes(n)),),
            export_level=ObservabilityLevel.SEALED,
        )
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            sizes[n] = len(zf.read("tracks/alpha.ento"))
    assert sizes[81] == sizes[88]


def test_0_4_0_downgrade_to_0_3_1_fails_authentication() -> None:
    track_key = crypto.derive_track_key(bytes(range(32)), "alpha")
    nonce, tag, ciphertext = crypto.encrypt_payload(
        track_key,
        b"x",
        format_version="0.4.0",
        track_id="alpha",
    )
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        crypto.decrypt_payload(
            track_key,
            nonce,
            tag,
            ciphertext,
            format_version="0.3.1",
            track_id="alpha",
        )


def test_legacy_formats_still_write_and_read(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    for version in ("0.2.0", "0.3.0", "0.3.1"):
        out = tmp_path / f"legacy-{version}.ento.zip"
        manifest = container.pack_container(out, key, (_TRACK,), format_version=version)
        assert manifest.format_version == version
        got_manifest, payloads = container.unpack_container(out, key)
        assert got_manifest.format_version == version
        assert payloads["alpha"] == _TRACK.payload
