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
    logger.info("Wrote benchmark CSV to %s", csv_path)
    return csv_path


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
