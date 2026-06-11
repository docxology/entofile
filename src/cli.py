"""ENTO CLI — inspect, pack, unpack, verify, proof, genkey."""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

import jsonschema

from . import crypto
from .container import (
    inspect_container,
    pack_container,
    unpack_container,
    verify_container,
)
from .manifest import manifest_to_json
from .fixtures import load_fixture_tracks
from .proof import export_proof
from .models import ObservabilityLevel
from .security import safe_output_path
from .telemetry import (
    append_jsonl,
    command_event,
    redact_error,
    utc_timestamp,
    write_json,
)


def _set_result(args: argparse.Namespace, **fields: Any) -> None:
    args._ento_result_fields = {k: v for k, v in fields.items() if v is not None}


def _result_fields(args: argparse.Namespace) -> dict[str, Any]:
    return dict(getattr(args, "_ento_result_fields", {}) or {})


def _write_sidecars(
    args: argparse.Namespace,
    *,
    ok: bool,
    exit_code: int,
    error: object | None = None,
) -> None:
    command = str(getattr(args, "command", "unknown"))
    fields = _result_fields(args)
    payload: dict[str, Any] = {
        "ok": ok,
        "command": command,
        "exit_code": exit_code,
        "timestamp": utc_timestamp(),
    }
    payload.update(fields)
    if error is not None:
        payload["error"] = redact_error(error)

    json_output = getattr(args, "json_output", None)
    if json_output:
        write_json(json_output, payload)
    telemetry_jsonl = getattr(args, "telemetry_jsonl", None)
    if telemetry_jsonl:
        append_jsonl(
            telemetry_jsonl,
            command_event(
                command=command,
                ok=ok,
                exit_code=exit_code,
                fields=fields,
                error=error,
            ),
        )


def _add_common_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Write a structured JSON result sidecar without changing stdout/stderr",
    )
    parser.add_argument(
        "--telemetry-jsonl",
        type=Path,
        help="Append one redacted local telemetry event as JSONL",
    )


def _load_key(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) != crypto.MASTER_KEY_SIZE:
        raise ValueError("key file must be 32 bytes")
    return data


def cmd_genkey(args: argparse.Namespace) -> int:
    key = crypto.generate_master_key()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Refuse to clobber an existing key: overwriting a live master key permanently
    # destroys the ability to decrypt/verify every container packed under it. Require
    # an explicit --force to replace one. Create exclusive + 0600 atomically (O_EXCL)
    # so there is no window where the secret exists at the default umask, and (without
    # --force) no TOCTOU between an exists() check and the write.
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | (0 if args.force else os.O_EXCL)
    try:
        fd = os.open(args.output, flags, 0o600)
    except FileExistsError:
        raise FileExistsError(
            f"refusing to overwrite existing key {str(args.output)!r}; pass --force to replace it"
        ) from None
    try:
        if args.force:
            # O_EXCL was not used, so an existing file kept its old mode — enforce 0600.
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(key)
    except OSError:
        os.close(fd)
        raise
    print(str(args.output))
    _set_result(args, output=str(args.output), key_bytes=crypto.MASTER_KEY_SIZE)
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    key = _load_key(args.key)
    fixtures = load_fixture_tracks(fixtures_path=args.fixtures, require_all=True)
    level = ObservabilityLevel(args.observability)
    manifest = pack_container(
        args.output,
        key,
        fixtures,
        creator=args.creator,
        observability_level=ObservabilityLevel.AUDITABLE,
        export_level=level,
        format_version=args.format,
    )
    print(str(args.output))
    _set_result(
        args,
        output=str(args.output),
        format_version=manifest.format_version,
        track_count=len(manifest.tracks),
        observability_level=int(level),
    )
    return 0


def cmd_unpack(args: argparse.Namespace) -> int:
    key = _load_key(args.key)
    _, payloads = unpack_container(args.input, key)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    written: list[dict[str, object]] = []
    for track_id, data in payloads.items():
        out = safe_output_path(args.output_dir, track_id)
        out.write_bytes(data)
        print(str(out))
        written.append({"track_id": track_id, "path": str(out), "bytes": len(data)})
    _set_result(
        args,
        input=str(args.input),
        output_dir=str(args.output_dir),
        track_count=len(payloads),
        written=written,
    )
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    key = _load_key(args.key) if args.key else None
    # Fail closed by default: a container whose integrity is "unverified" (no key
    # and no ciphertext digests — a stripped/forged or sealed manifest) returns
    # ok:False and exits non-zero. --allow-unverified opts back into a lenient
    # structural-only check (e.g. intentional sealed-container inspection).
    result = verify_container(
        args.input,
        key,
        require_proof=args.require_proof,
        require_integrity=not args.allow_unverified,
    )
    print(json.dumps(result, indent=2))
    _set_result(
        args,
        input=str(args.input),
        integrity=result.get("integrity"),
        track_count=result.get("track_count"),
        proof_present=result.get("proof_present"),
        plaintext_verified=result.get("plaintext_verified"),
        ciphertext_digests_present=result.get("ciphertext_digests_present"),
        observability_level=result.get("observability_level"),
    )
    if not result.get("ok"):
        audit = {
            "event": "verify_failed",
            "container": str(args.input),
            "ok": result.get("ok"),
            "integrity": result.get("integrity"),
            "track_count": result.get("track_count"),
        }
        print(json.dumps(audit), file=sys.stderr)
        return 1
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    manifest = inspect_container(args.input)
    print(manifest_to_json(manifest))
    _set_result(
        args,
        input=str(args.input),
        format_version=manifest.format_version,
        observability_level=int(manifest.observability_level),
        track_count=len(manifest.tracks),
    )
    return 0


def cmd_proof(args: argparse.Namespace) -> int:
    manifest = inspect_container(args.input)
    proof = export_proof(manifest)
    text = json.dumps(proof.to_dict(), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(str(args.output))
        output = str(args.output)
    else:
        print(text, end="")
        output = None
    _set_result(args, input=str(args.input), output=output, link_count=len(proof.links))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.cli", description="ENTO format 0.4.0 container tool"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    genkey = sub.add_parser("genkey", help="Write a 32-byte master key")
    _add_common_output_args(genkey)
    genkey.add_argument("-o", "--output", type=Path, required=True)
    genkey.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing key file (destroys access to containers under the old key)",
    )
    genkey.set_defaults(func=cmd_genkey)

    pack = sub.add_parser("pack", help="Pack fixture tracks into an ENTO container")
    _add_common_output_args(pack)
    pack.add_argument("-k", "--key", type=Path, required=True)
    pack.add_argument("-o", "--output", type=Path, required=True)
    pack.add_argument(
        "--fixtures",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "fixtures",
    )
    pack.add_argument("--creator", default="entofile")
    pack.add_argument("--observability", type=int, default=3, choices=[0, 1, 2, 3])
    pack.add_argument(
        "--format",
        default=crypto.FORMAT_VERSION,
        choices=list(crypto.SUPPORTED_FORMAT_VERSIONS),
        help=(
            "ENTO format version: 0.4.0 (default: 12-byte nonce + AAD + PADME length padding), "
            "or compatibility formats 0.2.0, 0.3.0, 0.3.1"
        ),
    )
    pack.set_defaults(func=cmd_pack)

    unpack = sub.add_parser("unpack", help="Decrypt tracks from an ENTO container")
    _add_common_output_args(unpack)
    unpack.add_argument("-k", "--key", type=Path, required=True)
    unpack.add_argument("-i", "--input", type=Path, required=True)
    unpack.add_argument("-o", "--output-dir", type=Path, required=True)
    unpack.set_defaults(func=cmd_unpack)

    verify = sub.add_parser(
        "verify", help="Verify container integrity (optional decrypt with key)"
    )
    _add_common_output_args(verify)
    verify.add_argument("-i", "--input", type=Path, required=True)
    verify.add_argument(
        "-k", "--key", type=Path, help="Optional master key to verify plaintext digests"
    )
    verify.add_argument(
        "--require-proof",
        action="store_true",
        help="Fail when proof/chain.json is absent",
    )
    verify.add_argument(
        "--allow-unverified",
        action="store_true",
        help="Permit a structurally-valid container whose integrity is 'unverified' "
        "(no key and no ciphertext digests); off by default so verify fails closed",
    )
    verify.set_defaults(func=cmd_verify)

    inspect_cmd = sub.add_parser("inspect", help="Print manifest JSON")
    _add_common_output_args(inspect_cmd)
    inspect_cmd.add_argument("-i", "--input", type=Path, required=True)
    inspect_cmd.set_defaults(func=cmd_inspect)

    proof = sub.add_parser("proof", help="Export proof chain JSON")
    _add_common_output_args(proof)
    proof.add_argument("-i", "--input", type=Path, required=True)
    proof.add_argument("-o", "--output", type=Path)
    proof.set_defaults(func=cmd_proof)

    types_cmd = sub.add_parser("types", help="List registered track types")
    _add_common_output_args(types_cmd)
    types_cmd.set_defaults(func=_cmd_types)

    return parser


def _cmd_types(_args: argparse.Namespace) -> int:
    from .ontology import registered_types

    uris = registered_types()
    for uri in uris:
        print(uri)
    _set_result(_args, type_count=len(uris), types=list(uris))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = int(args.func(args))
        _write_sidecars(args, ok=code == 0, exit_code=code)
        return code
    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        OSError,
        zipfile.BadZipFile,
        jsonschema.ValidationError,
    ) as exc:
        # zipfile.BadZipFile is an Exception but NOT an OSError, so a non-zip / corrupt
        # archive passed to verify/inspect/unpack/proof would otherwise escape as an
        # uncaught traceback. Catch it here so adversarial input yields a clean
        # "error: ..." + exit 1, consistent with every other malformed-input path.
        print(f"error: {exc}", file=sys.stderr)
        _write_sidecars(args, ok=False, exit_code=1, error=exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
