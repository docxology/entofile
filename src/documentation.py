"""API reference builder for entofile."""

from __future__ import annotations

from pathlib import Path


def build_api_reference_markdown(project_root: Path | None = None) -> str:
    root = project_root or Path(__file__).resolve().parent.parent
    return (
        "# entofile API reference\n\n"
        "Core modules under `src/`:\n\n"
        "- `crypto` — AES-256-GCM, HKDF-SHA256 per-track derivation "
        "(default format 0.5.0; compatibility 0.2.0/0.3.0/0.3.1/0.4.0)\n"
        "- `container` — ZIP pack/unpack\n"
        "- `manifest` — JSON Schema validation\n"
        "- `benchmarks` — throughput and tamper benchmarks\n"
        f"\nProject root: `{root}`\n"
    )


def run_api_doc_generation(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parent.parent
    out = root / "output" / "docs" / "api_reference.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_api_reference_markdown(root), encoding="utf-8")
    return out
