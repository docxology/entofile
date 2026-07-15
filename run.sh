#!/usr/bin/env bash
# run.sh — convenience script for entofile development
set -euo pipefail
cd "$(dirname "$0")"

cmd="${1:-help}"
shift || true

case "$cmd" in
  sync)
    uv sync --extra dev
    ;;
  lint)
    uv run ruff check src/ scripts/ tests/
    ;;
  typecheck)
    uv run mypy src/
    ;;
  test)
    uv run python scripts/run_tests.py
    ;;
  gates)
    uv run ruff check src/ scripts/ tests/
    uv run mypy src/
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
    uv run python scripts/run_tests.py
    uv run python scripts/ento_analysis.py
    uv run python scripts/generate_conformance_fixtures.py
    uv run python scripts/verify_conformance_fixtures.py
    uv run python scripts/check_figure_layout.py
    uv run python scripts/build_release_bundle.py
    uv run python scripts/check_public_promotion_metadata.py --check
    ;;
  help|*)
    echo "Usage: ./run.sh <command>"
    echo ""
    echo "Development:"
    echo "  sync               Install dependencies (uv sync --extra dev)"
    echo "  lint               Run ruff"
    echo "  typecheck          Run mypy"
    echo "  test               Run pytest with coverage"
    echo "  gates              Run lint + typecheck + test"
    echo ""
    echo "Pipeline:"
    echo "  analysis           Run the benchmark analysis pipeline"
    echo "  conformance        Generate + verify conformance fixtures"
    echo "  figures            Check figure layout"
    echo "  release-bundle     Build the release manifest and checksums"
    echo "  publication-check  Audit publication readiness"
    echo "  promotion-check    Check public promotion metadata"
    echo "  full-pipeline      Run all gates + analysis + conformance + release"
    ;;
esac
