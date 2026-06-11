"""CLI automation sidecars and telemetry."""

from __future__ import annotations

import json
from pathlib import Path

from src.cli import main


def test_cli_json_output_success_envelope(tmp_path: Path) -> None:
    key = tmp_path / "master.key"
    sidecar = tmp_path / "genkey.json"
    assert main(["genkey", "-o", str(key), "--json-output", str(sidecar)]) == 0
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["command"] == "genkey"
    assert payload["exit_code"] == 0
    assert payload["output"] == str(key)
    assert payload["key_bytes"] == 32
    assert key.read_bytes().hex() not in sidecar.read_text(encoding="utf-8")


def test_cli_json_output_failure_envelope(tmp_path: Path) -> None:
    bad_key = tmp_path / "bad.key"
    bad_key.write_bytes(b"short")
    sidecar = tmp_path / "pack-failure.json"
    code = main(
        [
            "pack",
            "-k",
            str(bad_key),
            "-o",
            str(tmp_path / "x.ento.zip"),
            "--json-output",
            str(sidecar),
        ]
    )
    assert code == 1
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["command"] == "pack"
    assert payload["exit_code"] == 1
    assert "key file must be 32 bytes" in payload["error"]
    assert bad_key.read_bytes().hex() not in sidecar.read_text(encoding="utf-8")


def test_cli_telemetry_jsonl_success_and_failure(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    telemetry = tmp_path / "events.jsonl"
    key = tmp_path / "master.key"
    container = tmp_path / "demo.ento.zip"
    assert main(["genkey", "-o", str(key), "--telemetry-jsonl", str(telemetry)]) == 0
    assert (
        main(
            [
                "pack",
                "-k",
                str(key),
                "-o",
                str(container),
                "--fixtures",
                str(root / "data" / "fixtures"),
                "--telemetry-jsonl",
                str(telemetry),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "verify",
                "-i",
                str(container),
                "-k",
                str(key),
                "--telemetry-jsonl",
                str(telemetry),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "verify",
                "-i",
                str(tmp_path / "missing.ento.zip"),
                "--telemetry-jsonl",
                str(telemetry),
            ]
        )
        == 1
    )
    events = [
        json.loads(line)
        for line in telemetry.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [event["command"] for event in events] == ["genkey", "pack", "verify", "verify"]
    assert events[1]["format_version"] == "0.4.0"
    assert events[2]["integrity"] == "key-authenticated"
    assert events[-1]["ok"] is False
    assert key.read_bytes().hex() not in telemetry.read_text(encoding="utf-8")
