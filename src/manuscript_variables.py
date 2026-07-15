"""Manuscript variable generation for entofile."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .benchmark_io import benchmark_csv_path, load_benchmark_csv
from .benchmark_stats import (
    avg_field,
    avg_manifest_bytes,
    benchmark_data_fingerprint,
    ci_method_description,
    field_summary,
    result_table_rows,
    tamper_detected_count,
)
from .container import REPORTED_INTEGRITY_LEVELS
from .crypto import (
    FORMAT_VERSION,
    FORMAT_VERSION_LATEST,
    FORMAT_VERSION_NEXT,
    FORMAT_VERSION_PREVIOUS,
    MASTER_KEY_SIZE,
    SUPPORTED_FORMAT_VERSIONS,
    TAG_SIZE,
    crypto_backend_for_format,
    nonce_size_for,
    pads_payload,
)
from .figure_registry import (
    FIGURE_SPECS,
    figure_block_markdown,
    figure_caption_variables,
    figure_index_markdown,
    spec_by_label,
)
from .fixtures import FIXTURE_MAPPING, fixtures_dir
from .output_gates import benchmark_report_ok, load_container_verification_report

try:
    from .experiment_config import ExperimentConfig, load_experiment_config
except ImportError:  # pragma: no cover
    from experiment_config import (  # type: ignore[no-redef,import-untyped,import-not-found]
        ExperimentConfig,
        load_experiment_config,
    )

try:
    from infrastructure.core.logging.utils import (
        get_logger,  # type: ignore[import-not-found]  # template infra, runtime-only
    )

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

_THROUGHPUT_SPEC_LABEL = "fig:throughput_benchmark"
_EXPANSION_SPEC_LABEL = "fig:expansion_ratio"
_OBSERVABILITY_SPEC_LABEL = "fig:observability_manifest_size"
_BENCHMARK_PILOT_REPETITIONS = 3
_NO_MOCK_PATTERNS = ("unittest.mock", "MagicMock", "@patch")


def benchmark_rows_per_repetition(cfg: ExperimentConfig) -> int:
    """Rows emitted by one benchmark repetition for the configured matrix."""
    tracks_per_repetition = len(FIXTURE_MAPPING) + 1  # fixture tracks + medium
    if cfg.large_track_bytes > 0:
        tracks_per_repetition += 1
    if cfg.include_mixed_container:
        tracks_per_repetition += len(FIXTURE_MAPPING) + 1
    return tracks_per_repetition * len(cfg.observability_levels)


def _load_config(project_root: Path) -> dict[str, Any]:
    path = project_root / "manuscript" / "config.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_benchmark_rows(project_root: Path) -> list[dict[str, str]]:
    return load_benchmark_csv(benchmark_csv_path(project_root))


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        return "N/A"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _list_output_files(project_root: Path, subdir: str, pattern: str = "*") -> str:
    directory = project_root / "output" / subdir
    if not directory.is_dir():
        return "N/A"
    names = sorted(path.name for path in directory.glob(pattern) if path.is_file())
    return ", ".join(names) if names else "N/A"


def _json_status(path: Path, *, ok_field: str = "ok") -> str:
    if not path.is_file():
        return "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "invalid JSON"
    if ok_field in payload:
        return "pass" if bool(payload[ok_field]) else "fail"
    status = payload.get("status")
    return str(status) if status is not None else "present"


def _no_mock_status(project_root: Path) -> str:
    tests_root = project_root / "tests"
    if not tests_root.is_dir():
        return "tests directory missing"
    hits: list[str] = []
    for path in sorted(tests_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for pattern in _NO_MOCK_PATTERNS:
            if pattern in text:
                hits.append(f"{path.relative_to(project_root)}:{pattern}")
    return "Clean" if not hits else "; ".join(hits)


def generate_variables(
    project_root: Path,
    *,
    require_analysis_outputs: bool = False,
    config: ExperimentConfig | None = None,
) -> dict[str, str]:
    cfg = config or load_experiment_config(project_root)
    manuscript_config = _load_config(project_root)
    rows = _load_benchmark_rows(project_root)
    if require_analysis_outputs and not rows:
        raise FileNotFoundError("output/data/ento_benchmark_results.csv is required")

    throughput_spec = spec_by_label(_THROUGHPUT_SPEC_LABEL)
    expansion_spec = spec_by_label(_EXPANSION_SPEC_LABEL)
    observability_spec = spec_by_label(_OBSERVABILITY_SPEC_LABEL)

    avg_throughput = avg_field(rows, throughput_spec, "pack_throughput_mib_s")
    avg_unpack = avg_field(rows, throughput_spec, "unpack_seconds")
    avg_expansion = avg_field(rows, expansion_spec, "expansion_ratio")
    # Dispersion (n, sd, cv, 95% t-CI) for the headline timing metric so the
    # manuscript reports reliability, not just a point mean.
    throughput_summary = field_summary(rows, throughput_spec, "pack_throughput_mib_s")
    tamper_detected = tamper_detected_count(rows)
    table_rows = result_table_rows(rows, expansion_spec)
    obs_track = observability_spec.track_id or "eeg"

    config_hash = hashlib.sha256(
        (project_root / "manuscript" / "config.yaml").read_bytes()
    ).hexdigest()[:16]
    fixture_root = fixtures_dir(project_root)
    csv_path = project_root / "output" / "data" / "ento_benchmark_results.csv"
    registry_path = project_root / "output" / "figures" / "figure_registry.json"
    keywords = (
        (manuscript_config.get("keywords") or [])
        if isinstance(manuscript_config.get("keywords"), list)
        else []
    )
    authors = manuscript_config.get("authors") or []
    first_author = authors[0].get("name", "N/A") if authors else "N/A"
    test_report_path = project_root / "output" / "reports" / "test_results.json"
    test_report = (
        json.loads(test_report_path.read_text(encoding="utf-8"))
        if test_report_path.is_file()
        else {}
    )
    measured_coverage = test_report.get("summary", {}).get("project_coverage", "N/A")
    figure_width = str(cfg.viz.figure_width_percent)

    verify_report = load_container_verification_report(project_root) or {}
    samples = verify_report.get("samples", [])
    sample_path = samples[0].get("path", "N/A") if samples else "N/A"
    sbom_path = project_root / "output" / "reports" / "sbom.cyclonedx.json"
    conformance_report_path = project_root / "output" / "reports" / "conformance_report.json"
    artifact_manifest_path = project_root / "output" / "reports" / "artifact_manifest.json"
    release_manifest_path = project_root / "output" / "release" / "release_manifest.json"
    sbom_component_count = 0
    if sbom_path.is_file():
        try:
            sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sbom = {}
        components = sbom.get("components", []) if isinstance(sbom, dict) else []
        sbom_component_count = len(components) if isinstance(components, list) else 0

    paper = manuscript_config.get("paper") or {}
    benchmark_ok, benchmark_report = benchmark_report_ok(project_root)
    overview_spec = spec_by_label("fig:benchmark_overview")
    overview_width = (
        str(overview_spec.width_percent)
        if overview_spec.width_percent is not None
        else figure_width
    )
    tamper_rate = (
        benchmark_report.get("tamper_detection_rate") if benchmark_report else None
    )
    validation_status = (
        str(benchmark_report.get("status", "N/A")) if benchmark_report else "N/A"
    )
    obs_levels = cfg.observability_levels
    obs_max = max(obs_levels) if obs_levels else 3
    rows_per_repetition = benchmark_rows_per_repetition(cfg)
    expected_benchmark_rows = rows_per_repetition * cfg.benchmark_repetitions
    throughput_df = throughput_summary.n - 1 if throughput_summary else None
    repetition_scale = cfg.benchmark_repetitions / float(_BENCHMARK_PILOT_REPETITIONS)

    # Format ladder, derived from crypto (never hand-written in prose):
    # compatibility versions are every supported version except the default,
    # ordered by SEMANTIC version (parse to int tuple) so "first"/"latest" stay
    # correct even past 0.3.10 — a plain string sort would mis-order 0.3.10 < 0.3.2.
    def _semver_key(v: str) -> tuple[int, ...]:
        return tuple(int(part) for part in v.split("."))

    def _join_versions(versions: tuple[str, ...]) -> str:
        if not versions:
            return "N/A"
        if len(versions) == 1:
            return versions[0]
        if len(versions) == 2:
            return " and ".join(versions)
        return ", ".join(versions[:-1]) + f" and {versions[-1]}"

    sorted_versions = tuple(sorted(SUPPORTED_FORMAT_VERSIONS, key=_semver_key))
    compatibility_versions = tuple(v for v in sorted_versions if v != FORMAT_VERSION)
    # FORMAT_VERSION_NEXT is a compatibility alias retained for older consumers;
    # there is no unimplemented forward profile in the current release.
    forward_versions: tuple[str, ...] = ()
    hardened_versions = tuple(v for v in sorted_versions if v != "0.2.0")
    hardened_join = _join_versions(hardened_versions)
    compatibility_join = _join_versions(compatibility_versions)
    # The hardened nonce size (12 for 0.3.x) read through the canonical resolver.
    hardened_nonce = (
        nonce_size_for(FORMAT_VERSION_LATEST)
        if hardened_versions
        else nonce_size_for(FORMAT_VERSION)
    )
    default_nonce = nonce_size_for(FORMAT_VERSION)
    default_header_bytes = default_nonce + TAG_SIZE

    variables: dict[str, str] = {
        "FORMAT_VERSION": FORMAT_VERSION,
        "FORMAT_VERSION_HARDENED_FIRST": hardened_versions[0]
        if hardened_versions
        else "N/A",
        "FORMAT_VERSION_LATEST": FORMAT_VERSION_LATEST,
        "FORMAT_VERSION_PREVIOUS": FORMAT_VERSION_PREVIOUS,
        "FORMAT_VERSION_NEXT": FORMAT_VERSION_NEXT,
        # Canonical current-profile names; retain the NEXT aliases below for
        # manuscript consumers that adopted the pre-default 0.5.0 vocabulary.
        "FORMAT_AAD_TEMPLATE": (
            f"ento:{FORMAT_VERSION}:manifest:{{manifest_binding}}:track:{{track_id}}"
        ),
        "FORMAT_BINDING_DESCRIPTION": (
            "canonical SHA-256 of the exported manifest context in every track tag"
        ),
        "FORMAT_NEXT_AAD_TEMPLATE": (
            f"ento:{FORMAT_VERSION}:manifest:{{manifest_binding}}:track:{{track_id}}"
        ),
        "FORMAT_NEXT_BINDING_DESCRIPTION": (
            "canonical SHA-256 of the exported manifest context in every track tag"
        ),
        "FORMAT_VERSIONS_HARDENED": hardened_join,
        "FORMAT_VERSIONS_COMPATIBILITY": compatibility_join,
        # This is a structural state, not a missing metric. Use descriptive
        # prose rather than a sentinel that the publication gate would reject.
        "FORMAT_VERSIONS_FORWARD": (
            _join_versions(forward_versions)
            if forward_versions
            else "not applicable (current profile)"
        ),
        "FORMAT_VERSIONS_SUPPORTED": ", ".join(SUPPORTED_FORMAT_VERSIONS),
        "NONCE_BYTES_HARDENED": str(hardened_nonce),
        "FORMAT_DEFAULT_HEADER_BYTES": str(default_header_bytes),
        "FORMAT_DEFAULT_PADS": "yes" if pads_payload(FORMAT_VERSION) else "no",
        "FORMAT_DEFAULT_EXPANSION_MODEL": (
            "r(n) = (H + PADME(n + 8)) / n"
            if pads_payload(FORMAT_VERSION)
            else "r(n) = (H + n) / n"
        ),
        "FORMAT_LATEST_PADS": "yes" if pads_payload(FORMAT_VERSION_LATEST) else "no",
        # Derived counts so spelled-out cardinalities in prose cannot drift when a
        # level or hardened format is added (len() of the canonical sources).
        "COUNT_OBSERVABILITY_LEVELS": str(len(obs_levels)) if obs_levels else "N/A",
        "COUNT_HARDENED_FORMATS": str(len(hardened_versions)),
        "COUNT_COMPATIBILITY_FORMATS": str(len(compatibility_versions)),
        "COUNT_FORWARD_FORMATS": str(len(forward_versions)),
        "COUNT_SUPPORTED_FORMATS": str(len(SUPPORTED_FORMAT_VERSIONS)),
        "COUNT_INTEGRITY_LEVELS": str(len(REPORTED_INTEGRITY_LEVELS)),
        "CRYPTO_BACKEND_DEFAULT": crypto_backend_for_format(FORMAT_VERSION),
        "PAPER_TITLE": str(paper.get("title", "N/A")),
        "PAPER_SUBTITLE": str(paper.get("subtitle", "")),
        "PAPER_VERSION": str(paper.get("version", "N/A")),
        "NONCE_BYTES": str(default_nonce),
        "TAG_BYTES": str(TAG_SIZE),
        "CONFIG_OBSERVABILITY_LEVEL_MAX": str(obs_max),
        "RESULT_TAMPER_DETECTION_RATE": (
            f"{float(tamper_rate):.1f}" if tamper_rate is not None else "N/A"
        ),
        "RESULT_BENCHMARK_VALIDATION_STATUS": validation_status
        if benchmark_ok or benchmark_report
        else "N/A",
        "FIGURE_OVERVIEW_WIDTH": overview_width,
        "MASTER_KEY_BYTES": str(MASTER_KEY_SIZE),
        "TRACK_HEADER_BYTES": str(default_header_bytes),
        "TEST_COVERAGE_MIN": "90",
        "MEASURED_COVERAGE_PERCENT": f"{float(measured_coverage):.2f}"
        if isinstance(measured_coverage, (int, float))
        else "N/A",
        "FIGURE_WIDTH": figure_width,
        "CONFIG_BENCHMARK_REPETITIONS": str(cfg.benchmark_repetitions),
        "CONFIG_BENCHMARK_PILOT_REPETITIONS": str(_BENCHMARK_PILOT_REPETITIONS),
        "CONFIG_BENCHMARK_REPETITION_SCALE": (
            f"{repetition_scale:.0f}"
            if repetition_scale.is_integer()
            else f"{repetition_scale:.1f}"
        ),
        "CONFIG_OBSERVABILITY_LEVELS": ",".join(
            str(v) for v in cfg.observability_levels
        ),
        "CONFIG_MEDIUM_TRACK_BYTES": str(cfg.medium_track_bytes),
        "CONFIG_LARGE_TRACK_BYTES": str(cfg.large_track_bytes),
        "CONFIG_INCLUDE_MIXED_CONTAINER": str(cfg.include_mixed_container).lower(),
        "CONFIG_VIZ_DPI": str(cfg.viz.dpi),
        "RESULT_ROWS_PER_REPETITION": str(rows_per_repetition),
        "RESULT_EXPECTED_BENCHMARK_ROWS": str(expected_benchmark_rows),
        "RESULT_BENCHMARK_ROWS": str(len(rows)) if rows else "N/A",
        "RESULT_AVG_THROUGHPUT_MIB_S": f"{avg_throughput:.4f}"
        if avg_throughput is not None
        else "N/A",
        "RESULT_THROUGHPUT_N": str(throughput_summary.n)
        if throughput_summary
        else "N/A",
        "RESULT_THROUGHPUT_DF": str(throughput_df)
        if throughput_df is not None
        else "N/A",
        "RESULT_THROUGHPUT_CI_METHOD": ci_method_description(throughput_summary.n)
        if throughput_summary
        else "N/A",
        "RESULT_THROUGHPUT_SD_MIB_S": f"{throughput_summary.sd:.4f}"
        if throughput_summary
        else "N/A",
        "RESULT_THROUGHPUT_CV_PERCENT": f"{throughput_summary.cv * 100:.1f}"
        if throughput_summary
        else "N/A",
        "RESULT_THROUGHPUT_CI95_LO_MIB_S": f"{throughput_summary.ci95_lo:.4f}"
        if throughput_summary
        else "N/A",
        "RESULT_THROUGHPUT_CI95_HI_MIB_S": f"{throughput_summary.ci95_hi:.4f}"
        if throughput_summary
        else "N/A",
        "RESULT_AVG_UNPACK_SECONDS": f"{avg_unpack:.6f}"
        if avg_unpack is not None
        else "N/A",
        "RESULT_AVG_EXPANSION_RATIO": f"{avg_expansion:.4f}"
        if avg_expansion is not None
        else "N/A",
        "RESULT_TAMPER_DETECTED_COUNT": str(tamper_detected) if rows else "N/A",
        "RESULT_TABLE_ROWS": table_rows if table_rows else "N/A",
        "RESULT_MANIFEST_BYTES_L0": avg_manifest_bytes(rows, obs_track, 0)
        if rows
        else "N/A",
        "RESULT_MANIFEST_BYTES_L1": avg_manifest_bytes(rows, obs_track, 1)
        if rows
        else "N/A",
        "RESULT_MANIFEST_BYTES_L2": avg_manifest_bytes(rows, obs_track, 2)
        if rows
        else "N/A",
        "RESULT_MANIFEST_BYTES_L3": avg_manifest_bytes(rows, obs_track, 3)
        if rows
        else "N/A",
        "FIXTURE_EEG_SHA256": _sha256_file(fixture_root / "eeg.csv"),
        "FIXTURE_VCF_SHA256": _sha256_file(fixture_root / "sample.vcf"),
        "FIXTURE_SPECTROGRAM_SHA256": _sha256_file(fixture_root / "spectrogram.bin"),
        "BENCHMARK_CSV_SHA256": _sha256_file(csv_path),
        "BENCHMARK_DATA_FINGERPRINT": benchmark_data_fingerprint(rows),
        "SBOM_STATUS": "present" if sbom_path.is_file() else "missing",
        "SBOM_PATH": str(sbom_path.relative_to(project_root))
        if sbom_path.is_file()
        else "missing",
        "SBOM_COMPONENT_COUNT": str(sbom_component_count),
        "NO_MOCK_STATUS": _no_mock_status(project_root),
        "FIXTURE_INPUT_CLASSIFICATION": "committed deterministic fixture inputs",
        "BENCHMARK_STRESS_INPUT_CLASSIFICATION": "generated synthetic throughput stress track",
        "CONFORMANCE_INPUT_CLASSIFICATION": "deterministic test-vector containers",
        "EXECUTION_EVIDENCE_CLASSIFICATION": "real ZIP, crypto, filesystem, and render execution outputs",
        "CONFORMANCE_REPORT_STATUS": _json_status(conformance_report_path),
        "CONFORMANCE_REPORT_PATH": str(conformance_report_path.relative_to(project_root))
        if conformance_report_path.is_file()
        else "missing",
        "ARTIFACT_MANIFEST_STATUS": _json_status(artifact_manifest_path, ok_field="valid")
        if artifact_manifest_path.is_file()
        else "missing",
        "ARTIFACT_MANIFEST_PATH": str(artifact_manifest_path.relative_to(project_root))
        if artifact_manifest_path.is_file()
        else "missing",
        "RELEASE_MANIFEST_STATUS": _json_status(release_manifest_path),
        "RELEASE_MANIFEST_PATH": str(release_manifest_path.relative_to(project_root))
        if release_manifest_path.is_file()
        else "missing",
        "ARTIFACT_FIGURES": _list_output_files(project_root, "figures", "*.png"),
        "ARTIFACT_DATA_FILES": _list_output_files(project_root, "data"),
        "FIGURE_COUNT": str(len(FIGURE_SPECS)),
        "FIGURE_REGISTRY_PATH": str(registry_path.relative_to(project_root))
        if registry_path.is_file()
        else "N/A",
        "CONFIG_HASH": config_hash,
        "CONFIG_VERSION": str((manuscript_config.get("paper") or {}).get("version", "0.4")),
        "CONFIG_FIRST_AUTHOR": first_author,
        "CONFIG_KEYWORDS": ", ".join(str(k) for k in keywords) if keywords else "N/A",
        "PYTHON_VERSION": platform.python_version(),
        "PLATFORM": platform.platform(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "FIXTURE_TRACK_COUNT": str(len(FIXTURE_MAPPING)),
        "RESULT_CONTAINER_VERIFY_OK": "true" if verify_report.get("ok") else "false",
        "RESULT_CONTAINER_VERIFY_SAMPLE": str(sample_path),
    }
    variables.update(figure_caption_variables())
    width = figure_width
    variables["FIGURE_INDEX"] = figure_index_markdown()
    variables["FIGURE_BLOCK_RESULTS"] = figure_block_markdown(
        "results", default_width=width
    )
    variables["FIGURE_BLOCK_BENCHMARK_INTERP"] = figure_block_markdown(
        "benchmark_interp", default_width=width
    )
    variables["FIGURE_BLOCK_METHODOLOGY"] = figure_block_markdown(
        "methodology", default_width=width
    )
    variables["FIGURE_BLOCK_SECURITY"] = figure_block_markdown(
        "security", default_width=width
    )
    return variables


def save_variables(variables: dict[str, str], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(variables, indent=2) + "\n", encoding="utf-8")
    return output_path
