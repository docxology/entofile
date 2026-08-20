"""Comprehensive legacy and multi-format compatibility matrix tests."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from src import container, crypto, track
from src.errors import IntegrityError
from src.fixtures import load_fixture_tracks
from src.models import ObservabilityLevel, PlainTrack
from src.ontology import default_resolution

_TRACK = PlainTrack(
    track_id="alpha",
    track_type="ento:spectrogram",
    payload=b"Legacy format compatibility payload: \x00\x01\x02\xff ABCDEF 123456\n",
    resolution=default_resolution("ento:spectrogram"),
)


def test_full_format_matrix_round_trip(tmp_path: Path) -> None:
    """Verify that every supported format version writes and reads correctly."""
    key = crypto.generate_master_key()
    for version in crypto.SUPPORTED_FORMAT_VERSIONS:
        out = tmp_path / f"test-{version}.ento.zip"
        manifest = container.pack_container(
            out,
            key,
            (_TRACK,),
            format_version=version,
            observability_level=ObservabilityLevel.AUDITABLE,
        )
        assert manifest.format_version == version

        # Verify keyless inspection
        inspected = container.inspect_container(out)
        assert inspected.format_version == version

        # Verify with key
        res = container.verify_container(out, key, require_integrity=True)
        assert res["ok"] is True
        assert res["integrity"] == "key-authenticated"

        # Verify without key
        res_nokey = container.verify_container(out, None, require_integrity=True)
        assert res_nokey["ok"] is True
        assert res_nokey["integrity"] == "digest-only"

        # Unpack and verify byte-identical payload
        got_manifest, payloads = container.unpack_container(out, key)
        assert got_manifest.format_version == version
        assert payloads["alpha"] == _TRACK.payload


def test_cross_format_downgrade_rejection(tmp_path: Path) -> None:
    """Tampering with format_version in manifest or decryption parameters must fail."""
    key = crypto.generate_master_key()
    track_key = crypto.derive_track_key(key, "alpha")

    # Encrypt under 0.5.0
    enc_5 = container.pack_container(
        tmp_path / "v5.ento.zip",
        key,
        (_TRACK,),
        format_version="0.5.0",
    )
    assert enc_5.format_version == "0.5.0"

    # Attempting to decrypt a 0.5.0 track as 0.4.0, 0.3.1, 0.3.0, or 0.2.0 must fail
    with zipfile.ZipFile(tmp_path / "v5.ento.zip", "r") as zf:
        raw_track = zf.read("tracks/alpha.ento")
        parsed = track.parse_track_bytes("alpha", raw_track, format_version="0.5.0")

    for legacy_ver in ("0.2.0", "0.3.0", "0.3.1", "0.4.0"):
        with pytest.raises((IntegrityError, ValueError)):
            crypto.decrypt_payload(
                track_key,
                parsed.nonce[: crypto.nonce_size_for(legacy_ver)],
                parsed.tag,
                parsed.ciphertext,
                format_version=legacy_ver,
                track_id="alpha",
            )


def test_format_conversions_preserve_payload(tmp_path: Path) -> None:
    """Unpacking any older format and repacking as current format preserves payload."""
    key = crypto.generate_master_key()
    fixtures = load_fixture_tracks(require_all=True)

    for old_ver in ("0.2.0", "0.3.0", "0.3.1", "0.4.0"):
        old_zip = tmp_path / f"old-{old_ver}.ento.zip"
        container.pack_container(old_zip, key, fixtures, format_version=old_ver)

        # Unpack
        _, payloads = container.unpack_container(old_zip, key)

        # Re-construct PlainTracks
        reconstructed = tuple(
            PlainTrack(
                track_id=t.track_id,
                track_type=t.track_type,
                payload=payloads[t.track_id],
                resolution=t.resolution,
            )
            for t in fixtures
        )

        # Repack as current default (0.5.0)
        new_zip = tmp_path / f"upgraded-from-{old_ver}.ento.zip"
        container.pack_container(new_zip, key, reconstructed, format_version=crypto.FORMAT_VERSION)

        # Verify new container
        v_res = container.verify_container(new_zip, key, require_integrity=True)
        assert v_res["ok"] is True
        assert v_res["integrity"] == "key-authenticated"
        inspected_new = container.inspect_container(new_zip)
        assert inspected_new.format_version == crypto.FORMAT_VERSION
        _, new_payloads = container.unpack_container(new_zip, key)
        for t in fixtures:
            assert new_payloads[t.track_id] == t.payload
