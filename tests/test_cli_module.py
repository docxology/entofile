"""Direct CLI module tests for coverage."""

from __future__ import annotations

from pathlib import Path


from src.cli import build_parser, cmd_genkey, cmd_inspect, main


def test_build_parser_has_subcommands() -> None:
    parser = build_parser()
    assert "genkey" in parser.format_help()


def test_cmd_genkey(tmp_path: Path) -> None:
    out = tmp_path / "key.bin"
    args = build_parser().parse_args(["genkey", "-o", str(out)])
    assert cmd_genkey(args) == 0
    assert len(out.read_bytes()) == 32


def test_cmd_inspect_after_pack(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    key = tmp_path / "key.bin"
    container = tmp_path / "c.zip"
    out_dir = tmp_path / "out"
    gen_args = build_parser().parse_args(["genkey", "-o", str(key)])
    cmd_genkey(gen_args)
    pack_args = build_parser().parse_args(
        [
            "pack",
            "-k",
            str(key),
            "-o",
            str(container),
            "--fixtures",
            str(root / "data" / "fixtures"),
        ]
    )
    from src.cli import cmd_pack, cmd_proof, cmd_unpack, _cmd_types

    assert cmd_pack(pack_args) == 0
    inspect_args = build_parser().parse_args(["inspect", "-i", str(container)])
    assert cmd_inspect(inspect_args) == 0
    proof_path = tmp_path / "proof.json"
    proof_args = build_parser().parse_args(
        ["proof", "-i", str(container), "-o", str(proof_path)]
    )

    assert cmd_proof(proof_args) == 0
    unpack_args = build_parser().parse_args(
        ["unpack", "-k", str(key), "-i", str(container), "-o", str(out_dir)]
    )
    assert cmd_unpack(unpack_args) == 0
    assert _cmd_types(build_parser().parse_args(["types"])) == 0


def test_main_invalid_key(tmp_path: Path) -> None:
    bad_key = tmp_path / "bad.key"
    bad_key.write_bytes(b"short")
    code = main(["pack", "-k", str(bad_key), "-o", str(tmp_path / "x.zip")])
    assert code == 1


def test_genkey_refuses_to_clobber_existing_key(tmp_path: Path) -> None:
    """genkey must not silently overwrite a live master key (data-loss footgun)."""
    out = tmp_path / "master.key"
    assert main(["genkey", "-o", str(out)]) == 0
    first = out.read_bytes()
    # Second genkey without --force must fail and leave the key untouched.
    assert main(["genkey", "-o", str(out)]) == 1
    assert out.read_bytes() == first


def test_genkey_force_replaces_and_keeps_0600(tmp_path: Path) -> None:
    import os
    import stat

    out = tmp_path / "master.key"
    assert main(["genkey", "-o", str(out)]) == 0
    first = out.read_bytes()
    assert main(["genkey", "-o", str(out), "--force"]) == 0
    assert out.read_bytes() != first
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(out).st_mode) == 0o600


def test_genkey_sets_0600_on_create(tmp_path: Path) -> None:
    import os
    import stat

    out = tmp_path / "master.key"
    assert main(["genkey", "-o", str(out)]) == 0
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(out).st_mode) == 0o600


def test_verify_non_zip_exits_cleanly(tmp_path: Path) -> None:
    """A non-zip / corrupt archive must yield a clean error + exit 1, not a
    BadZipFile traceback escaping the CLI boundary."""
    bad = tmp_path / "notazip.ento.zip"
    bad.write_bytes(b"this is not a zip file")
    assert main(["verify", "-i", str(bad)]) == 1


def test_inspect_non_zip_exits_cleanly(tmp_path: Path) -> None:
    bad = tmp_path / "notazip.ento.zip"
    bad.write_bytes(b"\x00\x01\x02 not a zip")
    assert main(["inspect", "-i", str(bad)]) == 1
