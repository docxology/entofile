"""ENTO format 0.3.1 — 0.3.0 (12-byte nonce + AAD) plus PADMÉ length-padding.

0.3.1 hides exact plaintext length: the on-disk ciphertext size reveals only a PADMÉ
bucket, not the byte count. Closes the length side-channel Forge flagged for SEALED.
0.5.0 is now default; 0.3.1 remains a readable/writable compatibility format.
No mocks: real containers.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from src import container, crypto, padding
from src.models import ObservabilityLevel, PlainTrack

# --- PADMÉ unit -------------------------------------------------------------


def test_padme_is_non_shrinking_and_low_overhead() -> None:
    for n in [0, 1, 2, 7, 8, 9, 20, 100, 1000, 4096, 65536]:
        assert padding.padme(n) >= n
    # documented overhead stays modest at scale (PADMÉ ~ O(log log L))
    assert padding.padme(4096) == 4096  # already aligned
    assert padding.padme(4097) == 4352  # next bucket, ~6% over
    assert padding.padme(1000) == 1024


def test_pad_unpad_round_trips_across_sizes() -> None:
    for n in [0, 1, 2, 15, 16, 81, 88, 255, 4096]:
        payload = bytes((i * 7) % 256 for i in range(n))
        assert padding.unpad_payload(padding.pad_payload(payload)) == payload


def test_pad_payload_deterministic_vector() -> None:
    """Pin the padded body for a fixed payload so the scheme cannot drift."""
    padded = padding.pad_payload(b"abc")  # body = 8 + 3 = 11 -> padme(11)=12
    assert padded == b"\x00\x00\x00\x00\x00\x00\x00\x03abc\x00"
    assert len(padded) == 12


def test_unpad_rejects_corrupt_length_prefix() -> None:
    with pytest.raises(ValueError, match="too short"):
        padding.unpad_payload(b"\x00\x00\x00")
    with pytest.raises(ValueError, match="exceeds available bytes"):
        padding.unpad_payload(b"\x00\x00\x00\x00\x00\x00\x00\xff" + b"only-a-few")


def test_unpad_rejects_noncanonical_padding() -> None:
    corrupted = bytearray(padding.pad_payload(b"abc"))
    corrupted[-1] = 1
    with pytest.raises(ValueError, match="non-zero padding"):
        padding.unpad_payload(bytes(corrupted))
    with pytest.raises(ValueError, match="non-canonical length"):
        padding.unpad_payload(padding.pad_payload(b"abc") + b"\0")


# --- format metadata --------------------------------------------------------


def test_0_3_1_metadata() -> None:
    assert "0.3.1" in crypto.SUPPORTED_FORMAT_VERSIONS
    assert crypto.nonce_size_for("0.3.1") == 12
    assert crypto.pads_payload("0.3.1") is True
    assert crypto.pads_payload("0.3.0") is False
    assert crypto.pads_payload("0.2.0") is False
    assert crypto.track_aad("0.3.1", "eeg") == b"ento:0.3.1:track:eeg"


def test_0_3_1_aead_deterministic_vector() -> None:
    """Pin the 0.3.1 primitive AEAD (nonce=12 + AAD). Padding is a track-layer concern,
    so the crypto primitive vector is unpadded."""
    tk = crypto.derive_track_key(bytes(range(32)), "eeg")
    nonce = bytes.fromhex("0102030405060708090a0b0c")
    n, t, c = crypto.encrypt_payload(tk, b"ento-0.3.1-vec", _nonce=nonce, format_version="0.3.1", track_id="eeg")
    assert len(n) == 12
    assert t.hex() == "b138d5ad525643e878d2c29955f28238"
    assert c.hex() == "3e59c1c8880f9e91059889ce31b7"


# --- container round-trip + length-hiding -----------------------------------


def test_0_3_1_container_round_trips(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    track = PlainTrack(track_id="alpha", track_type="ento:blockchain.proof", payload=b"secret-research")
    out = tmp_path / "v31.ento.zip"
    manifest = container.pack_container(out, key, (track,), format_version="0.3.1")
    assert manifest.format_version == "0.3.1"
    _, payloads = container.unpack_container(out, key)
    assert payloads["alpha"] == track.payload  # un-padded back to exact bytes


def test_0_3_1_hides_plaintext_length(tmp_path: Path) -> None:
    """Two payloads of DIFFERENT length in the same PADMÉ bucket (81 and 88) must
    produce IDENTICAL on-disk ciphertext member sizes — the exact length is hidden."""
    key = crypto.generate_master_key()
    sizes = {}
    for n in (81, 88):
        blob = container.pack_container_bytes(
            key,
            (PlainTrack("alpha", "ento:blockchain.proof", bytes(n)),),
            format_version="0.3.1",
            export_level=ObservabilityLevel.SEALED,
        )
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            sizes[n] = len(zf.read("tracks/alpha.ento"))
    assert sizes[81] == sizes[88]  # same bucket -> indistinguishable on the wire


def test_0_2_0_member_size_still_leaks_length_contrast(tmp_path: Path) -> None:
    """Contrast: legacy 0.2.0 (unpadded) DOES leak length — confirms 0.3.1 is
    what closes it, not some incidental effect."""
    key = crypto.generate_master_key()
    sizes = {}
    for n in (81, 88):
        blob = container.pack_container_bytes(
            key,
            (PlainTrack("alpha", "ento:blockchain.proof", bytes(n)),),
            format_version="0.2.0",
        )
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            sizes[n] = len(zf.read("tracks/alpha.ento"))
    assert sizes[81] != sizes[88]  # 0.2.0 leaks exact length


def test_0_3_1_keyed_verify_authenticated_and_downgrade_fails(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    out = tmp_path / "v31.ento.zip"
    container.pack_container(out, key, (PlainTrack("alpha", "ento:blockchain.proof", b"x"),), format_version="0.3.1")
    assert container.verify_container(out, key, require_integrity=True)["integrity"] == "key-authenticated"
    # AAD binds 0.3.1; decrypting the blob under 0.3.0 (no padding, different AAD) must fail
    tk = crypto.derive_track_key(key, "alpha")
    with zipfile.ZipFile(out) as zf:
        raw = zf.read("tracks/alpha.ento")
    from src import track as track_mod

    enc = track_mod.parse_track_bytes("alpha", raw, format_version="0.3.1")
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        crypto.decrypt_payload(tk, enc.nonce, enc.tag, enc.ciphertext, format_version="0.3.0", track_id="alpha")
