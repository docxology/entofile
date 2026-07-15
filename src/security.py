"""Security helpers for ENTO container ingestion and CLI output paths."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from .errors import ContainerError

# Safe track identifiers: no path separators or parent segments.
TRACK_ID_PATTERN = re.compile(r"^[a-z0-9._-]+$")

# ZIP ingestion limits (reference implementation; tune per deployment).
MAX_ZIP_BYTES = 256 * 1024 * 1024
MAX_ZIP_ENTRIES = 256
MAX_MEMBER_UNCOMPRESSED = 64 * 1024 * 1024
# Aggregate decompressed budget across all members — bounds the
# entries x per-member worst case so a many-member archive cannot fan out.
MAX_TOTAL_UNCOMPRESSED = 512 * 1024 * 1024
# manifest.json is parsed eagerly; keep it small regardless of the member cap.
MAX_MANIFEST_BYTES = 4 * 1024 * 1024

ALLOWED_ZIP_PREFIXES = ("manifest.json", "tracks/", "proof/")


def validate_track_id(track_id: str) -> None:
    """Reject track IDs that could escape output directories or ZIP layout."""
    if not track_id or ".." in track_id or not TRACK_ID_PATTERN.fullmatch(track_id):
        raise ContainerError(f"invalid track id {track_id!r}: must match [a-z0-9._-]+ with no path segments")


def safe_output_path(output_dir: Path, track_id: str) -> Path:
    """Resolve a track output file strictly under output_dir."""
    validate_track_id(track_id)
    base = output_dir.resolve()
    target = (base / f"{track_id}.bin").resolve()
    if base not in target.parents and target != base:
        raise ContainerError(f"refusing unsafe output path for track {track_id!r}")
    return target


def _member_uncompressed_size(info: zipfile.ZipInfo) -> int:
    return info.file_size


def validate_zip_archive(source: Path) -> None:
    """Fail closed on oversize archives or zip bombs before full read.

    ``ZipExtFile.read`` truncates output to the declared ``file_size`` (CPython
    tracks an uncompressed-bytes-remaining counter), so a member can never yield
    MORE than it declares — the declared per-member and aggregate caps here are
    therefore a real upper bound on decompressed bytes, not just a cheap pre-check.
    :func:`safe_read_member` adds a second, independent ceiling (it never
    materializes more than ``max_bytes`` even if the declared size is large).
    """
    size = source.stat().st_size
    if size > MAX_ZIP_BYTES:
        raise ContainerError(f"container exceeds max size ({size} > {MAX_ZIP_BYTES} bytes)")
    with zipfile.ZipFile(source, "r") as zf:
        names = zf.namelist()
        if len(names) > MAX_ZIP_ENTRIES:
            raise ContainerError(f"container has too many ZIP entries ({len(names)})")
        declared_total = 0
        for name in names:
            info = zf.getinfo(name)
            if _member_uncompressed_size(info) > MAX_MEMBER_UNCOMPRESSED:
                raise ContainerError(f"ZIP member {name!r} exceeds uncompressed size limit")
            declared_total += _member_uncompressed_size(info)
        if declared_total > MAX_TOTAL_UNCOMPRESSED:
            raise ContainerError(
                f"container declares {declared_total} uncompressed bytes (> {MAX_TOTAL_UNCOMPRESSED} aggregate limit)"
            )


def safe_read_member(
    zf: zipfile.ZipFile,
    name: str,
    *,
    max_bytes: int = MAX_MEMBER_UNCOMPRESSED,
) -> bytes:
    """Read a ZIP member enforcing a cap on *actual* decompressed bytes.

    Reads at most ``max_bytes + 1`` and rejects any overflow, so this materializes
    no more than ``max_bytes`` regardless of the declared ``file_size``. This is an
    independent ceiling layered on top of :func:`validate_zip_archive`'s declared-size
    caps — useful when a caller wants a tighter per-read bound (e.g. the 4 MiB
    manifest cap) than the 64 MiB member limit.
    """
    with zf.open(name, "r") as handle:
        data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ContainerError(f"ZIP member {name!r} exceeds uncompressed size limit ({max_bytes} bytes)")
    return data


def expected_zip_members(manifest_track_ids: tuple[str, ...], *, include_proof: bool) -> set[str]:
    """Return the exact member set allowed for a well-formed ENTO container."""
    members = {"manifest.json"}
    members.update(f"tracks/{track_id}.ento" for track_id in manifest_track_ids)
    if include_proof:
        members.add("proof/chain.json")
    return members


def validate_zip_member_names(names: list[str]) -> None:
    """Reject unexpected, malformed, or duplicated ZIP paths."""
    # Duplicate member names collapse under set() in the membership check, letting
    # a second blob ride inside a duplicated allowed name while zipfile resolves
    # reads to the last physical entry — a parser differential. Reject up front.
    if len(names) != len(set(names)):
        dupes = sorted({name for name in names if names.count(name) > 1})
        raise ContainerError(f"duplicate ZIP members: {dupes}")
    for name in names:
        if name.startswith("/") or ".." in name.split("/"):
            raise ContainerError(f"unsafe ZIP member path: {name!r}")
        if not name.startswith(ALLOWED_ZIP_PREFIXES):
            raise ContainerError(f"unexpected ZIP member: {name!r}")


def assert_zip_members_match_manifest(
    names: list[str],
    manifest_track_ids: tuple[str, ...],
    *,
    include_proof: bool,
) -> None:
    """Ensure ZIP listing matches manifest tracks (no extras, no omissions)."""
    validate_zip_member_names(names)
    expected = expected_zip_members(manifest_track_ids, include_proof=include_proof)
    actual = set(names)
    extra = actual - expected
    missing = expected - actual
    if extra:
        raise ContainerError(f"unexpected ZIP members: {sorted(extra)}")
    if missing:
        raise ContainerError(f"missing ZIP members: {sorted(missing)}")
