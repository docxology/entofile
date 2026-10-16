"""Tests for high-throughput chunk streaming container pack and unpack."""

from __future__ import annotations

from pathlib import Path

import pytest

from src import container, crypto
from src.errors import ContainerError
from src.models import ObservabilityLevel
from src.ontology import default_resolution


def test_chunk_streaming_round_trip(tmp_path: Path) -> None:
    """Verify that chunk streaming pack and unpack correctly reconstruct large tracks."""
    key = crypto.generate_master_key()
    destination = tmp_path / "streaming.ento.zip"

    # Create chunked stream generators for two tracks
    chunk_1 = b"STREAMING_CHUNK_1_DATA_" * 1024  # 24KB
    chunk_2 = b"STREAMING_CHUNK_2_DATA_" * 1024  # 24KB
    chunk_3 = b"STREAMING_CHUNK_3_FINAL_" * 512   # 12KB

    def iter_track1():
        yield chunk_1
        yield chunk_2
        yield chunk_3

    def iter_track2():
        yield b"SMALL_TRACK_STREAMING_TEST"

    track_streams = {
        "audio": ("ento:spectrogram", iter_track1(), default_resolution("ento:spectrogram")),
        "eeg": ("ento:timeseries.eeg", iter_track2(), default_resolution("ento:timeseries.eeg")),
    }

    manifest = container.pack_container_stream(
        destination,
        key,
        track_streams,
        creator="streaming-test",
        observability_level=ObservabilityLevel.AUDITABLE,
    )
    assert manifest.format_version == crypto.FORMAT_VERSION
    assert len(manifest.tracks) == 2

    # Verify standard verify_container accepts it
    v_res = container.verify_container(destination, key, require_integrity=True)
    assert v_res["ok"] is True
    assert v_res["integrity"] == "key-authenticated"

    # Unpack via streaming API
    got_manifest, output_streams = container.unpack_container_stream(
        destination, key, chunk_size=8192
    )
    assert got_manifest.format_version == crypto.FORMAT_VERSION
    assert set(output_streams.keys()) == {"audio", "eeg"}

    audio_bytes = b"".join(output_streams["audio"])
    eeg_bytes = b"".join(output_streams["eeg"])

    expected_audio = chunk_1 + chunk_2 + chunk_3
    expected_eeg = b"SMALL_TRACK_STREAMING_TEST"

    assert audio_bytes == expected_audio
    assert eeg_bytes == expected_eeg


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_stream_adapters_reject_invalid_chunk_sizes(tmp_path: Path, chunk_size: int) -> None:
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        container.pack_container_stream(tmp_path / "out.zip", bytes(32), {}, chunk_size=chunk_size)
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        container.unpack_container_stream(tmp_path / "missing.zip", bytes(32), chunk_size=chunk_size)


def test_stream_pack_bounds_accumulation(tmp_path: Path) -> None:
    chunk = b"x" * (1024 * 1024)
    destination = tmp_path / "out.zip"
    streams = {"proof": ("ento:blockchain.proof", (chunk for _ in range(65)), None)}
    with pytest.raises(ContainerError, match="uncompressed size limit"):
        container.pack_container_stream(destination, bytes(32), streams)
    assert not destination.exists()
