"""Unit tests for ZIP ingestion limits without mocks."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from src.security import (
    MAX_MEMBER_UNCOMPRESSED,
    MAX_ZIP_BYTES,
    MAX_ZIP_ENTRIES,
    assert_zip_members_match_manifest,
    validate_track_id,
    validate_zip_archive,
    validate_zip_member_names,
)


def test_validate_track_id_rejects_path_segments() -> None:
    with pytest.raises(ValueError, match="invalid track id"):
        validate_track_id("../escape")


def test_validate_zip_member_names_rejects_unsafe_paths() -> None:
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        validate_zip_member_names(["tracks/../evil.ento"])


def test_validate_zip_archive_rejects_oversize_file(tmp_path: Path) -> None:
    huge = tmp_path / "huge.zip"
    with huge.open("wb") as handle:
        handle.seek(MAX_ZIP_BYTES + 1)
        handle.write(b"\0")
    with pytest.raises(ValueError, match="max size"):
        validate_zip_archive(huge)


def test_validate_zip_archive_rejects_too_many_entries(tmp_path: Path) -> None:
    path = tmp_path / "many.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for index in range(MAX_ZIP_ENTRIES + 1):
            zf.writestr(f"tracks/t{index}.ento", b"x")
    with pytest.raises(ValueError, match="too many ZIP entries"):
        validate_zip_archive(path)


def test_validate_zip_archive_rejects_large_member_payload(tmp_path: Path) -> None:
    path = tmp_path / "bigmember.zip"
    payload = b"x" * (MAX_MEMBER_UNCOMPRESSED + 1)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("tracks/big.ento", payload)
    with pytest.raises(ValueError, match="exceeds uncompressed size limit"):
        validate_zip_archive(path)


def test_assert_zip_members_detects_extra_member() -> None:
    with pytest.raises(ValueError, match="unexpected ZIP members"):
        assert_zip_members_match_manifest(
            ["manifest.json", "tracks/a.ento", "tracks/extra.ento"],
            ("a",),
            include_proof=False,
        )
