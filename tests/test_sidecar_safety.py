"""Real filesystem regression tests for non-destructive CLI sidecars."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.cli import main
from src.telemetry import append_jsonl, write_json


@pytest.mark.parametrize("option", ["--json-output", "--telemetry-jsonl"])
def test_sidecar_cannot_replace_generated_key(tmp_path: Path, option: str) -> None:
    key = tmp_path / "master.key"
    assert main(["genkey", "-o", str(key), option, str(key)]) == 1
    assert not key.exists()


@pytest.mark.parametrize("option", ["--json-output", "--telemetry-jsonl"])
@pytest.mark.parametrize("alias_type", ["direct", "symlink", "hardlink"])
def test_sidecar_preserves_key_input(
    tmp_path: Path, option: str, alias_type: str
) -> None:
    key = tmp_path / "master.key"
    original = bytes(range(32))
    key.write_bytes(original)
    sidecar = tmp_path / "sidecar"
    if alias_type == "symlink":
        sidecar.symlink_to(key)
    elif alias_type == "hardlink":
        sidecar.hardlink_to(key)
    else:
        sidecar = key
    output = tmp_path / "container.zip"
    assert main(["pack", "-k", str(key), "-o", str(output), option, str(sidecar)]) == 1
    assert key.read_bytes() == original
    assert not output.exists()


def test_sidecars_cannot_alias_each_other(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    assert main(["types", "--json-output", str(output), "--telemetry-jsonl", str(output)]) == 1
    assert not output.exists()


def test_sidecar_failure_does_not_raise_traceback(tmp_path: Path, capsys) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    assert main(["types", "--json-output", str(directory)]) == 1
    assert "could not write sidecars" in capsys.readouterr().err


@pytest.mark.parametrize("writer", [write_json, append_jsonl])
def test_telemetry_writers_refuse_symlinks(tmp_path: Path, writer) -> None:
    target = tmp_path / "target"
    target.write_text("preserve", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(OSError, match="symlink"):
        writer(link, {"ok": True})
    assert target.read_text(encoding="utf-8") == "preserve"


def test_sidecar_json_is_complete(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    write_json(output, {"ok": True})
    write_json(output, {"ok": False})
    assert json.loads(output.read_text(encoding="utf-8")) == {"ok": False}


def test_telemetry_cannot_corrupt_hardlinked_fixture(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    original = fixtures / "eeg.csv"
    original.write_bytes(b"preserve fixture")
    telemetry = tmp_path / "events.jsonl"
    telemetry.hardlink_to(original)
    key = tmp_path / "master.key"
    key.write_bytes(bytes(32))
    destination = tmp_path / "out.zip"
    assert main([
        "pack", "-k", str(key), "-o", str(destination),
        "--fixtures", str(fixtures), "--telemetry-jsonl", str(telemetry),
    ]) == 1
    assert original.read_bytes() == b"preserve fixture"
    assert not destination.exists()
    with pytest.raises(OSError, match="multiply-linked"):
        append_jsonl(telemetry, {"ok": True})
    assert original.read_bytes() == b"preserve fixture"
