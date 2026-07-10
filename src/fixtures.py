"""Deterministic fixture track loading for CLI, benchmarks, and tests."""

from __future__ import annotations

from pathlib import Path

from .models import PlainTrack
from .ontology import default_resolution

FIXTURE_MAPPING: dict[str, tuple[str, str]] = {
    "eeg.csv": ("eeg", "ento:timeseries.eeg"),
    "sample.vcf": ("vcf", "ento:genomics.vcf"),
    "spectrogram.bin": ("spectrogram", "ento:spectrogram"),
}


def fixtures_dir(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parent.parent
    return root / "data" / "fixtures"


def load_fixture_tracks(
    project_root: Path | None = None,
    *,
    fixtures_path: Path | None = None,
    require_all: bool = True,
) -> tuple[PlainTrack, ...]:
    """Load committed fixture tracks from data/fixtures/."""
    root = fixtures_path or fixtures_dir(project_root)
    tracks: list[PlainTrack] = []
    missing: list[str] = []
    for filename, (track_id, track_type) in FIXTURE_MAPPING.items():
        path = root / filename
        if not path.is_file():
            missing.append(filename)
            continue
        tracks.append(
            PlainTrack(
                track_id=track_id,
                track_type=track_type,
                payload=path.read_bytes(),
                resolution=default_resolution(track_type),
            )
        )
    if require_all and missing:
        raise FileNotFoundError(f"missing fixture files under {root}: {', '.join(missing)}")
    if not tracks:
        raise FileNotFoundError(f"no fixtures under {root}")
    return tuple(tracks)
