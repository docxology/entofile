"""Deterministic ENTO conformance fixture generation."""

from __future__ import annotations

import json
import warnings
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import crypto
from .container import unpack_container, verify_container
from .manifest import build_track_descriptor, manifest_to_json
from .models import EncryptedTrack, Manifest, ObservabilityLevel, PlainTrack
from .ontology import default_resolution
from .padding import pad_payload
from .proof import export_proof
from .telemetry import redact_error, write_json

CONFORMANCE_KEY = bytes(range(crypto.MASTER_KEY_SIZE))
CONFORMANCE_CREATED = "2026-01-01T00:00:00Z"
CONFORMANCE_TRACK = PlainTrack(
    track_id="alpha",
    track_type="ento:spectrogram",
    payload=b"ENTO conformance payload\n",
    resolution=default_resolution("ento:spectrogram"),
)


@dataclass(frozen=True)
class ConformanceCase:
    case_id: str
    filename: str
    category: str
    format_version: str
    expected_verify_with_key: bool
    expected_verify_without_key: bool
    expected_unpack: bool
    description: str


GOOD_CASES: tuple[ConformanceCase, ...] = tuple(
    ConformanceCase(
        case_id=f"good-{version}",
        filename=f"good-{version}.ento.zip",
        category="known-good",
        format_version=version,
        expected_verify_with_key=True,
        expected_verify_without_key=True,
        expected_unpack=True,
        description=f"Valid ENTO {version} container with one auditable track.",
    )
    for version in crypto.SUPPORTED_FORMAT_VERSIONS
)

BAD_CASES: tuple[ConformanceCase, ...] = (
    ConformanceCase(
        case_id="bad-tamper",
        filename="bad-tamper.ento.zip",
        category="known-bad",
        format_version=crypto.FORMAT_VERSION_LATEST,
        expected_verify_with_key=False,
        expected_verify_without_key=False,
        expected_unpack=False,
        description="Ciphertext byte is flipped; keyed verify/unpack must reject.",
    ),
    ConformanceCase(
        case_id="bad-duplicate-member",
        filename="bad-duplicate-member.ento.zip",
        category="known-bad",
        format_version=crypto.FORMAT_VERSION,
        expected_verify_with_key=False,
        expected_verify_without_key=False,
        expected_unpack=False,
        description="ZIP contains a duplicate track member; readers must reject.",
    ),
    ConformanceCase(
        case_id="bad-path-escape",
        filename="bad-path-escape.ento.zip",
        category="known-bad",
        format_version=crypto.FORMAT_VERSION,
        expected_verify_with_key=False,
        expected_verify_without_key=False,
        expected_unpack=False,
        description="Manifest and member names attempt path escape; readers must reject.",
    ),
)


def generate_conformance_fixtures(output_dir: Path) -> Path:
    """Generate deterministic conformance fixtures and manifest under ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for case in GOOD_CASES:
        path = output_dir / case.filename
        _write_good_container(path, case.format_version)
        entries.append(_manifest_entry(case, path))

    good_latest = output_dir / f"good-{crypto.FORMAT_VERSION_LATEST}.ento.zip"
    bad_tamper = output_dir / "bad-tamper.ento.zip"
    bad_tamper.write_bytes(good_latest.read_bytes())
    _flip_first_track_byte(bad_tamper)
    entries.append(_manifest_entry(BAD_CASES[0], bad_tamper))

    duplicate = output_dir / "bad-duplicate-member.ento.zip"
    _write_duplicate_member_container(duplicate)
    entries.append(_manifest_entry(BAD_CASES[1], duplicate))

    path_escape = output_dir / "bad-path-escape.ento.zip"
    _write_path_escape_container(path_escape)
    entries.append(_manifest_entry(BAD_CASES[2], path_escape))

    manifest_path = output_dir / "conformance_manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": "1",
            "warning": "Uses a fixed public key and fixed nonces for conformance vectors only.",
            "key_hex": CONFORMANCE_KEY.hex(),
            "cases": entries,
        },
    )
    return manifest_path


def verify_conformance_fixtures(
    fixture_dir: Path, *, report_path: Path | None = None
) -> dict[str, Any]:
    """Verify generated conformance fixtures against their expected outcomes.

    This is intentionally implementation-local: it proves the reference Python
    reader accepts every known-good vector and rejects every known-bad vector.
    The manifest format is simple enough for independent implementations to
    reuse the same cases and compare their own verify/unpack results.
    """
    manifest_path = fixture_dir / "conformance_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    key = bytes.fromhex(manifest["key_hex"])
    results: list[dict[str, Any]] = []
    for case in manifest["cases"]:
        container = fixture_dir / case["path"]
        actual, errors = _evaluate_case(container, key)
        expected = {
            "verify_with_key": bool(case["expected_verify_with_key"]),
            "verify_without_key": bool(case["expected_verify_without_key"]),
            "unpack": bool(case["expected_unpack"]),
        }
        case_ok = actual == expected
        results.append(
            {
                "case_id": case["case_id"],
                "path": case["path"],
                "category": case["category"],
                "format_version": case["format_version"],
                "expected": expected,
                "actual": actual,
                "errors": errors,
                "ok": case_ok,
            }
        )
    failed = [case["case_id"] for case in results if not case["ok"]]
    payload = {
        "ok": not failed,
        "schema_version": "1",
        "fixture_dir": str(fixture_dir),
        "case_count": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "failed_cases": failed,
        "cases": results,
    }
    if report_path is not None:
        write_json(report_path, payload)
    return payload


def _evaluate_case(
    container: Path, key: bytes
) -> tuple[dict[str, bool], dict[str, str]]:
    actual: dict[str, bool] = {}
    errors: dict[str, str] = {}
    actual["verify_with_key"], errors["verify_with_key"] = _ok_or_error(
        lambda: verify_container(container, key, require_integrity=True),
        dict_result_required=True,
    )
    actual["verify_without_key"], errors["verify_without_key"] = _ok_or_error(
        lambda: verify_container(container, None, require_integrity=True),
        dict_result_required=True,
    )
    actual["unpack"], errors["unpack"] = _ok_or_error(
        lambda: unpack_container(container, key)
    )
    return actual, {name: error for name, error in errors.items() if error}


def _ok_or_error(
    operation: Callable[[], Any], *, dict_result_required: bool = False
) -> tuple[bool, str]:
    try:
        result = operation()
    except (
        Exception
    ) as exc:  # fixture verifier must report all failures, not stop early
        return False, redact_error(exc)
    if isinstance(result, dict):
        return bool(result.get("ok")), ""
    # `unpack_container` signals success with a (payload, manifest) tuple, so a
    # non-dict result is correct there. For `verify_*` operations the contract is
    # a dict carrying `ok`; a non-dict means the verifier was refactored out of
    # contract — treat it as an oracle error, never as a silent pass, so the
    # strongest laundering-defence axes cannot go vacuous unnoticed (ENTO-XV-F2).
    if dict_result_required:
        return False, f"expected dict verifier result, got {type(result).__name__}"
    return True, ""


def _manifest_entry(case: ConformanceCase, path: Path) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "path": path.name,
        "category": case.category,
        "format_version": case.format_version,
        "sha256": crypto.sha256_hex(path.read_bytes()),
        "size_bytes": path.stat().st_size,
        "expected_verify_with_key": case.expected_verify_with_key,
        "expected_verify_without_key": case.expected_verify_without_key,
        "expected_unpack": case.expected_unpack,
        "description": case.description,
    }


def _fixed_nonce(format_version: str) -> bytes:
    size = crypto.nonce_size_for(format_version)
    return bytes(range(1, size + 1))


def _write_good_container(path: Path, format_version: str) -> None:
    track = CONFORMANCE_TRACK
    track_key = crypto.derive_track_key(CONFORMANCE_KEY, track.track_id)
    plaintext = (
        pad_payload(track.payload)
        if crypto.pads_payload(format_version)
        else track.payload
    )
    nonce, tag, ciphertext = crypto.encrypt_payload(
        track_key,
        plaintext,
        _nonce=_fixed_nonce(format_version),
        format_version=format_version,
        track_id=track.track_id,
    )
    encrypted = EncryptedTrack(
        track_id=track.track_id,
        nonce=nonce,
        tag=tag,
        ciphertext=ciphertext,
    )
    manifest = Manifest(
        format_version=format_version,
        created=CONFORMANCE_CREATED,
        creator="entofile-conformance",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(build_track_descriptor(track, encrypted.to_bytes(), observability=3),),
    )
    _write_zip(
        path,
        {
            "manifest.json": manifest_to_json(manifest).encode("utf-8"),
            f"tracks/{track.track_id}.ento": encrypted.to_bytes(),
            "proof/chain.json": json.dumps(
                export_proof(manifest).to_dict(), indent=2, sort_keys=True
            ).encode("utf-8")
            + b"\n",
        },
    )


def _write_duplicate_member_container(path: Path) -> None:
    _write_good_container(path, crypto.FORMAT_VERSION)
    with zipfile.ZipFile(path, "a", compression=zipfile.ZIP_STORED) as zf:
        info = zipfile.ZipInfo("tracks/alpha.ento", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            zf.writestr(info, b"duplicate")


def _write_path_escape_container(path: Path) -> None:
    manifest = {
        "format_version": crypto.FORMAT_VERSION,
        "created": CONFORMANCE_CREATED,
        "creator": "entofile-conformance",
        "observability_level": 3,
        "tracks": [
            {
                "id": "../escape",
                "type": "ento:spectrogram",
                "sha256_plaintext": "",
                "sha256_ciphertext": "",
                "byte_length": 1,
            }
        ],
    }
    _write_zip(
        path,
        {
            "manifest.json": json.dumps(manifest, indent=2, sort_keys=True).encode()
            + b"\n",
            "tracks/../escape.ento": b"x",
        },
    )


def _flip_first_track_byte(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as zin:
        members = {name: zin.read(name) for name in zin.namelist()}
    for name in sorted(members):
        if name.startswith("tracks/"):
            data = bytearray(members[name])
            data[-1] ^= 0xFF
            members[name] = bytes(data)
            break
    _write_zip(path, members)


def _write_zip(path: Path, members: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, data in members.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, data)


def run_live_conformance(scratch_dir: Path | None = None) -> dict[str, Any]:
    """Generate the deterministic fixture set fresh and verify it, in one call.

    The certifying counterpart to reading ``conformance_report.json``: fixtures
    are regenerated from constants (fixed key, timestamp, nonce) into a scratch
    directory and verified immediately, so a stale or forged on-disk report
    cannot certify conformance — the same side-file-trust closure already
    applied to the test summary and container gates. No side file is read or
    written; the verdict is derived entirely from work done this call.
    """
    import tempfile

    if scratch_dir is not None:
        generate_conformance_fixtures(scratch_dir)
        return verify_conformance_fixtures(scratch_dir)
    with tempfile.TemporaryDirectory(prefix="ento_conformance_live_") as tmp:
        fixture_dir = Path(tmp)
        generate_conformance_fixtures(fixture_dir)
        return verify_conformance_fixtures(fixture_dir)
