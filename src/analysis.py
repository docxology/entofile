"""ENTO analysis pipeline orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from .artifact_manifest import write_artifact_manifest
from .benchmarks import run_all_benchmarks, write_benchmark_csv, write_validation_report
from .experiment_config import ExperimentConfig, load_experiment_config
from .figure_registry import (
    generate_all_figures,
    register_with_infrastructure,
    write_figure_registry,
)
from .figures import configure_viz
from .output_gates import validate_all_outputs
from .verification_report import write_container_verification_report

try:
    from infrastructure.core.logging.utils import (
        get_logger,  # type: ignore[import-not-found]  # template infra, runtime-only
    )

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


def run_benchmark_pipeline(
    project_root: Path | None = None, *, config: ExperimentConfig | None = None
) -> Path:
    root = project_root or Path(__file__).resolve().parent.parent
    cfg = config or load_experiment_config(root)
    configure_viz(cfg.viz)
    rows = run_all_benchmarks(
        root,
        repetitions=cfg.benchmark_repetitions,
        observability_levels=cfg.observability_levels,
        medium_track_bytes=cfg.medium_track_bytes,
        large_track_bytes=cfg.large_track_bytes,
        include_mixed_container=cfg.include_mixed_container,
    )
    csv_path = root / "output" / "data" / "ento_benchmark_results.csv"
    write_benchmark_csv(rows, csv_path)
    write_validation_report(
        rows, root / "output" / "reports" / "benchmark_validation.json"
    )
    outputs = generate_all_figures(csv_path, root / "output" / "figures")
    register_with_infrastructure(root, outputs)
    write_figure_registry(root, outputs)
    write_container_verification_report(root)
    write_artifact_manifest(root)

    # Standalone release-evidence artifacts (no template checkout required):
    _write_standalone_sbom(root)
    _write_standalone_manuscript_variables(root, cfg)
    _write_standalone_figure_layout_report(root, csv_path)
    _write_standalone_validation_report(root)

    logger.info("Wrote benchmark CSV to %s", csv_path)
    return csv_path


def _write_standalone_sbom(root: Path) -> None:
    """Generate the CycloneDX SBOM skeleton from the resolved dependency tree.

    Falls back gracefully if ``uv export`` is unavailable — the SBOM is an
    optional release artifact, not a pipeline gate.
    """
    try:
        import subprocess

        result = subprocess.run(
            ["uv", "export", "--no-dev", "--no-hashes"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(root),
            timeout=30,
        )
        from .sbom import build_cyclonedx_skeleton

        bom = build_cyclonedx_skeleton(root, result.stdout)
        import json

        out = root / "output" / "reports" / "sbom.cyclonedx.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(bom, indent=2) + "\n", encoding="utf-8")
        logger.info("Wrote SBOM to %s", out)
    except Exception as exc:
        logger.warning("SBOM generation skipped: %s", exc)


def _write_standalone_manuscript_variables(
    root: Path, cfg: ExperimentConfig
) -> None:
    """Generate manuscript variables JSON without the template rendering pipeline.

    The template-based ``z_generate_manuscript_variables.py`` script also
    resolves ``{{TOKEN}}`` injection and writes the resolved manuscript tree,
    which requires ``infrastructure.rendering``. This standalone path writes
    only the variables JSON — enough for the release manifest to record the
    file and for downstream consumers to inspect the measured values.
    """
    try:
        from .manuscript_variables import generate_variables, save_variables

        variables = generate_variables(root, require_analysis_outputs=True, config=cfg)
        out = root / "output" / "data" / "manuscript_variables.json"
        save_variables(variables, out)
        logger.info("Wrote manuscript variables to %s", out)
    except Exception as exc:
        logger.warning("Manuscript variable generation skipped: %s", exc)


def _write_standalone_figure_layout_report(root: Path, csv_path: Path) -> None:
    """Run the renderer-aware figure text layout QA.

    Writes ``output/reports/figure_layout_report.json`` so the release
    manifest can record the file as present.
    """
    try:
        from .figure_qa import validate_registered_figure_layout
        from .telemetry import write_json

        report = validate_registered_figure_layout(csv_path)
        out = root / "output" / "reports" / "figure_layout_report.json"
        write_json(out, report)
        logger.info("Wrote figure layout report to %s", out)
    except Exception as exc:
        logger.warning("Figure layout report skipped: %s", exc)


def _write_standalone_validation_report(root: Path) -> None:
    """Write a standalone manuscript validation report.

    The template-based validation pipeline (``infrastructure.validation``)
    performs full content diagnostics. This standalone version checks:
    - All manuscript markdown files exist and are non-empty
    - No unresolved ``{{TOKEN}}`` placeholders remain
    - References.bib exists and is non-empty
    - Config.yaml has required fields (paper.title, paper.version)

    Writes ``output/reports/validation_report.json``.
    """
    import json

    manuscript_dir = root / "manuscript"
    issues: list[str] = []
    warnings: list[str] = []
    checked_files: list[dict[str, object]] = []

    # Check manuscript markdown files
    md_files = sorted(manuscript_dir.glob("*.md"))
    if not md_files:
        issues.append("No manuscript markdown files found in manuscript/")
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        file_issues: list[str] = []
        if not content.strip():
            file_issues.append("empty file")
        # Check for unresolved tokens
        import re

        tokens = re.findall(r"\{\{[A-Z_]+\}\}", content)
        if tokens:
            file_issues.append(f"unresolved tokens: {', '.join(set(tokens))}")
        checked_files.append({
            "file": md_file.name,
            "lines": len(content.splitlines()),
            "issues": file_issues,
        })
        issues.extend(f"{md_file.name}: {i}" for i in file_issues)

    # Check references.bib
    bib_path = manuscript_dir / "references.bib"
    if not bib_path.is_file():
        warnings.append("manuscript/references.bib not found")
    elif not bib_path.read_text(encoding="utf-8").strip():
        warnings.append("manuscript/references.bib is empty")

    # Check config.yaml
    config_path = manuscript_dir / "config.yaml"
    if not config_path.is_file():
        issues.append("manuscript/config.yaml not found")
    else:
        try:
            import yaml

            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            paper = config.get("paper") or {}
            if not paper.get("title"):
                issues.append("manuscript/config.yaml: paper.title missing")
            if not paper.get("version"):
                issues.append("manuscript/config.yaml: paper.version missing")
        except Exception as exc:
            issues.append(f"manuscript/config.yaml parse error: {exc}")

    report = {
        "ok": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "checked_files": checked_files,
        "validator": "standalone",
        "note": (
            "Standalone validation (no template infrastructure). "
            "Full content diagnostics require the template rendering pipeline."
        ),
    }
    out = root / "output" / "reports" / "validation_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote validation report to %s", out)


def validate_generated_outputs(
    project_root: Path, *, live_containers: bool = False
) -> dict[str, object]:
    """Validate the generated output tree.

    ``live_containers=True`` re-runs the container-verification crypto this call rather
    than trusting the on-disk report — pass it on the *certifying* path (mirrors the
    live-test re-derivation) so a stale/forged container_verification.json cannot
    certify the crypto core."""
    return validate_all_outputs(project_root, live_containers=live_containers)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    run_benchmark_pipeline(root)
    result = validate_generated_outputs(root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
