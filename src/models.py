"""ENTO typed domain models for supported manifest format versions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class ObservabilityLevel(IntEnum):
    """Four-level observability contract for exported manifests."""

    SEALED = 0
    TYPED = 1
    RESOLVED = 2
    AUDITABLE = 3


@dataclass(frozen=True)
class ResolutionDescriptor:
    """Multi-domain resolution metadata for a track."""

    hz: float | None = None
    n_fft: int | None = None
    build: str | None = None
    chr: str | None = None
    loci: tuple[str, ...] | None = None
    shape: tuple[int, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.hz is not None:
            out["hz"] = self.hz
        if self.n_fft is not None:
            out["n_fft"] = self.n_fft
        if self.build is not None:
            out["build"] = self.build
        if self.chr is not None:
            out["chr"] = self.chr
        if self.loci is not None:
            out["loci"] = list(self.loci)
        if self.shape is not None:
            out["shape"] = list(self.shape)
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ResolutionDescriptor | None:
        if not data:
            return None
        loci = data.get("loci")
        shape = data.get("shape")
        return cls(
            hz=data.get("hz"),
            n_fft=data.get("n_fft"),
            build=data.get("build"),
            chr=data.get("chr"),
            loci=tuple(loci) if loci is not None else None,
            shape=tuple(shape) if shape is not None else None,
        )


@dataclass(frozen=True)
class TrackDescriptor:
    """Manifest entry for one encrypted track."""

    id: str
    type: str
    sha256_plaintext: str
    sha256_ciphertext: str
    byte_length: int
    resolution: ResolutionDescriptor | None = None
    observability: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "sha256_plaintext": self.sha256_plaintext,
            "sha256_ciphertext": self.sha256_ciphertext,
            "byte_length": self.byte_length,
        }
        if self.resolution is not None:
            out["resolution"] = self.resolution.to_dict()
        if self.observability is not None:
            out["observability"] = self.observability
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrackDescriptor:
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            sha256_plaintext=str(data["sha256_plaintext"]),
            sha256_ciphertext=str(data["sha256_ciphertext"]),
            byte_length=int(data["byte_length"]),
            resolution=ResolutionDescriptor.from_dict(data.get("resolution")),
            observability=data.get("observability"),
        )


@dataclass(frozen=True)
class Manifest:
    """Top-level ENTO manifest stored as manifest.json."""

    format_version: str
    created: str
    creator: str
    observability_level: ObservabilityLevel
    tracks: tuple[TrackDescriptor, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "created": self.created,
            "creator": self.creator,
            "observability_level": int(self.observability_level),
            "tracks": [t.to_dict() for t in self.tracks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        tracks_raw = data.get("tracks") or []
        return cls(
            format_version=str(data["format_version"]),
            created=str(data["created"]),
            creator=str(data["creator"]),
            observability_level=ObservabilityLevel(int(data["observability_level"])),
            tracks=tuple(TrackDescriptor.from_dict(t) for t in tracks_raw),
        )


@dataclass(frozen=True)
class EncryptedTrack:
    """Binary track payload: nonce + tag + ciphertext."""

    track_id: str
    nonce: bytes
    tag: bytes
    ciphertext: bytes

    def to_bytes(self) -> bytes:
        return self.nonce + self.tag + self.ciphertext


@dataclass(frozen=True)
class PlainTrack:
    """Cleartext track before encryption."""

    track_id: str
    track_type: str
    payload: bytes
    resolution: ResolutionDescriptor | None = None


@dataclass(frozen=True)
class ProofLink:
    """One hash-chained proof entry."""

    index: int
    track_id: str
    sha256_plaintext: str
    previous_hash: str
    entry_hash: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProofLink:
        return cls(
            index=int(data["index"]),
            track_id=str(data["track_id"]),
            sha256_plaintext=str(data["sha256_plaintext"]),
            previous_hash=str(data["previous_hash"]),
            entry_hash=str(data["entry_hash"]),
        )


@dataclass(frozen=True)
class ProofExport:
    """Blockchain-style proof chain export."""

    format_version: str
    created: str
    manifest_sha256: str
    links: tuple[ProofLink, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "created": self.created,
            "manifest_sha256": self.manifest_sha256,
            "links": [
                {
                    "index": link.index,
                    "track_id": link.track_id,
                    "sha256_plaintext": link.sha256_plaintext,
                    "previous_hash": link.previous_hash,
                    "entry_hash": link.entry_hash,
                }
                for link in self.links
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProofExport:
        links_raw = data.get("links", [])
        return cls(
            format_version=str(data["format_version"]),
            created=str(data["created"]),
            manifest_sha256=str(data["manifest_sha256"]),
            links=tuple(ProofLink.from_dict(item) for item in links_raw),
        )
