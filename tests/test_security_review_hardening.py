"""Adversarial + hardening tests from the 2026-05-28 deep security review.

No mocks: every test builds a real ENTO container (or real ZIP) and exercises the
real code paths. These pin the review findings so a regression re-opens them.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from src import container, crypto, security
from src.crypto import decrypt_payload, derive_track_key, encrypt_payload, hkdf_sha256
from src.manifest import manifest_from_json, manifest_to_json
from src.models import PlainTrack
from src.proof import export_proof
from src.security import safe_read_member


def _build_container() -> bytes:
    key = crypto.generate_master_key()
    track = PlainTrack(track_id="alpha", track_type="ento:blockchain.proof", payload=b"SECRET-RESEARCH-DATA")
    return key, container.pack_container_bytes(key, (track,), format_version="0.4.0")


def _adversary_rewrite(blob: bytes, *, blank_digests: bool, corrupt_ciphertext: bool) -> bytes:
    """Simulate an attacker who controls the bytes: optionally blank manifest
    digests, corrupt the ciphertext, and (always) regenerate a self-consistent
    proof chain — which needs no secret."""
    zin = zipfile.ZipFile(io.BytesIO(blob))
    man = json.loads(zin.read("manifest.json"))
    if blank_digests:
        for t in man["tracks"]:
            t["sha256_ciphertext"] = ""
            t["sha256_plaintext"] = ""
    man_obj = manifest_from_json(json.dumps(man))
    man_json = manifest_to_json(man_obj)
    new_proof = export_proof(man_obj)  # attacker recomputes — no key needed
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("manifest.json", man_json)
        for name in zin.namelist():
            if name == "manifest.json":
                continue
            if name == "proof/chain.json":
                z.writestr(name, json.dumps(new_proof.to_dict(), indent=2) + "\n")
                continue
            data = zin.read(name)
            if corrupt_ciphertext and name.startswith("tracks/"):
                data = data[:-1] + bytes([data[-1] ^ 0xFF])
            z.writestr(name, data)
    return out.getvalue()


# --- F1: verification honesty -------------------------------------------------


def test_forged_container_is_not_reported_key_authenticated(tmp_path: Path) -> None:
    """ISC-1/ISC-18: corrupted ciphertext + blanked digests + forged proof must
    never be reported as adversarial (key-authenticated) integrity, and must fail
    closed under require_integrity."""
    _, blob = _build_container()
    evil = _adversary_rewrite(blob, blank_digests=True, corrupt_ciphertext=True)
    p = tmp_path / "evil.ento.zip"
    p.write_bytes(evil)

    result = container.verify_container(p)  # keyless
    assert result["integrity"] != "key-authenticated"
    assert result["integrity"] == "unverified"
    assert result["ciphertext_digests_present"] is False

    strict = container.verify_container(p, require_integrity=True)
    assert strict["ok"] is False


def test_keyed_verify_authenticates_intact_container(tmp_path: Path) -> None:
    """ISC-2/ISC-4: a key-based verify of an intact container reports
    key-authenticated integrity (GCM is the real anchor)."""
    key, blob = _build_container()
    p = tmp_path / "ok.ento.zip"
    p.write_bytes(blob)
    result = container.verify_container(p, key, require_integrity=True)
    assert result["integrity"] == "key-authenticated"
    assert result["ok"] is True
    assert result["plaintext_verified"] is True


def test_keyless_intact_container_is_digest_only(tmp_path: Path) -> None:
    """ISC-5: keyless verify of a legit AUDITABLE container is digest-only and ok."""
    _, blob = _build_container()
    p = tmp_path / "ok.ento.zip"
    p.write_bytes(blob)
    result = container.verify_container(p)
    assert result["integrity"] == "digest-only"
    assert result["ok"] is True
    assert result["ciphertext_digests_present"] is True


def test_blanked_digests_no_key_fails_require_integrity(tmp_path: Path) -> None:
    """ISC-3/ISC-6: blanked digests with no key is 'unverified' and fails closed."""
    _, blob = _build_container()
    stripped = _adversary_rewrite(blob, blank_digests=True, corrupt_ciphertext=False)
    p = tmp_path / "stripped.ento.zip"
    p.write_bytes(stripped)
    lenient = container.verify_container(p)
    assert lenient["integrity"] == "unverified"
    assert lenient["ciphertext_digests_present"] is False
    strict = container.verify_container(p, require_integrity=True)
    assert strict["ok"] is False


def test_keyed_verify_cannot_be_downgraded_by_header_mutation(tmp_path: Path) -> None:
    """No header-mutation downgrade: with the key supplied, blanking digests and
    dropping observability_level (unauthenticated manifest fields) cannot coerce
    verify into a weaker check — GCM is always attempted, so integrity stays
    key-authenticated. The integrity level is derived from the decrypt attempt,
    never read from an attacker-controlled header field."""
    key, blob = _build_container()
    zin = zipfile.ZipFile(io.BytesIO(blob))
    man = json.loads(zin.read("manifest.json"))
    for t in man["tracks"]:
        t["sha256_ciphertext"] = ""
        t["sha256_plaintext"] = ""
        # A well-formed SEALED manifest redacts byte_length to the sentinel 0; an
        # attacker claiming SEALED must match it, since SEALED + a non-zero byte_length
        # is now rejected as a forged-size bypass (see
        # test_keyed_verify_rejects_sealed_header_byte_length_bypass). This test isolates
        # the anti-downgrade property: even a well-formed SEALED-claim with blanked
        # digests cannot coerce a keyed verify away from key-authenticated.
        t["byte_length"] = 0
    man["observability_level"] = 0  # attacker drops to "sealed" header
    man_obj = manifest_from_json(json.dumps(man))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("manifest.json", manifest_to_json(man_obj))
        for name in zin.namelist():
            if name == "manifest.json":
                continue
            if name == "proof/chain.json":
                z.writestr(name, json.dumps(export_proof(man_obj).to_dict(), indent=2) + "\n")
                continue
            z.writestr(name, zin.read(name))  # ciphertext intact
    p = tmp_path / "downgrade.ento.zip"
    p.write_bytes(out.getvalue())
    result = container.verify_container(p, key, require_integrity=True)
    assert result["integrity"] == "key-authenticated"  # not coerced to digest-only/unverified
    assert result["plaintext_verified"] is True


def test_keyed_verify_still_catches_ciphertext_tamper(tmp_path: Path) -> None:
    """The key-based path remains adversarially sound: GCM rejects tampered
    ciphertext even when the attacker blanked digests and forged the proof."""
    key, blob = _build_container()
    evil = _adversary_rewrite(blob, blank_digests=True, corrupt_ciphertext=True)
    p = tmp_path / "evil.ento.zip"
    p.write_bytes(evil)
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        container.verify_container(p, key)


# --- F1 (CLI call-site): the shipped command must also fail closed -----------


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_cli_verify_fails_closed_on_forged_container(tmp_path: Path) -> None:
    """ISC-18 (CLI call-site): a keyless `verify` of a forged/digest-stripped
    container must exit non-zero by default; --allow-unverified opts out; an
    intact AUDITABLE container still verifies ok keyless (digest-only)."""
    root = Path(__file__).resolve().parent.parent
    _, blob = _build_container()
    evil = _adversary_rewrite(blob, blank_digests=True, corrupt_ciphertext=True)
    evil_path = tmp_path / "evil.ento.zip"
    evil_path.write_bytes(evil)
    intact_path = tmp_path / "ok.ento.zip"
    intact_path.write_bytes(blob)

    forged = _run_cli("verify", "-i", str(evil_path), cwd=root)
    assert forged.returncode == 1, forged.stdout
    assert '"integrity": "unverified"' in forged.stdout

    lenient = _run_cli("verify", "-i", str(evil_path), "--allow-unverified", cwd=root)
    assert lenient.returncode == 0

    intact = _run_cli("verify", "-i", str(intact_path), cwd=root)
    assert intact.returncode == 0
    assert '"integrity": "digest-only"' in intact.stdout


# --- F4: zip-bomb actual-bytes enforcement -----------------------------------


def test_safe_read_member_bounds_actual_decompressed_bytes() -> None:
    """ISC-7: a highly compressible member is bounded by its ACTUAL decompressed
    size, not its (attacker-controlled) declared file_size."""
    buf = io.BytesIO()
    payload = b"A" * 5_000_000  # ~5 MB, deflates to a few KB
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("tracks/x.ento", payload)
    zf2 = zipfile.ZipFile(buf)
    assert zf2.getinfo("tracks/x.ento").compress_size < 100_000  # declared-size spoof surface
    with pytest.raises(ValueError, match="exceeds uncompressed size limit"):
        safe_read_member(zf2, "tracks/x.ento", max_bytes=1024)
    assert safe_read_member(zf2, "tracks/x.ento", max_bytes=10_000_000) == payload


def test_validate_zip_archive_rejects_aggregate_overflow(tmp_path: Path) -> None:
    """ISC-8: many members each under the per-member cap but summing past the
    aggregate cap are rejected (real streamed zeros; central-directory sizes only)."""
    path = tmp_path / "aggregate.zip"
    per_member = 60 * 1024 * 1024  # < MAX_MEMBER_UNCOMPRESSED (64 MiB)
    count = (security.MAX_TOTAL_UNCOMPRESSED // per_member) + 2
    chunk = b"\x00" * (1024 * 1024)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(count):
            with zf.open(f"tracks/t{i}.ento", "w") as handle:
                remaining = per_member
                while remaining > 0:
                    take = min(remaining, len(chunk))
                    handle.write(chunk[:take])
                    remaining -= take
    with pytest.raises(ValueError, match="aggregate limit"):
        security.validate_zip_archive(path)


# --- F8 / F5: crypto surface --------------------------------------------------


def test_hkdf_production_empty_salt_path_is_pinned() -> None:
    """ISC-9: the production derive_track_key path (empty salt -> 32 zero bytes)
    is byte-pinned, locking the vetted-HKDF swap against drift."""
    master = bytes(range(32))
    # Byte-pin captured for ikm=0..31, track_id="eeg". The hand-rolled and the
    # vetted-library HKDF were proven byte-identical across all review vectors;
    # this value (and tests/data/test_vectors/hkdf_regression.json) lock the swap.
    expected = bytes.fromhex("58a3d65e6ce3d22f250d9778fed651ca45a3c51a0c097163f955fb786f8a070d")
    assert derive_track_key(master, "eeg") == expected
    assert hkdf_sha256(master, 32, info=b"ento:track:eeg") == expected
    # empty-salt convention must equal an explicit 32-zero salt
    assert hkdf_sha256(master, 32, info=b"x") == hkdf_sha256(master, 32, info=b"x", salt=b"\x00" * 32)


def test_decrypt_does_not_mask_non_crypto_errors() -> None:
    """ISC-10: only an AEAD auth failure is reported as 'authentication tag
    mismatch'; a shape error raises its own message, undisguised."""
    track_key = derive_track_key(crypto.generate_master_key(), "eeg")
    nonce, tag, ct = encrypt_payload(track_key, b"payload", format_version="0.2.0")
    # genuine tamper -> InvalidTag -> remapped message
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        decrypt_payload(track_key, nonce, tag, ct[:-1] + bytes([ct[-1] ^ 0xFF]), format_version="0.2.0")
    # shape error must NOT be relabeled as a tag mismatch
    with pytest.raises(ValueError, match="nonce must be 16 bytes"):
        decrypt_payload(track_key, b"short", tag, ct, format_version="0.2.0")
