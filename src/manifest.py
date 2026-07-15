"""ENTO manifest validation and serialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]  # no bundled stubs; validate() is dynamically typed

from .errors import ManifestError
from .manifest_binding import validate_manifest_binding
from .models import Manifest, PlainTrack, TrackDescriptor
from .ontology import validate_track_resolution
from .structured_data import parse_json_object

_SCHEMA_CACHE: dict[Path, dict[str, Any]] = {}


def schema_path(project_root: Path | None = None) -> Path:
    """Return path to bundled JSON Schema."""
    root = project_root or Path(__file__).resolve().parent.parent
    return root / "data" / "ento_manifest_schema.json"


def load_schema(project_root: Path | None = None) -> dict[str, Any]:
    """Load and cache the manifest schema for the requested project root.

    The cache is keyed by the resolved schema path. A single process can validate
    containers from multiple checkouts, so a process-global single-schema cache would
    otherwise validate a later project against whichever checkout was loaded first.
    """
    path = schema_path(project_root).resolve()
    if path not in _SCHEMA_CACHE:
        loaded = parse_json_object(path.read_text(encoding="utf-8"), source=str(path))
        if not isinstance(loaded, dict):
            raise ManifestError(f"manifest schema must be a JSON object: {path}")
        _SCHEMA_CACHE[path] = loaded
    return _SCHEMA_CACHE[path]


def validate_manifest_dict(
    data: dict[str, Any], project_root: Path | None = None
) -> None:
    """Validate manifest dict against JSON Schema."""
    jsonschema.validate(data, load_schema(project_root))
    if data.get("format_version") == "0.5.0":
        validate_manifest_binding(Manifest.from_dict(data))


def manifest_to_json(manifest: Manifest, *, indent: int = 2) -> str:
    """Serialize manifest to JSON text."""
    return json.dumps(manifest.to_dict(), indent=indent, sort_keys=True) + "\n"


def manifest_from_json(text: str, *, project_root: Path | None = None) -> Manifest:
    """Parse and validate manifest JSON before constructing the typed model.

    Validation must happen on the parsed JSON object, before ``Manifest.from_dict``
    can coerce values such as ``byte_length`` or discard unknown fields. Duplicate
    object keys are rejected to avoid parser last-wins ambiguity.
    """
    parsed = parse_json_object(text, source="manifest JSON")
    validate_manifest_dict(parsed, project_root)
    manifest = Manifest.from_dict(parsed)
    validate_manifest_binding(manifest)
    return manifest


def build_track_descriptor(
    track: PlainTrack,
    encrypted_bytes: bytes,
    *,
    observability: int | None = None,
) -> TrackDescriptor:
    """Build manifest track entry from plaintext and ciphertext."""
    return TrackDescriptor(
        id=track.track_id,
        type=track.track_type,
        sha256_plaintext=crypto_sha256(track.payload),
        sha256_ciphertext=crypto_sha256(encrypted_bytes),
        byte_length=len(track.payload),
        resolution=track.resolution,
        observability=observability,
    )


def crypto_sha256(data: bytes) -> str:
    from . import crypto

    return crypto.sha256_hex(data)


def validate_plain_tracks(tracks: tuple[PlainTrack, ...]) -> None:
    """Validate ontology constraints and track-id uniqueness for all tracks.

    Track IDs must be unique: the pack path keys encrypted tracks by ``track_id``
    in a dict, so two tracks sharing an id would silently collapse to the last one —
    the manifest would still list both descriptors while the ZIP held a single
    member, producing a lossy container that nonetheless reports ``key-authenticated``
    at redacted export levels (the plaintext-digest check is skipped there). Reject
    duplicates up front, mirroring the read-side duplicate-member rejection in
    ``security.validate_zip_member_names``.
    """
    from .security import validate_track_id

    ids = [track.track_id for track in tracks]
    if len(ids) != len(set(ids)):
        dupes = sorted({tid for tid in ids if ids.count(tid) > 1})
        raise ManifestError(f"duplicate track ids: {dupes}")
    for track in tracks:
        validate_track_id(track.track_id)
        validate_track_resolution(track)
