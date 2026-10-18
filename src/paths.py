"""Typed project and output paths used by ENTO pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Explicit filesystem layout for one ENTO project execution.

    Keeping the layout in one value makes temporary-project tests, alternate output
    roots, and multi-checkout callers use the same path contract as the CLI scripts.
    """

    root: Path
    output: Path

    @classmethod
    def from_root(
        cls, project_root: Path | None = None, *, output_root: Path | None = None
    ) -> ProjectPaths:
        """Construct ProjectPaths from an optional root and output directory."""
        root = (project_root or Path(__file__).resolve().parent.parent).resolve()
        output = (output_root or root / "output").resolve()
        return cls(root=root, output=output)

    @property
    def data(self) -> Path:
        """Path to output/data directory."""
        return self.output / "data"

    @property
    def figures(self) -> Path:
        """Path to output/figures directory."""
        return self.output / "figures"

    @property
    def reports(self) -> Path:
        """Path to output/reports directory."""
        return self.output / "reports"

    @property
    def release(self) -> Path:
        """Path to the release envelope outside the attested output tree."""
        return self.root / "release"

    @property
    def conformance(self) -> Path:
        """Path to output/conformance directory."""
        return self.output / "conformance"

    @property
    def manuscript(self) -> Path:
        """Path to manuscript directory."""
        return self.root / "docs" / "manuscript"

    def report(self, filename: str) -> Path:
        """Resolve a flat JSON report filename under output/reports."""
        if Path(filename).name != filename or not filename.endswith(".json"):
            raise ValueError(f"report filename must be a flat JSON name: {filename!r}")
        return self.reports / filename

    def ensure_output_dirs(self) -> None:
        """Create all required output subdirectories if they do not exist."""
        for directory in (
            self.data,
            self.figures,
            self.reports,
            self.release,
            self.conformance,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def release_manifest_path(project_root: Path) -> Path:
    """Prefer the outer release envelope; read legacy inventories compatibly."""
    current = project_root / "release" / "release_manifest.json"
    if current.exists() or current.is_symlink():
        return current
    return project_root / "output" / "release" / "release_manifest.json"
