"""Pinned regression tests for ENTO cryptography."""

from __future__ import annotations

import json
from pathlib import Path

from src.crypto import hkdf_sha256


def _load_vector(name: str) -> dict[str, object]:
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "test_vectors" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_hkdf_regression_vector() -> None:
    vector = _load_vector("hkdf_regression.json")
    ikm = bytes.fromhex(str(vector["ikm_hex"]))
    salt = bytes.fromhex(str(vector["salt_hex"]))
    info = bytes.fromhex(str(vector["info_hex"]))
    length = int(vector["length"])
    expected = bytes.fromhex(str(vector["okm_hex"]))
    assert hkdf_sha256(ikm, length, info=info, salt=salt) == expected
