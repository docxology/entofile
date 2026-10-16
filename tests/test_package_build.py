"""Package build smoke tests.

Verifies that ``uv build`` produces a valid sdist + wheel and that the
wheel installs cleanly into a fresh virtualenv.  These tests are marked
``slow`` so they can be skipped in fast CI loops.
"""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from src.structured_data import read_toml_mapping

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Subprocess ceiling for build/install steps. On slow or heavily loaded
# filesystems (e.g. external archive drives) `uv build` and venv creation can
# take far longer than a small fixed default; scale via ENTOFILE_BUILD_TIMEOUT_SECONDS.
_BUILD_TIMEOUT = int(os.environ.get("ENTOFILE_BUILD_TIMEOUT_SECONDS", "600"))


@pytest.mark.slow
def test_uv_build_produces_wheel_and_sdist(tmp_path: Path) -> None:
    """``uv build`` should produce both a .whl and a .tar.gz."""
    result = subprocess.run(
        ["uv", "build", "--out-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
        timeout=_BUILD_TIMEOUT,
    )
    assert result.returncode == 0, result.stderr
    wheels = list(tmp_path.glob("*.whl"))
    sdists = list(tmp_path.glob("*.tar.gz"))
    assert len(wheels) == 1, f"Expected 1 wheel, found {len(wheels)}"
    assert len(sdists) == 1, f"Expected 1 sdist, found {len(sdists)}"

    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    assert "src/__init__.py" in names
    assert "src/py.typed" in names
    assert "src/resources/ento_manifest_schema.json" in names
    assert "src/resources/fixtures/eeg.csv" in names
    assert not any(name.startswith(("build/", "tests/")) for name in names)


@pytest.mark.slow
def test_wheel_installs_and_imports(tmp_path: Path) -> None:
    """The built wheel should install and ``import entofile`` should succeed."""
    build_result = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
        timeout=_BUILD_TIMEOUT,
    )
    assert build_result.returncode == 0, build_result.stderr

    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1
    wheel_path = wheels[0]

    venv_dir = tmp_path / "test_venv"
    venv_result = subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(venv_dir)],
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
        timeout=_BUILD_TIMEOUT,
    )
    assert venv_result.returncode == 0, venv_result.stderr

    python = venv_dir / "bin" / "python"
    install_result = subprocess.run(
        ["uv", "pip", "install", "--python", str(python), str(wheel_path)],
        capture_output=True,
        text=True,
        timeout=_BUILD_TIMEOUT,
    )
    assert install_result.returncode == 0, install_result.stderr

    import_result = subprocess.run(
        [
            str(python),
            "-c",
            "from src.crypto import FORMAT_VERSION, generate_master_key; "
            "from pathlib import Path; "
            "from src.container import pack_container_bytes, unpack_container; "
            "from src.fixtures import load_fixture_tracks; "
            "assert FORMAT_VERSION == '0.5.0'; "
            "key = generate_master_key(); tracks = load_fixture_tracks(); "
            "blob = pack_container_bytes(key, tracks); "
            "path = Path('installed.ento.zip'); path.write_bytes(blob); "
            "manifest, payloads = unpack_container(path, key); "
            "assert payloads == {track.track_id: track.payload for track in tracks}; "
            "print('import ok')",
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=_BUILD_TIMEOUT,
    )
    assert import_result.returncode == 0, import_result.stderr
    assert "import ok" in import_result.stdout


@pytest.mark.slow
def test_pyproject_version_matches_release_label() -> None:
    """The package patch version should normalize the paper release label."""
    pyproject = _PROJECT_ROOT / "pyproject.toml"
    pp = read_toml_mapping(pyproject)
    pp_version = pp["project"]["version"]

    cff_path = _PROJECT_ROOT / "CITATION.cff"
    cff_text = cff_path.read_text(encoding="utf-8")
    cff_version = None
    for line in cff_text.splitlines():
        if line.startswith("version:"):
            cff_version = line.split(":", 1)[1].strip().strip('"')
            break

    assert cff_version is not None, "CITATION.cff version not found"
    assert cff_version == ".".join(pp_version.split(".")[:2]), (
        "pyproject.toml package version must preserve the CITATION.cff major/minor "
        f"release label: '{pp_version}' vs '{cff_version}'"
    )
