"""SBOM skeleton builder tests (version-of-record + requirement parsing)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.sbom import build_cyclonedx_skeleton, parse_requirement_names, release_label

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_release_label_reads_manuscript_config() -> None:
    """The SBOM application version is paper.version from manuscript/config.yaml —
    the same label CITATION.cff pins — never a hardcoded literal."""
    label = release_label(PROJECT_ROOT)
    assert label == "0.4"


def test_release_label_fails_closed_without_config(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manuscript config not found"):
        release_label(tmp_path)


def test_release_label_fails_closed_without_version(tmp_path: Path) -> None:
    config = tmp_path / "manuscript" / "config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("paper: {title: x}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"paper.version missing"):
        release_label(tmp_path)


def test_parse_requirement_names_dedupes_and_skips_noise() -> None:
    text = "\n".join(
        [
            "# comment",
            "-e .",
            "numpy==1.26.0",
            "pyyaml==6.0.1",
            "numpy==1.26.0",
            "qrcode[pil]==8.0",
            "",
        ]
    )
    assert parse_requirement_names(text) == ["numpy", "pyyaml", "qrcode"]


def test_build_cyclonedx_skeleton_binds_real_release_label() -> None:
    """Regression: the component version was once hardcoded '0.2.0' in the
    export script, drifting from the 0.4 release label."""
    bom = build_cyclonedx_skeleton(PROJECT_ROOT, "numpy==1.26.0\n")
    assert bom["bomFormat"] == "CycloneDX"
    component = bom["metadata"]["component"]
    assert component["name"] == "entofile"
    assert component["version"] == release_label(PROJECT_ROOT)
    assert component["version"] != "0.2.0"
    assert bom["components"] == [
        {"type": "library", "name": "numpy", "bom-ref": "pkg:pypi/numpy"}
    ]
