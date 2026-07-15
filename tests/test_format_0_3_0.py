"""ENTO format 0.3.0 — hardened nonce (12-byte) + AEAD associated data.

0.3.0 is the hardened successor to the published 0.2.0 baseline: it uses the
standard 96-bit GCM nonce and binds (format_version, track_id) as associated data
so a format downgrade or cross-track relabel fails authentication. 0.5.0 is the
current default write format; 0.2.0 remains a readable/writable compatibility
format. No mocks: real containers.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from src import container, crypto
from src.crypto import (
    decrypt_payload,
    derive_track_key,
    encrypt_payload,
    nonce_size_for,
    track_aad,
)
from src.manifest import manifest_from_json, manifest_to_json
from src.models import PlainTrack

_TRACK = PlainTrack(
    track_id="alpha", track_type="ento:blockchain.proof", payload=b"hardened-payload"
)


# --- format metadata ----------------------------------------------------------


def test_nonce_size_per_format() -> None:
    assert nonce_size_for("0.2.0") == 16
    assert nonce_size_for("0.3.0") == 12
    with pytest.raises(ValueError, match="unsupported format_version"):
        nonce_size_for("9.9.9")


def test_track_aad_binds_only_for_0_3_0() -> None:
    assert track_aad("0.2.0", "alpha") is None
    assert track_aad("0.3.0", "alpha") == b"ento:0.3.0:track:alpha"
    with pytest.raises(ValueError, match="track_id is required"):
        track_aad("0.3.0", None)
    with pytest.raises(ValueError, match="unsupported format_version"):
        track_aad("9.9.9", "alpha")


# --- deterministic vector lock ------------------------------------------------


def test_0_3_0_deterministic_vector() -> None:
    """Pin the 0.3.0 AEAD output for a fixed key+nonce+track_id so the nonce
    length and AAD construction cannot silently drift."""
    tk = derive_track_key(bytes(range(32)), "eeg")
    nonce = bytes.fromhex("0102030405060708090a0b0c")
    n, t, c = encrypt_payload(
        tk, b"ento-0.3.0-vector", _nonce=nonce, format_version="0.3.0", track_id="eeg"
    )
    assert len(n) == 12
    assert t.hex() == "f045f678b8f34af0d6f358340395b17c"
    assert c.hex() == "3e59c1c8880f9e91059989ce31b782c091"
    assert (
        decrypt_payload(tk, n, t, c, format_version="0.3.0", track_id="eeg")
        == b"ento-0.3.0-vector"
    )


# --- AAD is load-bearing ------------------------------------------------------


def test_0_3_0_aad_binds_track_id() -> None:
    tk = derive_track_key(bytes(range(32)), "eeg")
    n, t, c = encrypt_payload(tk, b"x", format_version="0.3.0", track_id="eeg")
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        decrypt_payload(tk, n, t, c, format_version="0.3.0", track_id="vcf")  # relabel


def test_0_3_0_to_0_2_0_downgrade_fails() -> None:
    tk = derive_track_key(bytes(range(32)), "eeg")
    n, t, c = encrypt_payload(tk, b"x", format_version="0.3.0", track_id="eeg")
    with pytest.raises(ValueError, match="nonce must be"):  # 12-byte nonce rejected by 0.2.0 path
        decrypt_payload(tk, n, t, c, format_version="0.2.0", track_id="eeg")


# --- container round-trip + cross-version read-compat -------------------------


def test_0_3_0_container_round_trip(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    out = tmp_path / "v3.ento.zip"
    manifest = container.pack_container(out, key, (_TRACK,), format_version="0.3.0")
    assert manifest.format_version == "0.3.0"
    got_manifest, payloads = container.unpack_container(out, key)
    assert got_manifest.format_version == "0.3.0"
    assert payloads["alpha"] == _TRACK.payload
    # nonce on the wire is 12 bytes for 0.3.0
    with zipfile.ZipFile(out) as zf:
        raw = zf.read("tracks/alpha.ento")
    assert len(raw) - 16 - len(_TRACK.payload) == 12  # nonce(12) + tag(16) + ct


def test_0_2_0_still_round_trips_after_0_3_0_added(tmp_path: Path) -> None:
    """Backward read-compat: the published 0.2.0 legacy path is untouched."""
    key = crypto.generate_master_key()
    out = tmp_path / "v2.ento.zip"
    manifest = container.pack_container(out, key, (_TRACK,), format_version="0.2.0")
    assert manifest.format_version == "0.2.0"
    _, payloads = container.unpack_container(out, key)
    assert payloads["alpha"] == _TRACK.payload
    with zipfile.ZipFile(out) as zf:
        raw = zf.read("tracks/alpha.ento")
    assert len(raw) - 16 - len(_TRACK.payload) == 16  # 0.2.0 nonce(16)


def test_0_3_0_keyed_verify_is_key_authenticated(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    out = tmp_path / "v3.ento.zip"
    container.pack_container(out, key, (_TRACK,), format_version="0.3.0")
    result = container.verify_container(out, key, require_integrity=True)
    assert result["integrity"] == "key-authenticated"
    assert result["ok"] is True


def test_0_3_0_container_format_downgrade_in_manifest_fails(tmp_path: Path) -> None:
    """Editing a 0.3.0 container's manifest to claim 0.2.0 must not decrypt:
    the 12-byte nonce is parsed under 0.2.0's 16-byte rule and authentication fails."""
    key = crypto.generate_master_key()
    blob = container.pack_container_bytes(key, (_TRACK,), format_version="0.3.0")
    zin = zipfile.ZipFile(io.BytesIO(blob))
    man = json.loads(zin.read("manifest.json"))
    man["format_version"] = "0.2.0"  # attacker downgrade
    man_obj = manifest_from_json(json.dumps(man))
    from src.proof import export_proof

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("manifest.json", manifest_to_json(man_obj))
        for name in zin.namelist():
            if name == "manifest.json":
                continue
            if name == "proof/chain.json":
                z.writestr(
                    name, json.dumps(export_proof(man_obj).to_dict(), indent=2) + "\n"
                )
                continue
            z.writestr(name, zin.read(name))
    p = tmp_path / "downgraded.ento.zip"
    p.write_bytes(out.getvalue())
    with pytest.raises(ValueError):
        container.unpack_container(p, key)


# --- CLI opt-in ---------------------------------------------------------------


def test_cli_pack_format_0_3_0_round_trips(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    key_path = tmp_path / "master.key"
    container_path = tmp_path / "v3.ento.zip"
    out_dir = tmp_path / "out"

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "src.cli", *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

    assert run("genkey", "-o", str(key_path)).returncode == 0
    packed = run(
        "pack",
        "-k",
        str(key_path),
        "-o",
        str(container_path),
        "--fixtures",
        str(root / "data" / "fixtures"),
        "--format",
        "0.3.0",
    )
    assert packed.returncode == 0, packed.stderr
    inspected = run("inspect", "-i", str(container_path))
    assert '"format_version": "0.3.0"' in inspected.stdout
    unpacked = run(
        "unpack", "-k", str(key_path), "-i", str(container_path), "-o", str(out_dir)
    )
    assert unpacked.returncode == 0, unpacked.stderr
    assert list(out_dir.glob("*.bin"))
