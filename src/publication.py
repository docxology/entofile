"""Publication readiness checks for the entofile manuscript release."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .analysis import validate_generated_outputs
from .crypto import FORMAT_VERSION, MASTER_KEY_SIZE, NONCE_SIZE, TAG_SIZE
from .test_results import parse_test_summary

# Env flag set inside the live test subprocess so the meta-test that triggers a live
# run does not recurse (it skips when this is set). See tests/test_publication_live.py.
_LIVE_RUN_ENV = "ENTOFILE_PUBLICATION_LIVE_RUN"
_LIVE_RUN_TIMEOUT_S = 600


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a small YAML config file; return an empty mapping on absent/invalid input."""
    if not path.is_file():
        return {}
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError, ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _run_live_test_summary(project_root: Path) -> dict[str, Any]:
    """Re-derive the test summary by ACTUALLY running pytest — never trust a side file.

    Closes the F1 oracle-false-assurance residual: ``test_results.json`` is written by
    an external pipeline (or could be hand-written/stale), so a forged ``all_passed:true``
    would otherwise certify a red project. This runs the suite live and reports only what
    it observed. Fail-closed on every ambiguity (per the project's "audit: verify
    collection not just exit" and "reproduce, don't trace" memory):

    - parses structured junitxml (tests/passed/failures/errors) + coverage JSON, never stdout;
    - requires ``collected > 0`` (pytest exit 5 = no tests collected must NOT read as pass);
    - a missing/unparseable report, a timeout, or a wrong interpreter → ``all_passed: False``;
    - sets a recursion-guard env var so the nested run's meta-test skips.

    Returns ``{"all_passed": bool, "project_coverage": float|None, "collected": int,
    "source": "live", "detail": str}``.
    """
    if os.environ.get(_LIVE_RUN_ENV):
        # Already inside a live run — refuse to recurse, fail-closed.
        return {
            "all_passed": False,
            "project_coverage": None,
            "collected": 0,
            "source": "live",
            "detail": "recursion guard active",
        }
    with tempfile.TemporaryDirectory() as td:
        junit = Path(td) / "junit.xml"
        cov_json = Path(td) / "coverage.json"
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            f"--junitxml={junit}",
            "--cov=src",
            f"--cov-report=json:{cov_json}",
            "-q",
        ]
        env = {**os.environ, _LIVE_RUN_ENV: "1"}
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                start_new_session=os.name != "nt",
            )
            try:
                proc.communicate(timeout=_LIVE_RUN_TIMEOUT_S)
            except subprocess.TimeoutExpired as exc:
                if os.name == "nt":
                    proc.kill()
                else:
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
                return {
                    "all_passed": False,
                    "project_coverage": None,
                    "collected": 0,
                    "source": "live",
                    "detail": f"subprocess failed: {exc}",
                }
        except (OSError, subprocess.SubprocessError) as exc:
            return {
                "all_passed": False,
                "project_coverage": None,
                "collected": 0,
                "source": "live",
                "detail": f"subprocess failed: {exc}",
            }
        return _parse_live_results(junit, cov_json, proc.returncode)


def _parse_live_results(junit: Path, cov_json: Path, returncode: int) -> dict[str, Any]:
    """Parse junitxml + coverage JSON into a fail-closed summary."""
    return parse_test_summary(junit, cov_json, returncode, source="live")


def _is_real_pdf(path: Path, *, min_bytes: int = 1024) -> bool:
    """A real PDF: exists, starts with the %PDF- magic, and is non-trivially sized.

    Guards against a placeholder/truncated file passing a bare ``is_file()`` check.
    """
    if not path.is_file() or path.stat().st_size < min_bytes:
        return False
    with path.open("rb") as handle:
        return handle.read(5) == b"%PDF-"


def _evidence_issues(project_root: Path) -> tuple[list[str], str]:
    """Return (manuscript evidence-grounding issues, source).

    Prefers a LIVE re-derivation via the template evidence registry (the certification
    context, where ``infrastructure`` is importable) so a stale ``validation_report.json``
    cannot certify prose whose numbers were since grounded/un-grounded. Falls back to the
    on-disk report when the infra is unavailable (isolated project venv). ``source`` is
    "live" or "side-file" so a caller can tell certification from a convenience read.
    """
    try:
        import glob

        from infrastructure.validation.evidence_registry import (  # type: ignore[import-not-found]
            build_project_evidence_registry,
            unsupported_citation_tokens,
            unsupported_number_tokens,
            validate_text_against_registry,
        )

        registry = build_project_evidence_registry(project_root)
        md_files = sorted(glob.glob(str(project_root / "manuscript" / "*.md")))
        text = "\n".join(
            Path(p).read_text(encoding="utf-8")
            for p in md_files
            if Path(p).name[:2].isdigit()
        )
        report = validate_text_against_registry(text, registry)
        issues = [f"unsupported number {n}" for n in unsupported_number_tokens(report)]
        issues += [
            f"unsupported citation {c}" for c in unsupported_citation_tokens(report)
        ]
        return issues, "live"
    except ImportError:
        # Infra (the live registry) unavailable — isolated project venv. Fall back to the
        # on-disk report, but freshness-guard it: a validation_report.json older than the
        # manuscript or the claim ledger describes prose/grounding it never saw, so trusting
        # its (absent) issues would be the stale-side-file F1 pattern. A stale report is
        # treated as unverifiable, not clean.
        report_path = project_root / "output" / "reports" / "validation_report.json"
        if not report_path.is_file():
            return [
                "validation_report.json absent (run the pipeline to ground manuscript evidence)"
            ], "side-file"
        report_mtime = report_path.stat().st_mtime
        sources = [
            project_root / "manuscript",
            project_root / "data" / "claim_ledger.yaml",
        ]
        newest_source = max(
            (
                p.stat().st_mtime
                for src in sources
                for p in ([src] if src.is_file() else src.rglob("*.md"))
                if p.is_file()
            ),
            default=0.0,
        )
        if newest_source > report_mtime:
            return [
                "validation_report.json is stale (older than manuscript/claim_ledger); re-run the pipeline"
            ], "side-file (stale)"
        validation = _read_json(report_path)
        stats = validation.get("output_statistics")
        side_issues = (
            stats.get("evidence_issues", []) if isinstance(stats, dict) else []
        )
        return list(side_issues), "side-file"


def _find_combined_pdf(pdf_dir: Path) -> Path | None:
    """Return a real combined manuscript PDF in ``pdf_dir``, or None.

    The renderer names it ``<project>_combined.pdf`` (full pipeline) or
    ``_combined_manuscript.pdf`` (standalone render); accept whichever exists so the
    gate verifies the actual artifact regardless of invocation path. Only a file that
    passes :func:`_is_real_pdf` qualifies.
    """
    if not pdf_dir.is_dir():
        return None
    candidates = sorted(pdf_dir.glob("*_combined.pdf")) + sorted(
        pdf_dir.glob("_combined_manuscript.pdf")
    )
    for candidate in candidates:
        if _is_real_pdf(candidate):
            return candidate
    return None


# Case-insensitive sentinel values that signal an UNBOUND metric — a token that
# resolved to one of these renders as fake text (no {{}} residue) where a real value
# belongs. "" / "false" / "true" are NOT here: they are legitimate for specific tokens
# (an empty PAPER_SUBTITLE, the boolean RESULT_CONTAINER_VERIFY_OK), so a blanket ban
# would false-reject. They are handled per-token below.
_UNBOUND_SENTINELS: frozenset[str] = frozenset(
    {"n/a", "na", "none", "null", "nan", "tbd", "todo", "n.a."}
)

# Tokens whose value carries a pass/fail meaning: a specific value is a publication
# BLOCKER even though it is not an "unbound" sentinel. Maps token -> blocking value(s).
_BOOLEAN_BLOCKER_TOKENS: dict[str, frozenset[str]] = {
    "RESULT_CONTAINER_VERIFY_OK": frozenset({"false"}),
}

_PROSE_TOKEN_PREFIXES = ("FIG_CAPTION_", "FIGURE_BLOCK_")


def _na_valued_tokens(variables_json_text: str) -> set[str]:
    """Token names in manuscript_variables.json that signal an unbound/failed metric.

    Catches (a) any non-prose token whose value is a case-insensitive unbound sentinel
    (N/A, none, null, nan, tbd, todo, …) — these render as fake text where a real metric
    belongs; and (b) a pass/fail token resolved to its blocking value (e.g.
    RESULT_CONTAINER_VERIFY_OK == "false", a failed container verification that must not
    silently ship). Prose tokens (FIG_CAPTION_/FIGURE_BLOCK_) are excluded; legitimately
    empty/boolean tokens (PAPER_SUBTITLE="", RESULT_CONTAINER_VERIFY_OK="true") are NOT
    flagged.
    """
    try:
        data = json.loads(variables_json_text)
    except json.JSONDecodeError:
        return set()
    if not isinstance(data, dict):
        return set()
    flagged: set[str] = set()
    for key, value in data.items():
        if key.startswith(_PROSE_TOKEN_PREFIXES) or not isinstance(value, str):
            continue
        if value.strip().casefold() in _UNBOUND_SENTINELS or (
            key in _BOOLEAN_BLOCKER_TOKENS
            and value.strip().casefold() in _BOOLEAN_BLOCKER_TOKENS[key]
        ):
            flagged.add(key)
    return flagged


def check_publication_readiness(
    project_root: Path, *, live_tests: bool = False
) -> dict[str, object]:
    """Return structured gate results for the configured manuscript release.

    ``live_tests``: when True (the certifying path — set by ``audit_publication_readiness
    --check``), the test/coverage verdict is RE-DERIVED by actually running pytest, and
    the on-disk ``test_results.json`` is ignored entirely. This closes the F1 residual
    where a stale/forged side file could certify a red project. When False (display/quick
    path), the side file is read — but ``tests_source`` records "side-file" so a caller
    can tell certification from a convenience read. The certifying path NEVER returns a
    green test verdict from the side file alone.
    """
    root = project_root.resolve()
    checks: dict[str, bool] = {}
    blockers: list[str] = []
    warnings: list[str] = []

    if live_tests:
        summary = _run_live_test_summary(root)
        tests_source = "live"
    else:
        summary = _read_json(root / "output" / "reports" / "test_results.json").get(
            "summary", {}
        )
        tests_source = "side-file"

    if summary.get("all_passed") is True:
        checks["tests_passed"] = True
    else:
        checks["tests_passed"] = False
        blockers.append(
            f"project tests did not all pass ({tests_source}: {summary.get('detail', 'see test_results.json')})"
        )

    coverage = summary.get("project_coverage")
    if isinstance(coverage, (int, float)) and float(coverage) >= 90.0:
        checks["coverage_floor"] = True
    else:
        checks["coverage_floor"] = False
        blockers.append(f"project coverage below 90% or unavailable ({tests_source})")

    # On the certifying path (live_tests) re-run the container crypto live too, so a
    # stale/forged container_verification.json cannot certify the crypto core — the same
    # side-file-trust closure applied to the test summary above.
    outputs = validate_generated_outputs(root, live_containers=live_tests)
    if outputs.get("ok"):
        checks["analysis_outputs"] = True
    else:
        checks["analysis_outputs"] = False
        blockers.append(f"validate_generated_outputs failed: {outputs}")
    # Defense-in-depth against the twice-deferred side-file-trust residual regressing:
    # on the certifying path the container gate MUST have been re-derived live (crypto
    # re-run this call), not read from a possibly-stale/forged report. Trust the result
    # object's own record of how it ran, not that this call site passed the right flag.
    if live_tests and not outputs.get("containers_live"):
        checks["analysis_outputs"] = False
        blockers.append(
            "container verification was not re-derived live on the certifying path "
            "(containers_live is false) — refusing to certify a side-file-only check"
        )

    # Certifying path: re-derive CONFORMANCE live too — the last evidence rung
    # that was still side-file trust. Fixtures are deterministic (fixed key,
    # timestamp, nonce), so they are regenerated fresh into a scratch dir and
    # verified in one call; output/reports/conformance_report.json is ignored
    # here, exactly like the test summary and container gates above.
    if live_tests:
        from .conformance import run_live_conformance

        conformance = run_live_conformance()
        from .conformance import EXPECTED_CASE_IDS

        observed_case_ids = {
            str(case.get("case_id"))
            for case in conformance.get("cases", [])
            if isinstance(case, dict)
        }
        complete = (
            int(conformance.get("case_count") or 0) == len(EXPECTED_CASE_IDS)
            and observed_case_ids == EXPECTED_CASE_IDS
        )
        if bool(conformance.get("ok")) and complete:
            checks["conformance_live"] = True
        else:
            checks["conformance_live"] = False
            blockers.append(
                "live conformance verification failed: "
                f"{conformance.get('failed_cases') or 'incomplete case matrix'}"
            )

    # Find the combined manuscript PDF by its actual produced name. The renderer names
    # it "<project>_combined.pdf" (full pipeline) or "_combined_manuscript.pdf"
    # (standalone render), so a single hardcoded name false-fails depending on the
    # invocation path. Accept either, and require substance (real %PDF- header + size),
    # not bare existence — a 1-byte/non-PDF placeholder must not certify "rendered".
    pdf_dir = root / "output" / "pdf"
    combined_pdf = _find_combined_pdf(pdf_dir)
    checks["combined_pdf"] = combined_pdf is not None
    if not checks["combined_pdf"]:
        blockers.append(
            f"no valid combined manuscript PDF in {pdf_dir} (need *_combined.pdf or "
            "_combined_manuscript.pdf with a real %PDF- header and non-trivial size)"
        )

    # Evidence grounding: re-derive live when the validation infra is importable (the
    # certification context), so a stale validation_report.json cannot certify prose whose
    # numbers were since grounded (or un-grounded) — the same trusted-stale-side-file class
    # as the live test re-derivation above. Fall back to the on-disk report only when the
    # infra is unavailable (isolated venv), labelling the source.
    evidence_issues, evidence_source = _evidence_issues(root)
    if not evidence_issues:
        checks["evidence_registry"] = True
    else:
        checks["evidence_registry"] = False
        blockers.append(
            f"unsupported manuscript evidence ({evidence_source}): {evidence_issues}"
        )

    variables_path = root / "output" / "data" / "manuscript_variables.json"
    if variables_path.is_file():
        text = variables_path.read_text(encoding="utf-8")
        nested_caption = re.compile(r"\{\{(?!FIG_CAPTION_)[A-Z][A-Z0-9_]*\}\}")
        has_unresolved_token = nested_caption.search(text) is not None
        # A token that RESOLVED to the literal string "N/A" is not a {{TOKEN}} residue,
        # so the regex above misses it — yet it renders "N/A" where a real metric belongs.
        # Flag any result/fixture/config value that came back N/A as a blocker too.
        na_values = _na_valued_tokens(text)
        checks["manuscript_variables"] = not has_unresolved_token and not na_values
        if has_unresolved_token:
            blockers.append("unresolved {{TOKENS}} in manuscript_variables.json")
        if na_values:
            blockers.append(
                f"manuscript tokens resolved to 'N/A' (unbound metrics): {sorted(na_values)}"
            )
    else:
        checks["manuscript_variables"] = False
        blockers.append("missing output/data/manuscript_variables.json")

    config_path = root / "manuscript" / "config.yaml"
    config = _read_yaml(config_path)
    paper_raw = config.get("paper")
    paper: dict[str, Any] = paper_raw if isinstance(paper_raw, dict) else {}
    release = str(paper.get("version", "0.4"))
    config_text = (
        config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
    )
    if (
        "doi:" in config_text
        and 'doi: ""' not in config_text
        and "doi: ''" not in config_text
    ):
        checks["doi_configured"] = True
    else:
        checks["doi_configured"] = False
        warnings.append(
            "publication.doi not set in manuscript/config.yaml (optional pre-deposit)"
        )

    ok = not blockers
    return {
        "ok": ok,
        "release": release,
        "format_version": FORMAT_VERSION,
        "tests_source": tests_source,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "crypto_constants": {
            "master_key_bytes": MASTER_KEY_SIZE,
            "nonce_bytes": NONCE_SIZE,
            "tag_bytes": TAG_SIZE,
            "track_header_bytes": NONCE_SIZE + TAG_SIZE,
        },
    }
