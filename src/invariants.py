"""Format invariant checks for ENTO containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .fixtures import load_fixture_tracks
from .container import pack_container, unpack_container
from .crypto import generate_master_key
from .manifest import validate_manifest_dict
from .models import ObservabilityLevel


@dataclass
class InvariantResult:
    name: str
    kind: str
    actual: Any
    expected: Any = None
    tol: float = 1e-9
    description: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Whether the invariant holds, evaluated per ``kind``.

        Single source of truth for pass/fail so consumers (e.g. the dashboard) never
        hardcode it. ``equal`` is exact equality; ``close`` compares numerically within
        ``tol``. An unrecognized kind raises rather than defaulting to True — a silent
        ``True`` for an unevaluated invariant is precisely the green-oracle blindness
        this property exists to prevent.
        """
        if self.kind == "equal":
            return bool(self.actual == self.expected)
        if self.kind == "close":
            return abs(float(self.actual) - float(self.expected)) <= self.tol
        raise ValueError(f"unknown invariant kind: {self.kind!r}")


def round_trip_invariants(project_root: Path) -> list[InvariantResult]:
    key = generate_master_key()
    tracks = load_fixture_tracks(project_root)
    out = project_root / "output" / "data" / "_invariant.ento.zip"
    manifest = pack_container(
        out, key, tracks, observability_level=ObservabilityLevel.AUDITABLE
    )
    _, payloads = unpack_container(out, key)
    results: list[InvariantResult] = []
    for track in tracks:
        results.append(
            InvariantResult(
                name=f"round_trip_{track.track_id}",
                kind="equal",
                actual=payloads[track.track_id],
                expected=track.payload,
                description="Unpack equals original plaintext",
            )
        )
    validate_manifest_dict(manifest.to_dict(), project_root)
    results.append(
        InvariantResult(
            name="manifest_schema_valid",
            kind="equal",
            actual=True,
            expected=True,
            description="Manifest validates against JSON Schema",
        )
    )
    return results


def all_invariants(project_root: Path) -> list[InvariantResult]:
    return round_trip_invariants(project_root)
