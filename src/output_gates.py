"""Output validation gates for the ENTO analysis pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .figure_registry import FIGURE_SPECS, caption_token, visual_contract_for_spec


def benchmark_artifacts_ok(project_root: Path) -> bool:
    """Benchmark CSV and validation report exist."""
    csv_path = project_root / "output" / "data" / "ento_benchmark_results.csv"
    report_path = project_root / "output" / "reports" / "benchmark_validation.json"
    return csv_path.is_file() and report_path.is_file()


def benchmark_report_ok(project_root: Path) -> tuple[bool, dict[str, Any]]:
    """Tamper rate and status from benchmark_validation.json."""
    report_path = project_root / "output" / "reports" / "benchmark_validation.json"
    if not report_path.is_file():
        return False, {}
    report = json.loads(report_path.read_text(encoding="utf-8"))
    tamper_rate = float(report.get("tamper_detection_rate", 0.0))
    ok = report.get("status") == "pass" and tamper_rate == 1.0
    return ok, report


def figures_present_ok(project_root: Path) -> bool:
    """All registered figure PNGs exist on disk."""
    figures_dir = project_root / "output" / "figures"
    return all((figures_dir / spec.filename).is_file() for spec in FIGURE_SPECS)


def figure_registry_metadata_ok(project_root: Path) -> bool:
    """Registry JSON must match ``FIGURE_SPECS`` captions and provenance."""
    registry_path = project_root / "output" / "figures" / "figure_registry.json"
    if not registry_path.is_file():
        return False
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for spec in FIGURE_SPECS:
        entry = registry.get(spec.label)
        if not entry:
            return False
        if entry.get("generated_by") != spec.generated_by:
            return False
        if entry.get("caption") != spec.caption:
            return False
        if entry.get("caption_token") != caption_token(spec.label):
            return False
        contract = visual_contract_for_spec(spec)
        for key, value in contract.items():
            if entry.get(key) != value:
                return False
    return True


def _report_is_substantive(report: dict[str, Any]) -> bool:
    """A container-verification report passes only on real substance.

    ``ok:true`` alone is insufficient: a stale or hand-written report claiming
    ``ok:true`` with zero samples (or no negative control) would otherwise certify the
    crypto core without any crypto having run — the F1 oracle false-assurance pattern.
    Bind the pass to substance: a green overall result, at least one verified sample,
    AND a FIRED negative control (a digest-stripped container was actually rejected).
    A report produced by ``build_container_verification_report`` always carries both;
    a forged ``{"ok": true}`` shell does not.
    """
    if not bool(report.get("ok")):
        return False
    samples = report.get("samples")
    if not isinstance(samples, list) or len(samples) < 1:
        return False
    if not all(bool(row.get("ok")) for row in samples):
        return False
    negative_control = report.get("negative_control")
    if not isinstance(negative_control, dict) or not bool(
        negative_control.get("rejected")
    ):
        return False
    return True


def container_verification_report_ok(project_root: Path, *, live: bool = False) -> bool:
    """Whether the container-verification gate passes (a SUBSTANTIVE green report).

    Two derivation modes:

    - ``live=True`` (the *certifying* mode) RE-RUNS the keyless crypto verification
      this call via ``build_container_verification_report`` — which decrypts/verifies
      the real benchmark samples and fires a negative control — and judges that
      in-memory result, IGNORING any on-disk ``container_verification.json``. A stale
      or hand-forged side file therefore cannot certify the crypto core without crypto
      actually running this call. This closes the last side-file-trust residual the
      ISA deferred twice (R12/R13), the same class as the publication ``--check``
      live-test re-derivation. Fails closed (``False``) when no benchmark samples
      exist to verify — a certification cannot pass without containers to check.
    - ``live=False`` (the default, *display/aggregation* mode) reads the on-disk
      report. Suitable for surfacing an already-produced pipeline result; it is NOT a
      standalone certification because nothing re-runs the crypto.

    ``ok:true`` alone is never sufficient in either mode — see ``_report_is_substantive``.
    """
    if live:
        from .verification_report import build_container_verification_report

        return _report_is_substantive(build_container_verification_report(project_root))
    report_path = project_root / "output" / "reports" / "container_verification.json"
    if not report_path.is_file():
        return False
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return _report_is_substantive(report)


def load_container_verification_report(project_root: Path) -> dict[str, Any] | None:
    """Return parsed verification report or None when absent."""
    report_path = project_root / "output" / "reports" / "container_verification.json"
    if not report_path.is_file():
        return None
    return json.loads(report_path.read_text(encoding="utf-8"))


def validate_all_outputs(
    project_root: Path, *, live_containers: bool = False
) -> dict[str, object]:
    """Aggregate pipeline output gate results.

    ``live_containers=True`` re-derives the container-verification gate by re-running
    the crypto this call (ignoring the on-disk report) — pass it on any *certifying*
    invocation so a stale/forged ``container_verification.json`` cannot pass the
    aggregate gate. The default reads the freshly-written report (the pipeline writes
    it via live crypto immediately before validating, so the read is equivalent there).
    """
    files_ok = benchmark_artifacts_ok(project_root)
    metrics_ok, report = benchmark_report_ok(project_root)
    figures_ok = figures_present_ok(project_root)
    registry_ok = (
        project_root / "output" / "figures" / "figure_registry.json"
    ).is_file()
    registry_provenance_ok = figure_registry_metadata_ok(project_root)
    containers_ok = container_verification_report_ok(project_root, live=live_containers)
    tamper_rate = float(report.get("tamper_detection_rate", 0.0)) if report else 0.0
    ok = (
        files_ok
        and figures_ok
        and registry_ok
        and registry_provenance_ok
        and containers_ok
        and metrics_ok
    )
    return {
        "ok": ok,
        "report": report,
        "tamper_detection_rate": tamper_rate,
        "figures_ok": figures_ok,
        "registry_ok": registry_ok,
        "registry_provenance_ok": registry_provenance_ok,
        "containers_ok": containers_ok,
        # Carry how containers_ok was derived so a certifying consumer can REFUSE to
        # treat a display-grade (side-file) check as a certification — the caller must
        # not be trusted to remember it ran in live mode. False => side-file read.
        "containers_live": bool(live_containers),
    }
