"""Public-promotion metadata consistency tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from src import crypto
from src.public_promotion import check_public_promotion_metadata

# SHA-256 over the regex matches in the two self-referential scanner files
# (src/public_promotion.py + this file). Pins their absolute-path snippet
# content so a real leak hiding inside an allowlisted file is caught
# (test_machine_path_scan_self_allowlist_is_minimal_and_complete). Recompute and
# update ONLY after reviewing the diff that changed it.
_SCANNER_SELF_MATCH_SIGNATURE = (
    "ef026cb671301a888a15723c42b460337f0d436701e92a054404c3d34ac1aa63"
)


def _write_public_promotion_surfaces(
    root: Path, *, stale_security: bool = False
) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "output" / "data").mkdir(parents=True, exist_ok=True)
    security_scope = (
        "The 0.4 paper release candidate documents ENTO format `0.2.0` as the default "
        "write format.\n"
        if stale_security
        else (
            "The 0.4 paper release candidate documents ENTO format `0.4.0` as the "
            "default wire format. Formats `0.2.0`, `0.3.0`, and `0.3.1` remain "
            "compatibility formats.\n"
        )
    )
    (root / "SECURITY.md").write_text(security_scope, encoding="utf-8")
    (root / "docs" / "operator_checklist.md").write_text(
        "Pack with the current default wire format `0.4.0`; use `0.2.0` only for legacy compatibility.\n",
        encoding="utf-8",
    )
    (root / "docs" / "entofile-threat-model.md").write_text(
        "Default writes use `0.4.0`; `0.2.0`, `0.3.0`, and `0.3.1` are compatibility formats.\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_format_0_3_0.py").write_text(
        '"""0.4.0 is the current default write format; 0.2.0 is compatibility."""\n',
        encoding="utf-8",
    )
    for rel in ("docs/security.md", "docs/architecture.md", "docs/format_migration.md"):
        (root / rel).write_text(
            "Default ENTO wire format `0.4.0`; compatibility `0.2.0`, `0.3.0`, `0.3.1`.\n",
            encoding="utf-8",
        )
    (root / "ISA.md").write_text(
        "Historical note: current release guidance uses default wire format `0.4.0`.\n",
        encoding="utf-8",
    )
    (root / "CONTRIBUTING.md").write_text(
        "Default writes use format `0.4.0`; prior formats remain compatibility formats.\n",
        encoding="utf-8",
    )
    (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").write_text(
        'options:\n  - "0.4.0"\n  - "0.2.0"\n',
        encoding="utf-8",
    )
    (root / "output" / "data" / "transmission_manifest.json").write_text(
        json.dumps({"published": False, "pdf_sha256": None}),
        encoding="utf-8",
    )


def _write_complete_public_promotion_fixture(root: Path) -> None:
    (root / "manuscript").mkdir(parents=True, exist_ok=True)
    (root / "output" / "release").mkdir(parents=True, exist_ok=True)
    _write_public_promotion_surfaces(root)
    (root / "manuscript" / "config.yaml").write_text(
        """
paper:
  title: "ENTO title"
  version: "0.4"
authors:
  - name: "Daniel Ari Friedman"
    email: "daniel@activeinference.institute"
publication:
  doi: "10.5281/zenodo.20396329"
""".lstrip(),
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        """
[project]
name = "entofile"
authors = [{ name = "Daniel Ari Friedman", email = "daniel@activeinference.institute" }]
license = { file = "LICENSE" }
""".lstrip(),
        encoding="utf-8",
    )
    (root / "CITATION.cff").write_text(
        'title: "ENTO title"\nversion: "0.4"\ndoi: "10.5281/zenodo.20396329"\nrepository-code: "https://github.com/docxology/entofile"\n',
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "Planned public home: https://github.com/docxology/entofile; projects/working/entofile. Default `0.4.0`.\n",
        encoding="utf-8",
    )
    (root / "output" / "release" / "release_manifest.json").write_text(
        json.dumps(
            {
                "ok": True,
                "planned_public_home": "https://github.com/docxology/entofile",
                "release_label": "0.4",
                "doi": "10.5281/zenodo.20396329",
                "wire_format_default": crypto.FORMAT_VERSION,
                "supported_wire_formats": list(crypto.SUPPORTED_FORMAT_VERSIONS),
                "source_dirty_project": False,
                "source_dirty_repository": False,
            }
        ),
        encoding="utf-8",
    )


def _successful_endpoint_state() -> dict[str, object]:
    return {
        "checked": True,
        "ok": True,
        "github": {
            "url": "https://github.com/docxology/entofile",
            "ok": True,
            "status": 200,
        },
        "zenodo": {
            "url": "https://zenodo.org/records/20396329",
            "ok": True,
            "status": 200,
        },
        "doi": {
            "url": "https://doi.org/10.5281/zenodo.20396329",
            "ok": True,
            "status": 302,
        },
    }


def test_public_promotion_metadata_current_tree() -> None:
    root = Path(__file__).resolve().parent.parent
    report = check_public_promotion_metadata(root)
    assert report["ok"] is True
    assert report["failures"] == []
    assert report["release_ready"] is False
    assert report["release_label"] == "0.4"
    assert report["checks"]["release_manifest_default_format"] is True
    assert report["checks"]["security_policy_current_default_format"] is True
    assert report["checks"]["transmission_hash_current_or_pending"] is True
    # Publication readiness: no maintainer home-directory path may leak into the
    # hand-authored docs of a repo about to be cloned to an arbitrary location.
    assert report["checks"]["public_docs_no_machine_paths"] is True
    assert report["machine_path_hits"] == {}
    assert "public_endpoint_state" in report["release_blockers"]


def test_public_promotion_metadata_reports_mismatch(tmp_path: Path) -> None:
    (tmp_path / "manuscript").mkdir(parents=True)
    (tmp_path / "output" / "release").mkdir(parents=True)
    _write_public_promotion_surfaces(tmp_path)
    (tmp_path / "manuscript" / "config.yaml").write_text(
        """
paper:
  title: "ENTO title"
  version: "0.4"
authors:
  - name: "Daniel Ari Friedman"
    email: "daniel@activeinference.institute"
publication:
  doi: "10.5281/zenodo.20396329"
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "entofile"
authors = [{ name = "Wrong", email = "wrong@example.invalid" }]
license = { file = "LICENSE" }
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "CITATION.cff").write_text(
        'title: "ENTO title"\nversion: "0.4"\ndoi: "bad"\nrepository-code: "https://github.com/docxology/entofile"\n',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "Planned public home: https://github.com/docxology/entofile; projects/working/entofile\n",
        encoding="utf-8",
    )
    (tmp_path / "output" / "release" / "release_manifest.json").write_text(
        json.dumps(
            {
                "ok": True,
                "planned_public_home": "https://github.com/docxology/entofile",
                "release_label": "0.4",
                "doi": "10.5281/zenodo.20396329",
                "wire_format_default": crypto.FORMAT_VERSION,
                "supported_wire_formats": list(crypto.SUPPORTED_FORMAT_VERSIONS),
                "source_dirty_project": False,
                "source_dirty_repository": False,
            }
        ),
        encoding="utf-8",
    )
    report = check_public_promotion_metadata(tmp_path)
    assert report["ok"] is False
    assert "cff_doi" in report["failures"]
    assert "pyproject_author" in report["failures"]
    assert "security_policy_current_default_format" not in report["failures"]


def test_public_promotion_metadata_release_ready_when_endpoints_are_live(
    tmp_path: Path,
) -> None:
    _write_complete_public_promotion_fixture(tmp_path)

    report = check_public_promotion_metadata(
        tmp_path, public_endpoint_state=_successful_endpoint_state()
    )

    assert report["ok"] is True
    assert report["release_ready"] is True
    assert report["release_blockers"] == []
    assert report["public_endpoint_state"]["checked"] is True


def test_public_promotion_metadata_reports_stale_security_default(
    tmp_path: Path,
) -> None:
    (tmp_path / "manuscript").mkdir(parents=True)
    (tmp_path / "output" / "release").mkdir(parents=True)
    _write_public_promotion_surfaces(tmp_path, stale_security=True)
    (tmp_path / "manuscript" / "config.yaml").write_text(
        """
paper:
  title: "ENTO title"
  version: "0.4"
authors:
  - name: "Daniel Ari Friedman"
    email: "daniel@activeinference.institute"
publication:
  doi: "10.5281/zenodo.20396329"
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "entofile"
authors = [{ name = "Daniel Ari Friedman", email = "daniel@activeinference.institute" }]
license = { file = "LICENSE" }
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "CITATION.cff").write_text(
        'title: "ENTO title"\nversion: "0.4"\ndoi: "10.5281/zenodo.20396329"\nrepository-code: "https://github.com/docxology/entofile"\n',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "Planned public home: https://github.com/docxology/entofile; projects/working/entofile. Default `0.4.0`.\n",
        encoding="utf-8",
    )
    (tmp_path / "output" / "release" / "release_manifest.json").write_text(
        json.dumps(
            {
                "ok": True,
                "planned_public_home": "https://github.com/docxology/entofile",
                "release_label": "0.4",
                "doi": "10.5281/zenodo.20396329",
                "wire_format_default": crypto.FORMAT_VERSION,
                "supported_wire_formats": list(crypto.SUPPORTED_FORMAT_VERSIONS),
                "source_dirty_project": False,
                "source_dirty_repository": False,
            }
        ),
        encoding="utf-8",
    )
    report = check_public_promotion_metadata(tmp_path)
    assert report["ok"] is False
    assert "security_policy_current_default_format" in report["failures"]
    assert "public_docs_current_default_format" in report["failures"]
    assert report["stale_default_format_phrases"] == {
        "SECURITY.md": ["`0.2.0` as the default"]
    }


def test_public_promotion_metadata_reports_stale_contributing_default(
    tmp_path: Path,
) -> None:
    _write_complete_public_promotion_fixture(tmp_path)
    (tmp_path / "CONTRIBUTING.md").write_text(
        "Default writes remain format `0.2.0`.\n",
        encoding="utf-8",
    )

    report = check_public_promotion_metadata(tmp_path)

    assert report["ok"] is False
    assert "public_docs_current_default_format" in report["failures"]
    assert report["stale_default_format_phrases"] == {
        "CONTRIBUTING.md": ["default writes remain format `0.2.0`"]
    }


def test_public_promotion_metadata_reports_stale_draft_pdf_hash(tmp_path: Path) -> None:
    (tmp_path / "manuscript").mkdir(parents=True)
    (tmp_path / "output" / "release").mkdir(parents=True)
    (tmp_path / "output" / "data").mkdir(parents=True)
    _write_public_promotion_surfaces(tmp_path)
    (tmp_path / "output" / "data" / "transmission_manifest.json").write_text(
        json.dumps({"published": False, "pdf_sha256": "a" * 64}),
        encoding="utf-8",
    )
    report = check_public_promotion_metadata(tmp_path)
    assert report["checks"]["transmission_hash_current_or_pending"] is False


def test_public_promotion_script_check() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "check_public_promotion_metadata.py"),
            "--check",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["ok"] is True


def test_public_promotion_script_release_mode_blocks_unpublished_endpoints() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "check_public_promotion_metadata.py"),
            "--check",
            "--require-public-endpoints",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert result.returncode == 1
    assert report["ok"] is True
    assert report["release_ready"] is False
    assert "public_endpoint_state" in report["release_blockers"]


def test_public_promotion_metadata_flags_machine_path_leak(tmp_path: Path) -> None:
    """Negative control (2026-06-10): a maintainer home-directory path baked into
    a public-facing doc must fail the gate. Before this scan existed, 16 such
    maintainer home paths (`/Users/<name>/...`) passed `ok:True` and would have
    shipped to the public clone — leaking filesystem layout and giving readers
    unrunnable commands."""
    _write_complete_public_promotion_fixture(tmp_path)
    # Clean fixture passes the new check.
    clean = check_public_promotion_metadata(tmp_path)
    assert clean["checks"]["public_docs_no_machine_paths"] is True
    assert clean["machine_path_hits"] == {}

    # Inject a machine path into an authored doc surface; the gate must catch it.
    (tmp_path / "docs" / "quickstart.md").write_text(
        "Render from `/Users/maintainer/Documents/GitHub/template`:\n"
        "```bash\ncd /Users/maintainer/Documents/GitHub/template\n```\n",
        encoding="utf-8",
    )
    leaked = check_public_promotion_metadata(tmp_path)
    assert leaked["ok"] is False
    assert "public_docs_no_machine_paths" in leaked["failures"]
    assert "docs/quickstart.md" in leaked["machine_path_hits"]
    assert leaked["machine_path_hits"]["docs/quickstart.md"] == ["/Users/maintainer"]


def test_machine_path_scan_covers_nonmd_and_nested_surfaces(tmp_path: Path) -> None:
    """Cross-vendor regression (ENTO-XV-F1, 2026-06-10): the R16 scanner globbed
    only `*.md`/`docs/*.md`/`manuscript/*.md`, so a `/Users/<name>/...` path in
    CITATION.cff, pyproject.toml, configs/*.yaml, .github/*.yml, scripts/*.py, or
    depth-2 docs/research/*.md passed the gate as clean. The scan is now driven
    off the full tracked surface; pin coverage of the previously-blind kinds."""
    _write_complete_public_promotion_fixture(tmp_path)
    assert check_public_promotion_metadata(tmp_path)["machine_path_hits"] == {}

    # Non-`.md` metadata surface (Forge's reproduced leak) + a depth-2 doc that
    # `docs/*.md` could never reach.
    cff = tmp_path / "CITATION.cff"
    cff.write_text(
        cff.read_text(encoding="utf-8") + "note: /Users/leak/secret/key\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "research" / "related_formats.md").write_text(
        "See `/Users/leak/Documents/GitHub/template` for the render tree.\n",
        encoding="utf-8",
    )

    report = check_public_promotion_metadata(tmp_path)
    assert report["ok"] is False
    assert "public_docs_no_machine_paths" in report["failures"]
    hits = report["machine_path_hits"]
    assert "CITATION.cff" in hits
    assert "docs/research/related_formats.md" in hits
    assert hits["CITATION.cff"] == ["/Users/leak"]


def test_machine_path_scan_catches_path_in_binary_file(tmp_path: Path) -> None:
    """ENTO-XV-F1 RESIDUAL-2 (cross-vendor re-verify): a maintainer path carried
    as literal ASCII inside a mostly-binary tracked file was swallowed by the
    utf-8 decode skip. The scan now falls back to latin-1, so the path is still
    caught; a genuinely path-free binary must stay clean."""
    _write_complete_public_promotion_fixture(tmp_path)
    (tmp_path / "docs" / "research").mkdir(parents=True, exist_ok=True)

    # Embedded ASCII path + invalid-UTF-8 bytes (would raise UnicodeDecodeError).
    (tmp_path / "docs" / "research" / "blob.bin").write_bytes(
        b"\x89PNG\x00/Users/binsecret/layout\xff\xfe\x00binary"
    )
    report = check_public_promotion_metadata(tmp_path)
    assert report["ok"] is False
    assert "docs/research/blob.bin" in report["machine_path_hits"]
    assert report["machine_path_hits"]["docs/research/blob.bin"] == ["/Users/binsecret"]

    # A path-free binary must not produce a false positive.
    (tmp_path / "docs" / "research" / "blob.bin").write_bytes(
        b"\x89PNG\x00\xff\xfe\x00 no paths here \x01\x02"
    )
    assert check_public_promotion_metadata(tmp_path)["machine_path_hits"] == {}


def test_machine_path_scan_self_allowlist_is_minimal_and_complete() -> None:
    """Anti-laundering control: the scanner excludes exactly the two files that
    DEFINE and TEST it (they necessarily contain the detection pattern). Prove
    that exclusion hides no real leak — those two are the ONLY tracked files in
    the live tree that match the pattern, and the live gate is clean."""
    from src.public_promotion import _MACHINE_PATH_RE, _SCANNER_SELF_REFERENTIAL

    assert {
        "src/public_promotion.py",
        "tests/test_public_promotion.py",
    } == _SCANNER_SELF_REFERENTIAL

    root = Path(__file__).resolve().parent.parent
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    assert tracked, "git ls-files returned nothing — test must run inside the repo"

    matching = set()
    for rel in tracked:
        if rel.startswith("output/"):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _MACHINE_PATH_RE.search(text):
            matching.add(rel)

    # The only tracked files containing the pattern are the scanner's own
    # definition + test; excluding them therefore hides no real leak.
    assert matching == set(_SCANNER_SELF_REFERENTIAL)

    # ENTO-XV-F1 RESIDUAL-1 (cross-vendor re-verify): a filename-only allowlist
    # would let a REAL leak hide inside an allowlisted scanner file (its hits are
    # never reported). Pin a SIGNATURE of the exact snippets the regex matches in
    # those files (its pattern source + documented examples/fixtures). Any new
    # match — e.g. a planted concrete maintainer home path — changes the
    # signature and fails here, forcing review. A hex digest carries no path
    # literal, so pinning it does not itself perturb the matched set (which a
    # literal allowlist would).
    sig = hashlib.sha256()
    for rel in sorted(_SCANNER_SELF_REFERENTIAL):
        found = sorted(set(_MACHINE_PATH_RE.findall((root / rel).read_text("utf-8"))))
        sig.update(rel.encode())
        sig.update(repr(found).encode())
    assert sig.hexdigest() == _SCANNER_SELF_MATCH_SIGNATURE, (
        "absolute-path snippets in an allowlisted scanner file changed — a real "
        "leak may be hiding there; review the diff and update the signature only "
        "if the new match is a legitimate pattern/example."
    )
    assert check_public_promotion_metadata(root)["machine_path_hits"] == {}


def test_stale_phrase_scan_covers_review_ledger_and_spec_pointer() -> None:
    """Regression (2026-06-10): REVIEW.md and entofile.md carried stale
    0.2.0-default wording that the scan missed — both files were unscanned AND
    the exact sentences matched no phrase. Pin both closures: the surfaces are
    scanned, and the historical sentences now fire."""

    from src.public_promotion import (
        PUBLIC_DEFAULT_FORMAT_SURFACES,
        _stale_default_phrase_hits,
    )

    assert "REVIEW.md" in PUBLIC_DEFAULT_FORMAT_SURFACES
    assert "entofile.md" in PUBLIC_DEFAULT_FORMAT_SURFACES

    historical = {
        "REVIEW.md": (
            "**Default format version:** 0.2.0 (AES-256-GCM)\n"
            "It does not introduce an ENTO `format_version` 0.4 and does not "
            "change the default write format."
        ),
        "entofile.md": "The normative ENTO format **0.2.0** specification lives in README.",
    }
    hits = _stale_default_phrase_hits(historical)
    assert "REVIEW.md" in hits
    assert "entofile.md" in hits

    # The FIXED current files must be clean (no false positives).
    root = Path(__file__).resolve().parent.parent
    current = {
        name: (root / name).read_text(encoding="utf-8")
        for name in ("REVIEW.md", "entofile.md")
    }
    assert _stale_default_phrase_hits(current) == {}
