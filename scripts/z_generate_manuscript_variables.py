#!/usr/bin/env python3
"""Generate manuscript variables for entofile."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


def _template_root(project_root: Path) -> Path | None:
    """Return the template checkout that provides ``infrastructure/``, or None.

    Manuscript-variable injection depends on ``infrastructure.rendering`` from
    the template repository, which a standalone public clone of
    ``github.com/docxology/entofile`` does not ship. Returning None lets ``main``
    fail with a clear message instead of a raw ModuleNotFoundError.
    """
    candidates = (
        project_root,
        *project_root.parents,
        project_root.parent / "template",
        project_root.parent.parent.parent / "template",
    )
    for candidate in candidates:
        if (candidate / "infrastructure").is_dir():
            return candidate
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate manuscript variables for entofile"
    )
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()

    template_root = _template_root(_PROJECT_ROOT)
    if template_root is None:
        sys.stderr.write(
            "Manuscript-variable generation requires the template infrastructure "
            "(infrastructure.rendering.manuscript_injection), which is not present "
            "in a standalone checkout. Run this from a template repository checkout "
            "— see docs/rendering_pipeline.md.\n"
        )
        return 2
    sys.path.insert(0, str(template_root))

    from infrastructure.rendering.manuscript_injection import (
        write_resolved_manuscript_tree,
    )

    from src.artifact_manifest import write_artifact_manifest
    from src.manuscript_variables import generate_variables, save_variables

    variables = generate_variables(
        _PROJECT_ROOT,
        require_analysis_outputs=not args.allow_draft,
    )
    out_path = _PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    save_variables(variables, out_path)
    write_resolved_manuscript_tree(_PROJECT_ROOT, variables)
    write_artifact_manifest(_PROJECT_ROOT)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
