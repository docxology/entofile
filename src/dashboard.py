"""HTML dashboard for ENTO format invariants and benchmark figures."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path

from .benchmark_filters import is_tamper_detected
from .benchmark_io import benchmark_csv_path, load_benchmark_csv
from .experiment_config import load_experiment_config
from .figure_registry import FIGURE_SPECS
from .invariants import all_invariants


def build_dashboard_payload(project_root: Path) -> dict[str, object]:
    cfg = load_experiment_config(project_root)
    invariants = all_invariants(project_root)
    rows = load_benchmark_csv(benchmark_csv_path(project_root))
    tamper_detected = sum(1 for row in rows if is_tamper_detected(row))
    return {
        "project": "entofile",
        "benchmark_repetitions": cfg.benchmark_repetitions,
        "benchmark_rows": len(rows),
        "tamper_detected_rows": tamper_detected,
        "figure_count": len(FIGURE_SPECS),
        "invariants": [
            {
                "name": inv.name,
                "kind": inv.kind,
                "description": inv.description,
                "passed": inv.passed,
            }
            for inv in invariants
        ],
    }


def _figure_gallery_html(project_root: Path) -> str:
    figures_dir = project_root / "output" / "figures"
    blocks: list[str] = []
    for spec in sorted(FIGURE_SPECS, key=lambda s: (s.manuscript_section, s.label)):
        png_path = figures_dir / spec.filename
        if not png_path.is_file():
            continue
        encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
        caption = html.escape(spec.caption)
        label = html.escape(spec.label)
        alt_text = html.escape(
            spec.caption[:240] + ("…" if len(spec.caption) > 240 else "")
        )
        blocks.append(
            "<figure>"
            f"<img src='data:image/png;base64,{encoded}' alt='{alt_text}' "
            "style='max-width:100%;height:auto;border:1px solid #ddd;'/>"
            f"<figcaption><strong>{label}</strong> — {caption}</figcaption>"
            "</figure>"
        )
    if not blocks:
        return "<p>No benchmark figures found. Run <code>scripts/ento_analysis.py</code> first.</p>"
    return "\n".join(blocks)


def render_dashboard_html(project_root: Path, output_path: Path | None = None) -> Path:
    payload = build_dashboard_payload(project_root)
    out = output_path or project_root / "output" / "web" / "dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = html.escape(json.dumps(payload, indent=2))
    gallery = _figure_gallery_html(project_root)
    html_doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>ENTO Dashboard</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;}"
        "figure{margin:2rem 0;} pre{background:#f6f8fa;padding:1rem;overflow:auto;}</style>"
        "</head><body>"
        "<h1>ENTO format dashboard</h1>"
        f"<pre>{summary}</pre>"
        "<h2>Benchmark figures</h2>"
        f"{gallery}"
        "</body></html>"
    )
    out.write_text(html_doc, encoding="utf-8")
    return out


def run_dashboard_build(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parent.parent
    return render_dashboard_html(root)
