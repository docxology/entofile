"""Structured container verification reports for analysis gates."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import jsonschema

from .container import verify_container


def _benchmark_samples(project_root: Path) -> list[Path]:
    bench_dir = project_root / "output" / "data" / "_bench_tmp"
    if not bench_dir.is_dir():
        return []
    preferred = bench_dir / "medium_3.ento.zip"
    if preferred.is_file():
        return [preferred]
    return sorted(
        p
        for p in bench_dir.glob("*.ento.zip")
        if p.is_file() and p.name != "bad.ento.zip"
    )


def build_container_verification_report(project_root: Path) -> dict[str, object]:
    """Verify benchmark ENTO ZIP samples without a master key."""
    samples = _benchmark_samples(project_root)
    results: list[dict[str, object]] = []
    for sample in samples:
        entry: dict[str, object] = {"path": str(sample.relative_to(project_root))}
        try:
            # Keyless, fail-closed: an unverifiable (digest-stripped) sample must
            # not pass the gate. This report establishes "digest-only" integrity —
            # accidental-corruption detection. Adversarial tamper detection is
            # proven separately by the key-based benchmark (tamper_detection_rate).
            outcome = verify_container(sample, require_integrity=True)
            entry.update(outcome)
        except (ValueError, OSError, jsonschema.ValidationError) as exc:
            # ValidationError: verify_container surfaces a schema-invalid
            # manifest as a raw jsonschema error; that is a refusal of the
            # container, not a report-builder crash.
            entry["ok"] = False
            entry["error"] = str(exc)
        results.append(entry)
    # Negative control: the report above proves good samples verify; this proves a
    # known-bad (digest-stripped) container is REJECTED, so the gate binds rejection,
    # not merely acceptance (shape-only gates pass while a regression that returns
    # ok:True for an unverifiable container would slip through unnoticed).
    negative_control = _negative_control(samples)

    ok = (
        bool(results)
        and all(bool(row.get("ok")) for row in results)
        and bool(negative_control.get("rejected"))
    )
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sample_count": len(results),
        "integrity_basis": "digest-only (keyless); adversarial integrity requires the master key",
        "negative_control": negative_control,
        "ok": ok,
        "samples": results,
    }


def _negative_control(samples: list[Path]) -> dict[str, object]:
    """Build a digest-stripped container from a good sample and assert keyless
    fail-closed verification REJECTS it (``ok`` False under ``require_integrity``).

    Returns ``{"rejected": bool, ...}``. ``rejected`` is True only when the crafted
    bad container is correctly refused; if no sample is available to derive one,
    ``available`` is False and the control does not gate (nothing to test).
    """
    if not samples:
        return {
            "available": False,
            "rejected": False,
            "reason": "no sample to derive a negative control",
        }
    source = samples[0]
    # Crafting and verifying are SEPARATE failure domains. A failure while
    # CRAFTING the tampered container (corrupt source zip, malformed manifest
    # JSON, "tracks": null) means no negative control ever ran — reporting it
    # as ``rejected: True`` would let the gate pass with zero crypto exercised,
    # the same F1 false-assurance class this report exists to close. Craft
    # failures therefore fail CLOSED (``rejected: False``).
    try:
        with zipfile.ZipFile(source, "r") as zin:
            members = {name: zin.read(name) for name in zin.namelist()}
        manifest = json.loads(members["manifest.json"].decode("utf-8"))
        # Strip every ciphertext digest -> integrity becomes "unverified" keyless.
        # ``or []`` (not a .get default): an explicit ``"tracks": null`` returns
        # None from .get even with a default, and must not crash the control.
        for track in manifest.get("tracks") or []:
            track["sha256_ciphertext"] = ""
            track["sha256_plaintext"] = ""
        members["manifest.json"] = (json.dumps(manifest)).encode("utf-8")
        # A stripped manifest has no proof binding; drop the now-stale proof member.
        members.pop("proof/chain.json", None)
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zout:
            for name, data in members.items():
                zout.writestr(name, data)
        buf.seek(0)
        tmp = source.parent / "_negative_control.ento.zip"
        tmp.write_bytes(buf.getvalue())
    except (
        zipfile.BadZipFile,
        ValueError,
        OSError,
        KeyError,
        TypeError,
        AttributeError,
    ) as exc:
        return {
            "available": False,
            "rejected": False,
            "reason": f"could not craft negative control: {exc}",
        }
    try:
        outcome = verify_container(tmp, require_integrity=True)
        rejected = not bool(outcome.get("ok"))
        return {
            "available": True,
            "rejected": rejected,
            "integrity": outcome.get("integrity"),
        }
    except (ValueError, OSError, KeyError, jsonschema.ValidationError) as exc:
        # A raised error on the crafted bad container IS a valid rejection: the
        # verifier refused the tampered bytes (schema refusal included).
        return {
            "available": True,
            "rejected": True,
            "reason": f"rejected by exception: {exc}",
        }
    finally:
        tmp.unlink(missing_ok=True)


def write_container_verification_report(project_root: Path) -> Path:
    """Write ``output/reports/container_verification.json``."""
    report = build_container_verification_report(project_root)
    path = project_root / "output" / "reports" / "container_verification.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def containers_verification_ok(project_root: Path, *, live: bool = True) -> bool:
    """Return whether container verification passes.

    Defaults to ``live=True``: this is the named "is the crypto verified" surface, so
    it RE-RUNS the verification this call (decrypt + negative control) rather than
    trusting a possibly-stale or hand-forged on-disk report — closing the last
    side-file-trust residual. Pass ``live=False`` only for a pure display read of an
    already-produced report.
    """
    from .output_gates import container_verification_report_ok

    return container_verification_report_ok(project_root, live=live)
