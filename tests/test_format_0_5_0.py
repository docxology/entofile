"""Tests for the current 0.5.0 authenticated-manifest-context profile."""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from src import container, crypto
from src.manifest import manifest_to_json
from src.manifest_binding import (
    canonical_manifest_binding_bytes,
    compute_manifest_binding,
)
from src.models import Manifest, ObservabilityLevel, PlainTrack, TrackDescriptor
from src.proof import export_proof


def _vector_manifest() -> Manifest:
    return Manifest(
        format_version="0.5.0",
        created="2026-01-01T00:00:00Z",
        creator="vector",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(
            TrackDescriptor(
                id="alpha",
                type="ento:spectrogram",
                sha256_plaintext="a" * 64,
                sha256_ciphertext="b" * 64,
                byte_length=7,
                observability=3,
            ),
        ),
    )


def test_0_5_0_profile_contract_and_vector() -> None:
    manifest = _vector_manifest()
    binding = compute_manifest_binding(manifest)
    assert crypto.FORMAT_VERSION == "0.5.0"
    assert crypto.FORMAT_VERSION_LATEST == "0.5.0"
    assert crypto.FORMAT_VERSION_NEXT == "0.5.0"
    assert crypto.requires_manifest_binding("0.5.0") is True
    assert crypto.nonce_size_for("0.5.0") == 12
    assert crypto.pads_payload("0.5.0") is True
    assert canonical_manifest_binding_bytes(manifest).decode() == (
        '{"created":"2026-01-01T00:00:00Z","creator":"vector",'
        '"format_version":"0.5.0","observability_level":3,"tracks":['
        '{"byte_length":7,"id":"alpha","observability":3,'
        '"sha256_plaintext":"' + "a" * 64 + '","type":"ento:spectrogram"}]}'
    )
    assert binding == "b8272d2c7ebba75fce8f095db20c7e2523b0bbd181663947bfd0379d6b6640b7"

    track_key = crypto.derive_track_key(bytes(range(32)), "alpha")
    nonce, tag, ciphertext = crypto.encrypt_payload(
        track_key,
        b"ento-0.5.0-vector",
        _nonce=bytes.fromhex("0102030405060708090a0b0c"),
        format_version="0.5.0",
        track_id="alpha",
        manifest_binding=binding,
    )
    assert tag.hex() == "490b23b8439cabd9edfdef76862717d3"
    assert ciphertext.hex() == "956d6a74edd45f875b2667a6d5bfe57e92"
    assert crypto.decrypt_payload(
        track_key,
        nonce,
        tag,
        ciphertext,
        format_version="0.5.0",
        track_id="alpha",
        manifest_binding=binding,
    ) == b"ento-0.5.0-vector"


def test_0_5_0_requires_binding_at_crypto_boundary() -> None:
    track_key = crypto.derive_track_key(bytes(range(32)), "alpha")
    with pytest.raises(ValueError, match="manifest_binding is required"):
        crypto.encrypt_payload(
            track_key,
            b"payload",
            format_version="0.5.0",
            track_id="alpha",
        )


@pytest.mark.parametrize("export_level", list(ObservabilityLevel))
def test_0_5_0_round_trip_binds_exported_observability_view(
    tmp_path: Path, export_level: ObservabilityLevel
) -> None:
    key = crypto.generate_master_key()
    track = PlainTrack("alpha", "ento:blockchain.proof", b"payload")
    path = tmp_path / f"{int(export_level)}.ento.zip"
    written = container.pack_container(
        path,
        key,
        (track,),
        format_version="0.5.0",
        export_level=export_level,
    )
    manifest, payloads = container.unpack_container(path, key)
    assert manifest.format_version == "0.5.0"
    assert manifest.manifest_binding == compute_manifest_binding(manifest)
    assert written == manifest
    assert manifest == container.inspect_container(path)
    assert payloads == {"alpha": b"payload"}
    assert container.verify_container(path, key, require_integrity=True)["integrity"] == (
        "key-authenticated"
    )


def _rewrite_container(
    source: bytes, manifest: Manifest, *, include_proof: bool = True
) -> bytes:
    source_zip = zipfile.ZipFile(io.BytesIO(source))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as target:
        target.writestr("manifest.json", manifest_to_json(manifest))
        for name in source_zip.namelist():
            if name in {"manifest.json", "proof/chain.json"}:
                continue
            target.writestr(name, source_zip.read(name))
        if include_proof:
            target.writestr(
                "proof/chain.json",
                json.dumps(export_proof(manifest).to_dict(), indent=2, sort_keys=True) + "\n",
            )
    return out.getvalue()


def test_0_5_0_rejects_manifest_mutation_before_decryption(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    track = PlainTrack("alpha", "ento:blockchain.proof", b"payload")
    original = container.pack_container_bytes(key, (track,), format_version="0.5.0")
    raw_manifest = json.loads(zipfile.ZipFile(io.BytesIO(original)).read("manifest.json"))
    raw_manifest["creator"] = "attacker"
    tampered = tmp_path / "tampered.ento.zip"
    tampered.write_bytes(_rewrite_container(original, Manifest.from_dict(raw_manifest)))
    with pytest.raises(ValueError, match="manifest binding mismatch"):
        container.inspect_container(tampered)


def test_0_5_0_rejects_rebound_manifest_under_original_ciphertext(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    track = PlainTrack("alpha", "ento:blockchain.proof", b"payload")
    original = container.pack_container_bytes(key, (track,), format_version="0.5.0")
    raw_manifest = json.loads(zipfile.ZipFile(io.BytesIO(original)).read("manifest.json"))
    raw_manifest["creator"] = "attacker"
    rebound = Manifest.from_dict(raw_manifest)
    rebound = Manifest(
        format_version=rebound.format_version,
        created=rebound.created,
        creator=rebound.creator,
        observability_level=rebound.observability_level,
        tracks=rebound.tracks,
        manifest_binding=compute_manifest_binding(rebound),
    )
    tampered = tmp_path / "rebound.ento.zip"
    tampered.write_bytes(_rewrite_container(original, rebound))
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        container.unpack_container(tampered, key)


def test_0_5_0_relabelled_as_legacy_format_fails_keyed_unpack(tmp_path: Path) -> None:
    key = crypto.generate_master_key()
    track = PlainTrack("alpha", "ento:blockchain.proof", b"payload")
    original = container.pack_container_bytes(key, (track,), format_version="0.5.0")
    raw_manifest = json.loads(zipfile.ZipFile(io.BytesIO(original)).read("manifest.json"))
    raw_manifest["format_version"] = "0.4.0"
    raw_manifest.pop("manifest_binding")
    tampered = tmp_path / "downgraded.ento.zip"
    tampered.write_bytes(_rewrite_container(original, Manifest.from_dict(raw_manifest)))
    with pytest.raises(ValueError, match="authentication tag mismatch"):
        container.unpack_container(tampered, key)


def test_0_5_0_rejects_empty_container(tmp_path: Path) -> None:
    template = Manifest(
        format_version="0.5.0",
        created="2026-01-01T00:00:00Z",
        creator="empty",
        observability_level=ObservabilityLevel.AUDITABLE,
        tracks=(),
    )
    manifest = Manifest(
        format_version=template.format_version,
        created=template.created,
        creator=template.creator,
        observability_level=template.observability_level,
        tracks=template.tracks,
        manifest_binding=compute_manifest_binding(template),
    )
    path = tmp_path / "empty.ento.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", manifest_to_json(manifest))
    with pytest.raises(ValueError, match="at least one track"):
        container.inspect_container(path)


def test_legacy_manifest_binding_field_is_rejected() -> None:
    bound = Manifest(
        format_version="0.5.0",
        created=_vector_manifest().created,
        creator=_vector_manifest().creator,
        observability_level=_vector_manifest().observability_level,
        tracks=_vector_manifest().tracks,
        manifest_binding=compute_manifest_binding(_vector_manifest()),
    )
    raw = bound.to_dict()
    raw["format_version"] = "0.4.0"
    from src.manifest import manifest_from_json

    with pytest.raises(jsonschema.ValidationError):
        manifest_from_json(json.dumps(raw))


def test_0_5_0_binding_is_required_when_legacy_manifest_is_relabelled() -> None:
    raw = _vector_manifest().to_dict()
    raw["format_version"] = "0.5.0"
    from src.manifest import manifest_from_json

    with pytest.raises(jsonschema.ValidationError):
        manifest_from_json(json.dumps(raw))


def test_ciphertext_digest_is_redundant_to_the_0_5_0_binding() -> None:
    manifest = _vector_manifest()
    changed_track = replace(
        manifest.tracks[0], sha256_ciphertext="c" * 64
    )
    changed = replace(manifest, tracks=(changed_track,))
    assert compute_manifest_binding(manifest) == compute_manifest_binding(changed)


def test_0_5_0_rejects_wrong_binding_even_when_shape_is_valid() -> None:
    from src.manifest import manifest_from_json

    raw = _vector_manifest().to_dict()
    raw["manifest_binding"] = "0" * 64
    with pytest.raises(ValueError, match="manifest binding mismatch"):
        manifest_from_json(json.dumps(raw))


def test_canonical_binding_normalizes_integral_numbers_and_unicode() -> None:
    base = _vector_manifest()
    unicode_a = Manifest(
        format_version=base.format_version,
        created=base.created,
        creator="é",
        observability_level=base.observability_level,
        tracks=base.tracks,
    )
    unicode_b = Manifest(
        format_version=base.format_version,
        created=base.created,
        creator="é",
        observability_level=base.observability_level,
        tracks=base.tracks,
    )
    assert compute_manifest_binding(unicode_a) == compute_manifest_binding(unicode_b)
