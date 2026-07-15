"""Observability level filtering for exported manifests."""

from __future__ import annotations

from dataclasses import replace

from .models import Manifest, ObservabilityLevel, TrackDescriptor

_SHA256_EMPTY = ""
_OPAQUE = "ento:opaque"


def _redact_track(track: TrackDescriptor, level: ObservabilityLevel) -> TrackDescriptor:
    """Apply observability redaction policy to one track descriptor."""
    if level == ObservabilityLevel.AUDITABLE:
        return replace(track, observability=int(level))
    if level == ObservabilityLevel.RESOLVED:
        return TrackDescriptor(
            id=track.id,
            type=track.type,
            sha256_plaintext=_SHA256_EMPTY,
            sha256_ciphertext=track.sha256_ciphertext,
            byte_length=track.byte_length,
            resolution=track.resolution,
            observability=int(level),
        )
    if level == ObservabilityLevel.TYPED:
        return TrackDescriptor(
            id=track.id,
            type=track.type,
            sha256_plaintext=_SHA256_EMPTY,
            sha256_ciphertext=track.sha256_ciphertext,
            byte_length=track.byte_length,
            resolution=None,
            observability=int(level),
        )
    # SEALED (level 0) drops the manifest-declared plaintext byte_length, which would
    # otherwise be a redundant size side-channel. NOTE: this does NOT fully hide length —
    # AES-GCM is length-preserving and the container is ZIP_STORED, so plaintext length
    # is still recoverable from the on-disk track member size by anyone holding the bytes.
    # SEALED hides type/digests/declared-length, not length itself. Default format
    # 0.4.0 mitigates exact-length leakage with PADMÉ padding, but bucket size remains visible.
    # See docs/entofile-threat-model.md.
    return TrackDescriptor(
        id=track.id,
        type=_OPAQUE,
        sha256_plaintext=_SHA256_EMPTY,
        sha256_ciphertext=_SHA256_EMPTY,
        byte_length=0,
        resolution=None,
        observability=int(level),
    )


def filter_manifest(manifest: Manifest, level: ObservabilityLevel) -> Manifest:
    """Return a redacted manifest view for the given observability level."""
    if level == ObservabilityLevel.AUDITABLE:
        return replace(manifest, observability_level=level)
    tracks = tuple(_redact_track(t, level) for t in manifest.tracks)
    return replace(manifest, observability_level=level, tracks=tracks)


def validate_export_level(
    observability_level: ObservabilityLevel,
    export_level: ObservabilityLevel,
) -> None:
    """Reject exports that would expose more metadata than the source permits."""
    if export_level > observability_level:
        raise ValueError(
            "export_level cannot expose more metadata than observability_level"
        )


def include_proof_chain(level: ObservabilityLevel) -> bool:
    """Whether proof export is permitted at this observability level."""
    return level in (ObservabilityLevel.TYPED, ObservabilityLevel.RESOLVED, ObservabilityLevel.AUDITABLE)
