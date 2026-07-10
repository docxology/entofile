"""Machine-readable metadata checks for eventual public promotion."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

from . import crypto

PLANNED_PUBLIC_HOME = "https://github.com/docxology/entofile"
PRIVATE_WORKING_HOME = "projects/working/entofile"
PLANNED_ZENODO_RECORD = "https://zenodo.org/records/20396329"
PLANNED_DOI_URL = "https://doi.org/10.5281/zenodo.20396329"
PUBLIC_ENDPOINTS = {
    "github": PLANNED_PUBLIC_HOME,
    "zenodo": PLANNED_ZENODO_RECORD,
    "doi": PLANNED_DOI_URL,
}
PUBLIC_ENDPOINT_USER_AGENT = "entofile-release-check/0.4"
CORE_CURRENT_DEFAULT_DOCS = (
    "SECURITY.md",
    "docs/operator_checklist.md",
    "docs/entofile-threat-model.md",
    "tests/test_format_0_3_0.py",
)
PUBLIC_DEFAULT_FORMAT_SURFACES = (*CORE_CURRENT_DEFAULT_DOCS,
    "README.md",
    "CONTRIBUTING.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    "docs/security.md",
    "docs/architecture.md",
    "docs/format_migration.md",
    "ISA.md",
    # 2026-06-10: both carried stale 0.2.0-default wording that this checker
    # missed because they were not scanned — scan every root-level doc that
    # states the default format.
    "REVIEW.md",
    "entofile.md",
)
STALE_DEFAULT_FORMAT_PHRASES = (
    "`0.2.0` as the default",
    "0.2.0 as the default",
    "default writes remain format `0.2.0`",
    "default writes remain format 0.2.0",
    "default writes remain `0.2.0`",
    "0.2.0 stays default",
    "0.2.0 stays the default",
    "0.2.0 still default",
    "format stays 0.2.0",
    "default published wire format",
    # Variants that slipped past the list above (found stale in REVIEW.md and
    # entofile.md on 2026-06-10; both sides are normalised before matching):
    "default format version:** 0.2.0",
    "default format version: 0.2.0",
    "format **0.2.0** specification",
    "does not change the default write format",
)

# Public-release leak scan. A clone of github.com/docxology/entofile sits at an
# arbitrary location, so any maintainer absolute home path baked into a tracked
# file both leaks the maintainer's filesystem layout AND gives public readers
# broken, unrunnable commands. The scan is driven off the ACTUAL tracked set
# (`git ls-files`) rather than a hand-maintained glob list: the R16 scanner
# shipped globbing only `*.md`/`docs/*.md`/`manuscript/*.md` and was blind to
# CITATION.cff, pyproject.toml, configs/*.yaml, .github/*.yml, scripts/*.py, and
# depth-2 docs/research/*.md (cross-vendor audit ENTO-XV-F1, 2026-06-10). A glob
# list drifts as files are added; the tracked set cannot.
_LEAK_SCAN_EXCLUDED_TOP = "output/"
# Non-shipping directories skipped in the non-git fallback walk (test fixtures).
_LEAK_SCAN_SKIP_PARTS = frozenset(
    {
        ".git",
        ".venv",
        "output",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "htmlcov",
        ".benchmarks",
        "node_modules",
    }
)
# The two files that DEFINE and TEST this scanner necessarily contain the
# detection pattern and example fixtures, so they always match it. A test
# asserts they are the ONLY tracked files that match, so excluding them here
# prevents the scanner from flagging its own source without hiding any leak.
_SCANNER_SELF_REFERENTIAL = frozenset(
    {"src/public_promotion.py", "tests/test_public_promotion.py"}
)
# Identity-leaking ABSOLUTE home paths: `/Users/<name>`, `/home/<name>/`, or a
# Windows user profile (`C:\Users\`; `C:/Users/` is caught by the `/Users/`
# arm). Portable references (`~/...`, `$HOME/...`) are deliberately NOT flagged:
# they expand per-user and leak no specific layout, and flagging them would
# false-positive on legitimate `~/.config`-style documentation.
_MACHINE_PATH_RE = re.compile(
    r"(?:/Users/[^/\s`\"']+|/home/[^/\s`\"']+/|[A-Za-z]:\\Users\\)"
)


def check_public_promotion_metadata(
    project_root: Path, *, public_endpoint_state: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Compare public-facing metadata surfaces before repository promotion."""
    root = project_root.resolve()
    config = _read_yaml(root / "manuscript" / "config.yaml")
    pyproject = _read_toml(root / "pyproject.toml")
    cff = _read_yaml(root / "CITATION.cff")
    readme = _read_text(root / "README.md")
    release = _read_json(root / "output" / "release" / "release_manifest.json")
    transmission = _read_json(root / "output" / "data" / "transmission_manifest.json")
    public_docs = {
        path: _read_text(root / path) for path in PUBLIC_DEFAULT_FORMAT_SURFACES
    }
    stale_default_phrases = _stale_default_phrase_hits(public_docs)
    machine_path_hits = _machine_path_hits(root)
    project_dirty = bool(_git_text(root, "status", "--porcelain", "--", "."))
    repository_dirty = bool(_git_text(root, "status", "--porcelain"))

    paper = config.get("paper", {}) if isinstance(config.get("paper"), dict) else {}
    publication = (
        config.get("publication", {})
        if isinstance(config.get("publication"), dict)
        else {}
    )
    authors = (
        config.get("authors", []) if isinstance(config.get("authors"), list) else []
    )
    author0 = authors[0] if authors and isinstance(authors[0], dict) else {}
    project = (
        pyproject.get("project", {})
        if isinstance(pyproject.get("project"), dict)
        else {}
    )
    project_authors = project.get("authors", [])
    project_author0 = (
        project_authors[0]
        if project_authors and isinstance(project_authors[0], dict)
        else {}
    )

    checks = {
        # Post-publication (2026-06-11): the README now states the live public
        # home + development source rather than a "Planned" future home. Require
        # the public-home URL and the development-source path to both be present.
        "readme_public_home": (
            PLANNED_PUBLIC_HOME in readme and PRIVATE_WORKING_HOME in readme
        ),
        "cff_repository_code": cff.get("repository-code") == PLANNED_PUBLIC_HOME,
        "cff_release_label": str(cff.get("version")) == str(paper.get("version")),
        "cff_title": str(cff.get("title")) == str(paper.get("title")),
        "cff_doi": str(cff.get("doi")) == str(publication.get("doi")),
        "pyproject_author": project_author0.get("name") == author0.get("name")
        and project_author0.get("email") == author0.get("email"),
        "pyproject_license_file": project.get("license") == {"file": "LICENSE"},
        "release_manifest_present": bool(release),
        "release_manifest_ok": release.get("ok") is True,
        "release_manifest_home": release.get("planned_public_home")
        == PLANNED_PUBLIC_HOME,
        "release_manifest_label": str(release.get("release_label"))
        == str(paper.get("version")),
        "release_manifest_doi": str(release.get("doi")) == str(publication.get("doi")),
        "release_manifest_default_format": release.get("wire_format_default")
        == crypto.FORMAT_VERSION,
        "release_manifest_supported_formats": release.get("supported_wire_formats")
        == list(crypto.SUPPORTED_FORMAT_VERSIONS),
        "release_manifest_project_dirty_field_present": isinstance(
            release.get("source_dirty_project"), bool
        ),
        "release_manifest_repository_dirty_field_present": isinstance(
            release.get("source_dirty_repository"), bool
        ),
        "security_policy_current_default_format": _security_policy_current_default(
            public_docs["SECURITY.md"]
        ),
        "public_docs_current_default_format": (
            not stale_default_phrases
            and all(
                crypto.FORMAT_VERSION in public_docs[path]
                for path in CORE_CURRENT_DEFAULT_DOCS
            )
        ),
        "transmission_hash_current_or_pending": _transmission_hash_current_or_pending(
            root, transmission
        ),
        "public_docs_no_machine_paths": not machine_path_hits,
    }
    failures = [name for name, ok in checks.items() if not ok]
    endpoint_state = public_endpoint_state or _unchecked_public_endpoint_state()
    release_readiness_checks = {
        "project_source_clean": not project_dirty,
        "release_manifest_project_source_clean": release.get("source_dirty_project")
        is False,
        "public_endpoint_state": _public_endpoint_state_ok(endpoint_state),
    }
    release_blockers = [name for name, ok in release_readiness_checks.items() if not ok]
    return {
        "ok": not failures,
        "release_ready": not failures and not release_blockers,
        "planned_public_home": PLANNED_PUBLIC_HOME,
        "private_working_home": PRIVATE_WORKING_HOME,
        "release_label": str(paper.get("version", "")),
        "doi": str(publication.get("doi", "")),
        "checks": checks,
        "failures": failures,
        "release_readiness_checks": release_readiness_checks,
        "release_blockers": release_blockers,
        "source_state": {
            "project_dirty": project_dirty,
            "repository_dirty": repository_dirty,
            "release_manifest_source_dirty_project": release.get(
                "source_dirty_project"
            ),
            "release_manifest_source_dirty_repository": release.get(
                "source_dirty_repository"
            ),
        },
        "stale_default_format_phrases": stale_default_phrases,
        "machine_path_hits": machine_path_hits,
        "public_endpoint_state": endpoint_state,
    }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _normalise_text(text: str) -> str:
    return " ".join(text.lower().split())


def _stale_default_phrase_hits(texts: dict[str, str]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for path, text in texts.items():
        normalised = _normalise_text(text)
        found = [
            phrase
            for phrase in STALE_DEFAULT_FORMAT_PHRASES
            if _normalise_text(phrase) in normalised
        ]
        if found:
            hits[path] = found
    return hits


def _scan_candidate_files(root: Path) -> list[str]:
    """POSIX-relative tracked text files to scan for leaked absolute paths.

    Uses ``git ls-files`` (authoritative for what actually ships) when ``root``
    is a git work tree; falls back to a filesystem walk for non-git contexts
    such as temporary test fixtures. ``output/``, the scanner's own
    self-referential files, and common non-shipping directories are excluded;
    binary files are skipped at read time by the caller.
    """
    tracked = _git_text(root, "ls-files")
    if tracked:
        rels = [line for line in tracked.splitlines() if line]
    else:
        rels = [
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file()
            and not (set(p.relative_to(root).parts) & _LEAK_SCAN_SKIP_PARTS)
        ]
    return [
        rel
        for rel in rels
        if not rel.startswith(_LEAK_SCAN_EXCLUDED_TOP)
        and rel not in _SCANNER_SELF_REFERENTIAL
    ]


def _machine_path_hits(root: Path) -> dict[str, list[str]]:
    """Flag tracked files that leak a maintainer absolute home path.

    Returns a mapping of POSIX-relative path -> sorted unique matched snippets.
    Empty mapping means no machine-specific absolute path is present, which is
    the publication-ready state. Scans the full tracked surface (see
    :func:`_scan_candidate_files`), not a fixed documentation-glob list.
    """
    hits: dict[str, list[str]] = {}
    for rel in _scan_candidate_files(root):
        path = root / rel
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        # A mostly-binary tracked file can still carry a maintainer path as literal
        # ASCII (e.g. an embedded string in a `.pyc`/image). utf-8 may raise on it,
        # so fall back to latin-1, which decodes every byte 1:1 and preserves any
        # ASCII path for the regex (ENTO-XV-F1 RESIDUAL-2).
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        matches = sorted(set(_MACHINE_PATH_RE.findall(text)))
        if matches:
            hits[rel] = matches
    return hits


def _security_policy_current_default(text: str) -> bool:
    normalised = _normalise_text(text)
    return (
        crypto.FORMAT_VERSION in text
        and "default wire format" in normalised
        and "compatibility" in normalised
        and not _stale_default_phrase_hits({"SECURITY.md": text})
    )


def _transmission_hash_current_or_pending(root: Path, manifest: dict[str, Any]) -> bool:
    if not manifest:
        return False
    pdf_sha256 = manifest.get("pdf_sha256")
    if manifest.get("published") is not True:
        return pdf_sha256 in (None, "", "pending")
    if not isinstance(pdf_sha256, str) or len(pdf_sha256) != 64:
        return False
    pdf_path = root / "output" / "pdf" / "entofile_combined.pdf"
    if not pdf_path.is_file():
        return False
    return pdf_sha256 == _sha256(pdf_path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_public_endpoints(timeout_seconds: float = 10.0) -> dict[str, Any]:
    """Resolve the planned public endpoints without requiring a publishing side effect."""
    states = {
        name: _endpoint_state(url, timeout_seconds=timeout_seconds)
        for name, url in PUBLIC_ENDPOINTS.items()
    }
    return {
        "checked": True,
        "ok": all(item["ok"] for item in states.values()),
        **states,
    }


def _unchecked_public_endpoint_state() -> dict[str, Any]:
    return {
        "checked": False,
        "ok": False,
        "github": "not_checked",
        "zenodo": "not_checked",
        "doi": "not_checked",
        "note": (
            "Local metadata gate does not perform network publication checks; "
            "release_ready remains false until a live promotion check records public endpoints."
        ),
    }


def _public_endpoint_state_ok(state: dict[str, Any]) -> bool:
    return state.get("checked") is True and state.get("ok") is True


def _endpoint_state(url: str, *, timeout_seconds: float) -> dict[str, Any]:
    head_state = _endpoint_state_once(
        url, method="HEAD", timeout_seconds=timeout_seconds
    )
    if head_state["status"] is not None:
        return head_state
    return _endpoint_state_once(url, method="GET", timeout_seconds=timeout_seconds)


def _endpoint_state_once(
    url: str, *, method: str, timeout_seconds: float
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": PUBLIC_ENDPOINT_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status = int(response.status)
            final_url = response.geturl()
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        final_url = exc.geturl()
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        return {
            "url": url,
            "ok": False,
            "status": None,
            "final_url": None,
            "error": exc.__class__.__name__,
            "method": method,
        }
    return {
        "url": url,
        "ok": 200 <= status < 400,
        "status": status,
        "final_url": final_url,
        "method": method,
    }


def _git_text(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()
