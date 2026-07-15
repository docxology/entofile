"""Tests for manuscript variable generation."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.analysis import run_benchmark_pipeline
from src.manuscript_variables import generate_variables, save_variables

_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})
_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def test_generate_variables_after_analysis(
    fast_benchmark_project: tuple[Path, object],
) -> None:
    root, cfg = fast_benchmark_project
    run_benchmark_pipeline(root, config=cfg)
    variables = generate_variables(root, require_analysis_outputs=True, config=cfg)
    assert variables["FORMAT_VERSION"] == "0.4.0"
    assert variables["FORMAT_DEFAULT_HEADER_BYTES"] == "28"
    assert variables["FORMAT_DEFAULT_PADS"] == "yes"
    assert variables["FORMAT_VERSIONS_COMPATIBILITY"] == "0.2.0, 0.3.0 and 0.3.1"
    assert variables["FORMAT_VERSION_NEXT"] == "0.5.0"
    assert variables["FORMAT_VERSIONS_FORWARD"] == "0.5.0"
    assert variables["FORMAT_NEXT_AAD_TEMPLATE"] == (
        "ento:0.5.0:manifest:{manifest_binding}:track:{track_id}"
    )
    assert variables["COUNT_FORWARD_FORMATS"] == "1"
    assert variables["RESULT_BENCHMARK_ROWS"] != "N/A"
    assert variables["RESULT_AVG_UNPACK_SECONDS"] != "N/A"
    assert variables["FIXTURE_EEG_SHA256"] != "N/A"
    assert variables["BENCHMARK_CSV_SHA256"] != "N/A"
    assert variables["RESULT_MANIFEST_BYTES_L3"] != "N/A"
    assert variables["SBOM_STATUS"] in {"present", "missing"}
    assert "SBOM_PATH" in variables
    assert variables["NO_MOCK_STATUS"] != "N/A"
    assert variables["FIXTURE_INPUT_CLASSIFICATION"] == "committed deterministic fixture inputs"
    assert variables["BENCHMARK_STRESS_INPUT_CLASSIFICATION"] == "generated synthetic throughput stress track"
    assert variables["CONFORMANCE_INPUT_CLASSIFICATION"] == "deterministic test-vector containers"
    assert variables["EXECUTION_EVIDENCE_CLASSIFICATION"] == "real ZIP, crypto, filesystem, and render execution outputs"
    assert "CONFORMANCE_REPORT_STATUS" in variables
    assert "ARTIFACT_MANIFEST_STATUS" in variables
    assert "RELEASE_MANIFEST_STATUS" in variables
    assert variables["COUNT_SUPPORTED_FORMATS"] == "5"
    assert variables["COUNT_COMPATIBILITY_FORMATS"] == "3"
    assert variables["CONFIG_BENCHMARK_REPETITIONS"] == "3"
    assert variables["CONFIG_BENCHMARK_PILOT_REPETITIONS"] == "3"
    assert variables["CONFIG_BENCHMARK_REPETITION_SCALE"] == "1"
    assert variables["RESULT_ROWS_PER_REPETITION"] == "16"
    assert variables["RESULT_EXPECTED_BENCHMARK_ROWS"] == "48"
    assert variables["RESULT_BENCHMARK_ROWS"] == "48"
    out = root / "output" / "data" / "manuscript_variables.json"
    save_variables(variables, out)
    assert out.exists()


def test_throughput_dispersion_tokens_present_and_consistent(
    fast_benchmark_project: tuple[Path, object],
) -> None:
    """The dispersion layer's tokens are produced and the CI brackets the mean."""
    root, cfg = fast_benchmark_project
    run_benchmark_pipeline(root, config=cfg)
    v = generate_variables(root, require_analysis_outputs=True, config=cfg)
    for token in (
        "RESULT_THROUGHPUT_N",
        "RESULT_THROUGHPUT_SD_MIB_S",
        "RESULT_THROUGHPUT_CV_PERCENT",
        "RESULT_THROUGHPUT_DF",
        "RESULT_THROUGHPUT_CI_METHOD",
        "RESULT_THROUGHPUT_CI95_LO_MIB_S",
        "RESULT_THROUGHPUT_CI95_HI_MIB_S",
    ):
        assert v[token] != "N/A", f"{token} not produced"
    lo = float(v["RESULT_THROUGHPUT_CI95_LO_MIB_S"])
    hi = float(v["RESULT_THROUGHPUT_CI95_HI_MIB_S"])
    mean = float(v["RESULT_AVG_THROUGHPUT_MIB_S"])
    assert lo <= mean <= hi  # CI brackets the mean
    assert int(v["RESULT_THROUGHPUT_N"]) >= 2
    assert int(v["RESULT_THROUGHPUT_DF"]) == int(v["RESULT_THROUGHPUT_N"]) - 1
    assert "Student-t" in v["RESULT_THROUGHPUT_CI_METHOD"]


def test_require_analysis_outputs_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        generate_variables(tmp_path, require_analysis_outputs=True)


def test_all_manuscript_tokens_are_generated() -> None:
    """Every {{TOKEN}} in manuscript/*.md must be produced by generate_variables()."""
    project_root = Path(__file__).resolve().parent.parent
    produced = set(generate_variables(project_root))
    manuscript_dir = project_root / "manuscript"
    if not manuscript_dir.is_dir():
        pytest.skip("manuscript/ directory not found")

    unresolved: dict[str, list[str]] = {}
    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in _DOC_ONLY:
            continue
        text = md_file.read_text(encoding="utf-8")
        for token in _TOKEN_RE.findall(text):
            if token not in produced:
                unresolved.setdefault(token, []).append(md_file.name)

    assert not unresolved, (
        "Manuscript tokens not produced by generate_variables():\n"
        + "\n".join(
            f"  {{{{{{t}}}}}}: {files}" for t, files in sorted(unresolved.items())
        )
    )
