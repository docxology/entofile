"""Fail-closed structured-data readers and atomic text writers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import tomllib
import yaml


def reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate JSON object keys instead of accepting parser last-wins data."""
    seen: set[str] = set()
    for key, _value in pairs:
        if key in seen:
            raise ValueError(f"duplicate JSON key: {key!r}")
        seen.add(key)
    return dict(pairs)


def reject_nonstandard_json_constant(value: str) -> None:
    """Reject NaN/Infinity extensions accepted by Python but not JSON."""
    raise ValueError(f"non-standard JSON constant: {value}")


def parse_json_object(text: str, *, source: str = "JSON") -> dict[str, Any]:
    """Parse one JSON object with duplicate-key and root-type enforcement."""
    value = json.loads(
        text,
        object_pairs_hook=reject_duplicate_json_keys,
        parse_constant=reject_nonstandard_json_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{source} root must be a JSON object")
    return value


def read_json_object(path: Path, *, required: bool = True) -> dict[str, Any]:
    """Read one JSON object, preserving fail-closed errors for required files."""
    if not path.is_file() or path.is_symlink():
        if required:
            raise FileNotFoundError(f"required JSON file is missing or symlinked: {path}")
        return {}
    return parse_json_object(path.read_text(encoding="utf-8"), source=str(path))


def read_yaml_mapping(path: Path, *, required: bool = True) -> dict[str, Any]:
    """Read a YAML mapping using ``safe_load`` and reject non-mapping roots."""
    if not path.is_file() or path.is_symlink():
        if required:
            raise FileNotFoundError(f"required YAML file is missing or symlinked: {path}")
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if value is None and not required:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be a YAML mapping")
    return value


def read_toml_mapping(path: Path, *, required: bool = True) -> dict[str, Any]:
    """Read one TOML mapping and reject missing/symlinked files."""
    if not path.is_file() or path.is_symlink():
        if required:
            raise FileNotFoundError(f"required TOML file is missing or symlinked: {path}")
        return {}
    value = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be a TOML mapping")
    return value


def atomic_write_text(path: Path, text: str) -> None:
    """Replace a file atomically without following a pre-existing symlink."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise OSError(f"refusing to replace symlinked output: {path}")
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent, text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            Path(temporary_name).unlink(missing_ok=True)
        finally:
            raise


def atomic_write_json(path: Path, payload: object) -> None:
    """Serialize JSON deterministically and replace the target atomically."""
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
