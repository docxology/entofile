#!/usr/bin/env bash
# run.sh — convenience script for entofile development
set -euo pipefail
cd "$(dirname "$0")"

run_no_mocks() {
  local matches status first_test_file
  if [ ! -d tests/ ]; then
    echo "tests directory missing" >&2
    return 2
  fi
  first_test_file="$(find tests/ -type f -name '*.py' -print -quit)"
  if [ -z "$first_test_file" ]; then
    echo "no Python test files" >&2
    return 2
  fi
  if matches="$(grep -R -n -E --include='*.py' 'unittest\.mock|from unittest import mock|MagicMock|AsyncMock|PropertyMock|Mock\(|@patch|patch\.object|mock\.patch|create_autospec|monkeypatch|MonkeyPatch' tests/)"; then
    printf '%s\n' "$matches" >&2
    echo "Mock-based tests are prohibited; use real fixtures and execution paths." >&2
    return 1
  else
    status=$?
    if [ "$status" -ne 1 ]; then
      return "$status"
    fi
  fi
  echo "Clean"
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  sync)
    uv sync --locked --extra dev
    ;;
  lint)
    uv run ruff check src/ scripts/ tests/
    ;;
  typecheck)
    uv run mypy src/
    ;;
  no-mocks)
    run_no_mocks
    ;;
  test)
    uv run python scripts/run_tests.py
    ;;
  gates)
    uv run ruff check src/ scripts/ tests/
    uv run mypy src/
    run_no_mocks
    uv run python scripts/run_tests.py
    ;;
  analysis)
    uv run python scripts/ento_analysis.py
    ;;
  conformance)
    uv run python scripts/generate_conformance_fixtures.py
    uv run python scripts/verify_conformance_fixtures.py
    ;;
  figures)
    uv run python scripts/check_figure_layout.py
    ;;
  release-bundle)
    uv run python scripts/build_release_bundle.py
    ;;
  publication-check)
    uv run python scripts/audit_publication_readiness.py --check
    ;;
  promotion-check)
    uv run python scripts/check_public_promotion_metadata.py --check
    ;;
  full-pipeline)
    uv run ruff check src/ scripts/ tests/
    uv run mypy src/
    run_no_mocks
    uv run python scripts/ento_analysis.py
    uv run python scripts/generate_conformance_fixtures.py
    uv run python scripts/verify_conformance_fixtures.py
    uv run python scripts/check_figure_layout.py
    uv run python scripts/build_dashboard.py
    uv run python scripts/generate_api_docs.py
    uv run python scripts/export_sbom.py
    uv run python scripts/build_release_bundle.py
    uv run python scripts/run_tests.py
    uv run python scripts/build_release_bundle.py
    uv run python scripts/check_public_promotion_metadata.py --check
    ;;
  help|*)
    echo "Usage: ./run.sh <command>"
    echo ""
    echo "Development:"
    echo "  sync               Install locked development dependencies"
    echo "  lint               Run ruff"
    echo "  typecheck          Run mypy"
    echo "  no-mocks           Fail if Python tests use prohibited mocks"
    echo "  test               Run pytest with coverage"
    echo "  gates              Run lint + typecheck + no-mocks + test"
    echo ""
    echo "Pipeline:"
    echo "  analysis           Run the benchmark analysis pipeline"
    echo "  conformance        Generate + verify conformance fixtures"
    echo "  figures            Check figure layout"
    echo "  release-bundle     Build the release manifest and checksums"
    echo "  publication-check  Audit publication readiness"
    echo "  promotion-check    Check public promotion metadata"
    echo "  full-pipeline      Run standalone checks with existing rendered artifacts"
    ;;
esac
