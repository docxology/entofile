"""ENTO track type ontology registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .models import PlainTrack, ResolutionDescriptor


@dataclass(frozen=True)
class TrackTypeSpec:
    """Registered ENTO track type and required resolution keys."""

    uri: str
    label: str
    required_resolution: frozenset[str]


_REGISTRY: Final[dict[str, TrackTypeSpec]] = {
    "ento:timeseries.eeg": TrackTypeSpec(
        uri="ento:timeseries.eeg",
        label="EEG time series",
        required_resolution=frozenset({"hz"}),
    ),
    "ento:genomics.vcf": TrackTypeSpec(
        uri="ento:genomics.vcf",
        label="VCF genomics slice",
        required_resolution=frozenset({"build", "chr"}),
    ),
    "ento:spectrogram": TrackTypeSpec(
        uri="ento:spectrogram",
        label="Spectrogram matrix",
        required_resolution=frozenset({"hz", "n_fft", "shape"}),
    ),
    "ento:blockchain.proof": TrackTypeSpec(
        uri="ento:blockchain.proof",
        label="Proof chain anchor",
        required_resolution=frozenset(),
    ),
}


def registered_types() -> tuple[str, ...]:
    """Return all registered track type URIs."""
    return tuple(sorted(_REGISTRY))


def get_type_spec(track_type: str) -> TrackTypeSpec:
    """Return spec for a track type or raise KeyError."""
    if track_type not in _REGISTRY:
        raise KeyError(f"unknown track type: {track_type}")
    return _REGISTRY[track_type]


def validate_track_resolution(track: PlainTrack) -> None:
    """Ensure resolution fields satisfy ontology requirements."""
    spec = get_type_spec(track.track_type)
    if not spec.required_resolution:
        return
    if track.resolution is None:
        missing = ", ".join(sorted(spec.required_resolution))
        raise ValueError(f"track {track.track_id} missing resolution keys: {missing}")
    present = set(track.resolution.to_dict())
    missing_keys = spec.required_resolution - present
    if missing_keys:
        raise ValueError(f"track {track.track_id} missing resolution keys: {', '.join(sorted(missing_keys))}")


def default_resolution(track_type: str) -> ResolutionDescriptor | None:
    """Return canonical default resolution for fixture builders."""
    if track_type == "ento:timeseries.eeg":
        return ResolutionDescriptor(hz=256.0)
    if track_type == "ento:genomics.vcf":
        return ResolutionDescriptor(build="GRCh38", chr="chr1")
    if track_type == "ento:spectrogram":
        return ResolutionDescriptor(hz=44100.0, n_fft=512, shape=(8, 8))
    return None
