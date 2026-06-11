"""Small JSON/JSONL helpers for CLI automation and local telemetry."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    """Current UTC timestamp with second precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def redact_error(message: object, *, max_chars: int = 500) -> str:
    """Bound error text for sidecar files without exposing large blobs."""
    text = str(message)
    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    """Write a JSON payload, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_jsonl(path: Path, payload: dict[str, Any]) -> Path:
    """Append a single JSONL event, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def command_event(
    *,
    command: str,
    ok: bool,
    exit_code: int,
    fields: dict[str, Any] | None = None,
    error: object | None = None,
) -> dict[str, Any]:
    """Build the stable local telemetry event for an ENTO CLI command."""
    payload: dict[str, Any] = {
        "event": "ento.cli.command",
        "schema_version": "1",
        "timestamp": utc_timestamp(),
        "command": command,
        "ok": ok,
        "exit_code": exit_code,
    }
    for key, value in (fields or {}).items():
        if value is not None:
            payload[key] = value
    if error is not None:
        payload["error"] = redact_error(error)
    return payload
