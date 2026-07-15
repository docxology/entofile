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
        root = (project_root or Path(__file__).resolve().parent.parent).resolve()
        output = (output_root or root / "output").resolve()
        return cls(root=root, output=output)

    @property
    def data(self) -> Path:
        return self.output / "data"

    @property
    def figures(self) -> Path:
        return self.output / "figures"

    @property
    def reports(self) -> Path:
        return self.output / "reports"

    @property
    def release(self) -> Path:
        return self.output / "release"

    @property
    def conformance(self) -> Path:
        return self.output / "conformance"

    @property
    def manuscript(self) -> Path:
        return self.root / "manuscript"

    def report(self, filename: str) -> Path:
        if Path(filename).name != filename or not filename.endswith(".json"):
            raise ValueError(f"report filename must be a flat JSON name: {filename!r}")
        return self.reports / filename

    def ensure_output_dirs(self) -> None:
        for directory in (
            self.data,
            self.figures,
            self.reports,
            self.release,
            self.conformance,
        ):
            directory.mkdir(parents=True, exist_ok=True)
