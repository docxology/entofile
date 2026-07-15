"""Shared path and structured-data boundary contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.paths import ProjectPaths
from src.structured_data import (
    atomic_write_json,
    parse_json_object,
    read_json_object,
    read_toml_mapping,
    read_yaml_mapping,
)


def test_project_paths_support_independent_root_and_output(tmp_path: Path) -> None:
    root = tmp_path / "checkout"
    output = tmp_path / "run-output"
    paths = ProjectPaths.from_root(root, output_root=output)

    assert paths.root == root.resolve()
    assert paths.output == output.resolve()
    assert paths.report("release.json") == output / "reports" / "release.json"
    paths.ensure_output_dirs()
    assert paths.release.is_dir()
    assert paths.conformance.is_dir()


def test_project_paths_reject_nested_or_non_json_report_names(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    with pytest.raises(ValueError):
        paths.report("../release.json")
    with pytest.raises(ValueError):
        paths.report("release.yaml")


def test_structured_json_rejects_duplicate_keys_and_non_object_roots() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        parse_json_object('{"a": 1, "a": 2}')
    with pytest.raises(ValueError, match="root must be a JSON object"):
        parse_json_object("[1, 2]")


def test_structured_readers_and_atomic_writer_are_composable(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    yaml_path = tmp_path / "config.yaml"
    toml_path = tmp_path / "config.toml"
    atomic_write_json(json_path, {"ok": True, "count": 2})
    yaml_path.write_text("enabled: true\n", encoding="utf-8")
    toml_path.write_text("enabled = true\n", encoding="utf-8")

    assert read_json_object(json_path) == {"count": 2, "ok": True}
    assert read_yaml_mapping(yaml_path)["enabled"] is True
    assert read_toml_mapping(toml_path)["enabled"] is True


def test_structured_reader_rejects_symlinked_required_json(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text(json.dumps({"ok": True}), encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)

    with pytest.raises(FileNotFoundError):
        read_json_object(link)
