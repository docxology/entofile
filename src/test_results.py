"""Structured pytest and coverage result parsing for project gates."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def parse_test_summary(
    junit_path: Path,
    coverage_path: Path,
    returncode: int,
    *,
    source: str,
) -> dict[str, Any]:
    """Parse JUnit XML and coverage JSON into a fail-closed test summary."""
    if not junit_path.is_file():
        return {
            "all_passed": False,
            "project_coverage": None,
            "collected": 0,
            "source": source,
            "detail": "no junitxml produced",
        }
    try:
        root = ET.parse(junit_path).getroot()
        suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
        tests = sum(int(s.get("tests", 0)) for s in suites)
        failures = sum(int(s.get("failures", 0)) for s in suites)
        errors = sum(int(s.get("errors", 0)) for s in suites)
    except (ET.ParseError, OSError, TypeError, ValueError) as exc:
        return {
            "all_passed": False,
            "project_coverage": None,
            "collected": 0,
            "source": source,
            "detail": f"junitxml parse error: {exc}",
        }

    coverage: float | None = None
    if coverage_path.is_file():
        try:
            coverage = round(
                float(
                    json.loads(coverage_path.read_text(encoding="utf-8"))["totals"][
                        "percent_covered"
                    ]
                ),
                2,
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            coverage = None

    return {
        "all_passed": returncode == 0 and tests > 0 and failures == 0 and errors == 0,
        "project_coverage": coverage,
        "collected": tests,
        "source": source,
        "detail": (
            f"returncode={returncode} tests={tests} "
            f"failures={failures} errors={errors}"
        ),
    }
