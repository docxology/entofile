"""Container verification report tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.analysis import validate_generated_outputs
from src.verification_report import (
    build_container_verification_report,
    write_container_verification_report,
)


def test_container_verification_report_after_pipeline(
    fast_benchmark_project: tuple[Path, object],
) -> None:
    root, cfg = fast_benchmark_project
    from src.analysis import run_benchmark_pipeline

    run_benchmark_pipeline(root, config=cfg)
    path = write_container_verification_report(root)
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert report["sample_count"] >= 1
    assert all(sample.get("ok") for sample in report["samples"])


def test_validate_generated_outputs_requires_verification_report(
    fast_benchmark_project: tuple[Path, object],
) -> None:
    root, cfg = fast_benchmark_project
    from src.analysis import run_benchmark_pipeline

    run_benchmark_pipeline(root, config=cfg)
    result = validate_generated_outputs(root)
    assert result["containers_ok"] is True
    assert result["registry_provenance_ok"] is True


def test_build_report_empty_when_no_samples(tmp_path: Path) -> None:
    report = build_container_verification_report(tmp_path)
    assert report["ok"] is False
    assert report["sample_count"] == 0


def test_report_negative_control_rejects_bad_container(tmp_path: Path) -> None:
    """The report's negative control must report a digest-stripped container as
    rejected, so report ok binds rejection (not just acceptance of good samples)."""

    from src.container import pack_container
    from src.crypto import generate_master_key
    from src.fixtures import load_fixture_tracks
    from src.models import ObservabilityLevel
    from src.verification_report import _negative_control

    key = generate_master_key()
    tracks = load_fixture_tracks(require_all=True)
    bench = tmp_path / "output" / "data" / "_bench_tmp"
    bench.mkdir(parents=True)
    sample = bench / "medium_3.ento.zip"
    pack_container(
        sample, key, tracks, observability_level=ObservabilityLevel.AUDITABLE
    )
    control = _negative_control([sample])
    assert control["available"] is True
    assert control["rejected"] is True
    # Bind the rejection to the injected defect (stripped digests -> keyless
    # integrity "unverified"), not merely "something was rejected" — a verifier
    # that rejects everything would also set rejected:True here, but the
    # positive samples in build_container_verification_report would catch it.
    assert control.get("integrity") == "unverified"


def test_negative_control_craft_failure_fails_closed(tmp_path: Path) -> None:
    """A failure while CRAFTING the tampered container (corrupt source zip) must
    NOT be reported as the control firing. Pre-fix, the crafting steps shared the
    verify except-clause, so a corrupt source returned ``rejected: True`` and the
    gate could pass with zero crypto exercised — the F1 false-assurance class."""

    from src.verification_report import _negative_control

    bad_source = tmp_path / "corrupt.ento.zip"
    bad_source.write_bytes(b"this is not a zip archive")
    control = _negative_control([bad_source])
    assert control["available"] is False
    assert control["rejected"] is False
    assert "could not craft" in str(control["reason"])


def test_negative_control_survives_null_tracks_manifest(tmp_path: Path) -> None:
    """An explicit ``"tracks": null`` in the source manifest must not crash the
    control (dict.get returns None despite the default); crafting proceeds and
    the schema-invalid container is rejected by the verifier."""

    import zipfile

    from src.verification_report import _negative_control

    source = tmp_path / "null_tracks.ento.zip"
    with zipfile.ZipFile(source, "w") as zf:
        zf.writestr("manifest.json", json.dumps({"format_version": "0.4.0", "tracks": None}))
    control = _negative_control([source])
    # Crafting succeeds (no tracks to strip); the verifier must reject the
    # schema-invalid container, so the control fires.
    assert control["available"] is True
    assert control["rejected"] is True


def test_report_builder_records_schema_invalid_sample_as_failure(tmp_path: Path) -> None:
    """A schema-invalid sample must be recorded ok:False (report stays usable),
    not crash the builder with a raw jsonschema error."""

    import zipfile

    bench = tmp_path / "output" / "data" / "_bench_tmp"
    bench.mkdir(parents=True)
    sample = bench / "medium_3.ento.zip"
    with zipfile.ZipFile(sample, "w") as zf:
        zf.writestr("manifest.json", json.dumps({"format_version": "0.4.0", "tracks": None}))
    report = build_container_verification_report(tmp_path)
    assert report["ok"] is False
    assert report["sample_count"] == 1
    assert report["samples"][0]["ok"] is False
    assert "error" in report["samples"][0]
