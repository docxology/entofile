"""ENTO format benchmark helpers."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from .container import pack_container_bytes, unpack_container
from .crypto import FORMAT_VERSION, generate_master_key, sha256_hex
from .fixtures import load_fixture_tracks
from .manifest import manifest_to_json
from .models import Manifest, ObservabilityLevel, PlainTrack
from .observability import filter_manifest
from .ontology import default_resolution


@dataclass(frozen=True)
class BenchmarkRow:
    format_version: str
    condition: str
    track_id: str
    track_type: str
    plaintext_bytes: int
    ciphertext_bytes: int
    expansion_ratio: float
    pack_seconds: float
    unpack_seconds: float
    pack_throughput_mib_s: float
    tamper_detected: bool
    observability_level: int
    manifest_bytes: int

    def to_csv_row(self) -> dict[str, str]:
        return {
            "format_version": self.format_version,
            "condition": self.condition,
            "track_id": self.track_id,
            "track_type": self.track_type,
            "plaintext_bytes": str(self.plaintext_bytes),
            "ciphertext_bytes": str(self.ciphertext_bytes),
            "expansion_ratio": f"{self.expansion_ratio:.6f}",
            "pack_seconds": f"{self.pack_seconds:.6f}",
            "unpack_seconds": f"{self.unpack_seconds:.6f}",
            "pack_throughput_mib_s": f"{self.pack_throughput_mib_s:.6f}",
            "tamper_detected": str(self.tamper_detected),
            "observability_level": str(self.observability_level),
            "manifest_bytes": str(self.manifest_bytes),
        }


def _synthetic_track(track_id: str, size: int) -> PlainTrack:
    payload = bytes(i % 256 for i in range(size))
    return PlainTrack(
        track_id=track_id,
        track_type="ento:spectrogram",
        payload=payload,
        resolution=default_resolution("ento:spectrogram"),
    )


def _medium_track(size: int) -> PlainTrack:
    return _synthetic_track("medium", size)


def benchmark_track(
    master_key: bytes,
    track: PlainTrack,
    *,
    condition: str,
    observability_level: ObservabilityLevel,
    tmp_dir: Path,
) -> BenchmarkRow:
    start = time.perf_counter()
    blob = pack_container_bytes(
        master_key,
        (track,),
        observability_level=ObservabilityLevel.AUDITABLE,
        export_level=observability_level,
    )
    pack_seconds = time.perf_counter() - start
    container_path = tmp_dir / f"{track.track_id}_{int(observability_level)}.ento.zip"
    container_path.write_bytes(blob)
    start = time.perf_counter()
    _, payloads = unpack_container(container_path, master_key)
    unpack_seconds = time.perf_counter() - start
    assert payloads[track.track_id] == track.payload
    with ZipFile(BytesIO(blob), "r") as zf:
        enc = zf.read(f"tracks/{track.track_id}.ento")
        manifest_bytes = len(zf.read("manifest.json"))
    corrupted = bytearray(enc)
    corrupted[20] ^= 0xFF
    tamper_detected = False
    bad_path = tmp_dir / "bad.ento.zip"
    try:
        with ZipFile(BytesIO(blob), "r") as zin, ZipFile(bad_path, "w") as zout:
            for name in zin.namelist():
                data = zin.read(name)
                if name.startswith("tracks/"):
                    data = bytes(corrupted)
                zout.writestr(name, data)
        unpack_container(bad_path, master_key)
    except ValueError:
        tamper_detected = True
    finally:
        bad_path.unlink(missing_ok=True)
    plaintext_bytes = len(track.payload)
    ciphertext_bytes = len(enc)
    expansion = ciphertext_bytes / plaintext_bytes if plaintext_bytes else 0.0
    throughput = (plaintext_bytes / (1024 * 1024)) / pack_seconds if pack_seconds else 0.0
    return BenchmarkRow(
        format_version=FORMAT_VERSION,
        condition=condition,
        track_id=track.track_id,
        track_type=track.track_type,
        plaintext_bytes=plaintext_bytes,
        ciphertext_bytes=ciphertext_bytes,
        expansion_ratio=expansion,
        pack_seconds=pack_seconds,
        unpack_seconds=unpack_seconds,
        pack_throughput_mib_s=throughput,
        tamper_detected=tamper_detected,
        observability_level=int(observability_level),
        manifest_bytes=manifest_bytes,
    )


def benchmark_tracks(
    master_key: bytes,
    tracks: tuple[PlainTrack, ...],
    *,
    condition: str,
    observability_level: ObservabilityLevel,
    tmp_dir: Path,
) -> list[BenchmarkRow]:
    """Benchmark one multi-track container and return one row per track."""
    start = time.perf_counter()
    blob = pack_container_bytes(
        master_key,
        tracks,
        observability_level=ObservabilityLevel.AUDITABLE,
        export_level=observability_level,
    )
    pack_seconds = time.perf_counter() - start
    container_path = tmp_dir / f"{condition}_{int(observability_level)}.ento.zip"
    container_path.write_bytes(blob)
    start = time.perf_counter()
    _, payloads = unpack_container(container_path, master_key)
    unpack_seconds = time.perf_counter() - start
    for track in tracks:
        assert payloads[track.track_id] == track.payload

    with ZipFile(BytesIO(blob), "r") as zf:
        manifest_bytes = len(zf.read("manifest.json"))
        encrypted = {
            track.track_id: zf.read(f"tracks/{track.track_id}.ento") for track in tracks
        }

    tamper_detected = False
    bad_path = tmp_dir / "bad_mixed.ento.zip"
    first_track = tracks[0].track_id
    corrupted = bytearray(encrypted[first_track])
    corrupted[20] ^= 0xFF
    try:
        with ZipFile(BytesIO(blob), "r") as zin, ZipFile(bad_path, "w") as zout:
            for name in zin.namelist():
                data = zin.read(name)
                if name == f"tracks/{first_track}.ento":
                    data = bytes(corrupted)
                zout.writestr(name, data)
        unpack_container(bad_path, master_key)
    except ValueError:
        tamper_detected = True
    finally:
        bad_path.unlink(missing_ok=True)

    rows: list[BenchmarkRow] = []
    for track in tracks:
        enc = encrypted[track.track_id]
        plaintext_bytes = len(track.payload)
        expansion = len(enc) / plaintext_bytes if plaintext_bytes else 0.0
        throughput = (
            (plaintext_bytes / (1024 * 1024)) / pack_seconds if pack_seconds else 0.0
        )
        rows.append(
            BenchmarkRow(
                format_version=FORMAT_VERSION,
                condition=condition,
                track_id=track.track_id,
                track_type=track.track_type,
                plaintext_bytes=plaintext_bytes,
                ciphertext_bytes=len(enc),
                expansion_ratio=expansion,
                pack_seconds=pack_seconds,
                unpack_seconds=unpack_seconds,
                pack_throughput_mib_s=throughput,
                tamper_detected=tamper_detected,
                observability_level=int(observability_level),
                manifest_bytes=manifest_bytes,
            )
        )
    return rows


def run_all_benchmarks(
    project_root: Path,
    *,
    repetitions: int,
    observability_levels: tuple[int, ...],
    medium_track_bytes: int,
    large_track_bytes: int = 0,
    include_mixed_container: bool = False,
) -> list[BenchmarkRow]:
    master_key = generate_master_key()
    tmp_dir = project_root / "output" / "data" / "_bench_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    rows: list[BenchmarkRow] = []
    small_tracks = load_fixture_tracks(project_root)
    medium = _medium_track(medium_track_bytes)
    large = _synthetic_track("large", large_track_bytes) if large_track_bytes > 0 else None
    for rep in range(repetitions):
        for track in small_tracks:
            for level in observability_levels:
                rows.append(
                    benchmark_track(
                        master_key,
                        track,
                        condition=f"small_tracks_r{rep}",
                        observability_level=ObservabilityLevel(level),
                        tmp_dir=tmp_dir,
                    )
                )
        for level in observability_levels:
            rows.append(
                benchmark_track(
                    master_key,
                    medium,
                    condition=f"medium_tracks_r{rep}",
                    observability_level=ObservabilityLevel(level),
                    tmp_dir=tmp_dir,
                )
            )
        if large is not None:
            for level in observability_levels:
                rows.append(
                    benchmark_track(
                        master_key,
                        large,
                        condition=f"large_tracks_r{rep}",
                        observability_level=ObservabilityLevel(level),
                        tmp_dir=tmp_dir,
                    )
                )
        if include_mixed_container:
            mixed_tracks = (*small_tracks, medium)
            for level in observability_levels:
                rows.extend(
                    benchmark_tracks(
                        master_key,
                        mixed_tracks,
                        condition=f"mixed_tracks_r{rep}",
                        observability_level=ObservabilityLevel(level),
                        tmp_dir=tmp_dir,
                    )
                )
    return rows


def manifest_size_for_level(manifest: Manifest, level: ObservabilityLevel) -> int:
    filtered = filter_manifest(manifest, level)
    return len(manifest_to_json(filtered).encode("utf-8"))


def write_benchmark_csv(rows: list[BenchmarkRow], path: Path) -> Path:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].to_csv_row().keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())
    return path


def write_validation_report(rows: list[BenchmarkRow], path: Path) -> Path:
    tamper_rate = sum(1 for r in rows if r.tamper_detected) / len(rows) if rows else 0.0
    payload = {
        "status": "pass" if tamper_rate == 1.0 else "fail",
        "rows": len(rows),
        "tamper_detection_rate": tamper_rate,
        "manifest_digest": sha256_hex(json.dumps([r.to_csv_row() for r in rows]).encode()),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
