"""CLI security behaviour tests."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

from src.cli import build_parser, cmd_genkey


def test_genkey_sets_private_mode_on_unix(tmp_path: Path) -> None:
    if sys.platform == "win32":
        pytest.skip("Unix file mode not applicable on Windows")
    key_path = tmp_path / "master.key"
    args = build_parser().parse_args(["genkey", "-o", str(key_path)])
    assert cmd_genkey(args) == 0
    mode = key_path.stat().st_mode
    assert stat.S_IMODE(mode) == 0o600
