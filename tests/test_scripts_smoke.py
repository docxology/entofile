"""Smoke tests for auxiliary scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src import crypto


def test_generate_api_docs(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "generate_api_docs.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (root / "output" / "docs" / "api_reference.md").exists()


def test_build_dashboard(fast_benchmark_project: tuple[Path, object]) -> None:
    root, cfg = fast_benchmark_project
    from src.analysis import run_benchmark_pipeline
    from src.dashboard import run_dashboard_build

    run_benchmark_pipeline(root, config=cfg)
    assert run_dashboard_build(root).exists()


def test_preflight_is_standalone_safe(tmp_path: Path) -> None:
    """PUB-3 (2026-06-10): a standalone public clone of the repo ships no template
    `infrastructure/`, so `00_preflight.py` must fail with a clear, actionable
    message and exit code 2 — never a raw ModuleNotFoundError traceback. Run a
    copy from an isolated tree with no `infrastructure/` ancestor."""
    import shutil

    root = Path(__file__).resolve().parent.parent
    proj = tmp_path / "entofile"
    (proj / "scripts").mkdir(parents=True)
    (proj / "manuscript").mkdir()
    shutil.copy(
        root / "scripts" / "00_preflight.py", proj / "scripts" / "00_preflight.py"
    )
    result = subprocess.run(
        [sys.executable, str(proj / "scripts" / "00_preflight.py")],
        cwd=proj,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "standalone checkout" in result.stderr
    assert "Traceback" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr


def test_generate_manuscript_variables_is_standalone_safe(tmp_path: Path) -> None:
    """DOC-1 (2026-06-10): z_generate_manuscript_variables.py is documented in the
    README/quickstart quick-start, but it hard-imported template infrastructure.
    On a standalone public clone it must fail with a clear message and exit code
    2 — never a raw ModuleNotFoundError — matching 00_preflight's guard."""
    import shutil

    root = Path(__file__).resolve().parent.parent
    proj = tmp_path / "entofile"
    (proj / "scripts").mkdir(parents=True)
    (proj / "manuscript").mkdir()
    shutil.copy(
        root / "scripts" / "z_generate_manuscript_variables.py",
        proj / "scripts" / "z_generate_manuscript_variables.py",
    )
    result = subprocess.run(
        [sys.executable, str(proj / "scripts" / "z_generate_manuscript_variables.py")],
        cwd=proj,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "standalone checkout" in result.stderr
    assert "Traceback" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr


def test_audit_publication_readiness_script() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "audit_publication_readiness.py"),
            "--check",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip().startswith("{")
    payload = json.loads(result.stdout)
    assert payload["format_version"] == crypto.FORMAT_VERSION
