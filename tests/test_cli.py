"""CLI subprocess tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "src.cli", *args]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def test_genkey_writes_32_bytes(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    key_path = tmp_path / "master.key"
    result = _run_cli("genkey", "-o", str(key_path), cwd=root)
    assert result.returncode == 0
    assert len(key_path.read_bytes()) == 32


def test_pack_inspect_unpack(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    key_path = tmp_path / "master.key"
    container = tmp_path / "demo.ento.zip"
    out_dir = tmp_path / "out"
    assert _run_cli("genkey", "-o", str(key_path), cwd=root).returncode == 0
    pack = _run_cli(
        "pack",
        "-k",
        str(key_path),
        "-o",
        str(container),
        "--fixtures",
        str(root / "data" / "fixtures"),
        cwd=root,
    )
    assert pack.returncode == 0, pack.stderr
    inspect = _run_cli("inspect", "-i", str(container), cwd=root)
    assert inspect.returncode == 0
    assert "format_version" in inspect.stdout
    unpack = _run_cli(
        "unpack",
        "-k",
        str(key_path),
        "-i",
        str(container),
        "-o",
        str(out_dir),
        cwd=root,
    )
    assert unpack.returncode == 0
    assert list(out_dir.glob("*.bin"))


def test_proof_command(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    key_path = tmp_path / "master.key"
    container = tmp_path / "demo.ento.zip"
    proof_path = tmp_path / "chain.json"
    _run_cli("genkey", "-o", str(key_path), cwd=root)
    _run_cli(
        "pack",
        "-k",
        str(key_path),
        "-o",
        str(container),
        "--fixtures",
        str(root / "data" / "fixtures"),
        cwd=root,
    )
    result = _run_cli(
        "proof",
        "-i",
        str(container),
        "-o",
        str(proof_path),
        cwd=root,
    )
    assert result.returncode == 0
    assert proof_path.exists()


def test_verify_command(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    key_path = tmp_path / "master.key"
    container = tmp_path / "demo.ento.zip"
    _run_cli("genkey", "-o", str(key_path), cwd=root)
    _run_cli(
        "pack",
        "-k",
        str(key_path),
        "-o",
        str(container),
        "--fixtures",
        str(root / "data" / "fixtures"),
        cwd=root,
    )
    result = _run_cli("verify", "-i", str(container), cwd=root)
    assert result.returncode == 0, result.stderr
    assert '"ok": true' in result.stdout.lower() or '"ok": True' in result.stdout
    with_key = _run_cli("verify", "-i", str(container), "-k", str(key_path), cwd=root)
    assert with_key.returncode == 0
    assert "plaintext_verified" in with_key.stdout
