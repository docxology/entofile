#!/usr/bin/env python3
"""Pre-flight check for manuscript rendering prerequisites.

Manuscript rendering is template-integrated: it depends on
``infrastructure.rendering`` from the template repository. A standalone public
clone of ``github.com/docxology/entofile`` does not ship that template, so this
script must fail with a clear, actionable message rather than a raw
``ModuleNotFoundError`` traceback. It locates the template the same way the
sibling render scripts do (search parents for an ``infrastructure/`` directory,
then a sibling ``template`` checkout) and defers the import into ``main``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _template_root(project_root: Path) -> Path | None:
    """Return the template checkout that provides ``infrastructure/``, or None."""
    for candidate in (project_root, *project_root.parents):
        if (candidate / "infrastructure").is_dir():
            return candidate
    sibling_template = project_root.parent.parent.parent / "template"
    if (sibling_template / "infrastructure").is_dir():
        return sibling_template
    return None


def main() -> int:
    template_root = _template_root(_PROJECT_ROOT)
    if template_root is None:
        sys.stderr.write(
            "Manuscript pre-flight requires the template infrastructure "
            "(infrastructure.rendering.preflight), which is not present in a "
            "standalone checkout. Render the manuscript from a template "
            "repository checkout — see docs/rendering_pipeline.md.\n"
        )
        return 2
    sys.path.insert(0, str(template_root))

    from infrastructure.rendering.preflight import run_manuscript_preflight

    manuscript_dir = _PROJECT_ROOT / "manuscript"
    ok, message = run_manuscript_preflight(manuscript_dir)
    if ok:
        return 0
    sys.stderr.write(message)
    return 1


if __name__ == "__main__":
    sys.exit(main())
