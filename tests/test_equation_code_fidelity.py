"""Bind each manuscript equation in ``02d_formal_model.md`` to the code it models.

The cross-reference tests (``test_equation_crossrefs.py``) prove the equations are
*referenced*; these tests prove they are *true of the implementation*. Each test
names the equation label it pins, so a code change that drifts from the stated
formalism fails here rather than silently making the manuscript wrong.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src import crypto, padding
from src.benchmark_stats import TRACK_HEADER_BYTES, expansion_ratio_model
from src.container import pack_container, verify_container
from src.crypto import (
    FORMAT_VERSION,
    MASTER_KEY_SIZE,
    TAG_SIZE,
    derive_track_key,
    generate_master_key,
)
from src.fixtures import load_fixture_tracks
from src.manifest import manifest_to_json
from src.models import ObservabilityLevel, PlainTrack
from src.observability import filter_manifest
from src.track import encrypt_track, parse_track_bytes

# ---- eq:track_key — k_i = HKDF-SHA256(K, "ento:track:" || i) ----------------------


def test_eq_track_key_derivation_matches_formula() -> None:
    """eq:track_key: per-track key is HKDF-SHA256 over the master key with a
    track-binding info label, output length = master-key length (32)."""
    master = generate_master_key()
    k_eeg = derive_track_key(master, "eeg")
    k_vcf = derive_track_key(master, "vcf")
    assert len(k_eeg) == MASTER_KEY_SIZE == 32
    assert k_eeg != k_vcf  # track id bound into derivation
    assert derive_track_key(master, "eeg") == k_eeg  # deterministic
    # The info label is exactly the manuscript's "ento:track:{id}".
    assert k_eeg == crypto.hkdf_sha256(master, MASTER_KEY_SIZE, info=b"ento:track:eeg")


# ---- eq:track_member — member = nonce || tag || ciphertext -----------------------


def test_eq_track_member_byte_layout_matches() -> None:
    """eq:track_member: default 0.4.0 parses as nonce(12) || tag(16) ||
    ciphertext, where ciphertext length is the PADME-padded plaintext length."""
    master = generate_master_key()
    plain = PlainTrack(
        track_id="t", track_type="ento:timeseries.eeg", payload=b"x" * 200
    )
    enc = encrypt_track(master, plain)
    assert len(enc.nonce) == crypto.nonce_size_for(FORMAT_VERSION) == 12
    assert len(enc.tag) == TAG_SIZE == 16
    assert len(enc.ciphertext) == padding.padme(len(plain.payload) + 8)
    # Round-trip through the concatenated wire layout in eq:track_member order.
    parsed = parse_track_bytes("t", enc.nonce + enc.tag + enc.ciphertext)
    assert (parsed.nonce, parsed.tag, parsed.ciphertext) == (
        enc.nonce,
        enc.tag,
        enc.ciphertext,
    )


# ---- eq:expansion_law — version-aware expansion model ----------------------------


def test_eq_expansion_law_total_bytes_equals_model() -> None:
    """eq:expansion_law: default 0.4.0 stored member size is header plus PADME
    padded plaintext, and the ratio equals expansion_ratio_model(n)."""
    assert TRACK_HEADER_BYTES == crypto.nonce_size_for(FORMAT_VERSION) + TAG_SIZE == 28
    master = generate_master_key()
    for n in (1, 42, 64, 1000):
        enc = encrypt_track(
            master,
            PlainTrack(track_id="t", track_type="ento:spectrogram", payload=b"z" * n),
        )
        total = len(enc.nonce) + len(enc.tag) + len(enc.ciphertext)
        assert total == TRACK_HEADER_BYTES + padding.padme(n + 8)
        assert (total / n) == pytest.approx(expansion_ratio_model(n))


# ---- eq:integrity_levels — the three-way integrity function -----------------------


def _pack_tmp(tmp_path: Path, key: bytes, export_level: ObservabilityLevel) -> Path:
    fixtures = load_fixture_tracks(require_all=True)
    out = tmp_path / "c.ento.zip"
    pack_container(
        out,
        key,
        fixtures,
        creator="entofile",
        observability_level=ObservabilityLevel.AUDITABLE,
        export_level=export_level,
    )
    return out


def test_eq_integrity_levels_key_authenticated(tmp_path: Path) -> None:
    """eq:integrity_levels branch 1: key supplied + tags verify -> key-authenticated."""
    key = generate_master_key()
    container = _pack_tmp(tmp_path, key, ObservabilityLevel.AUDITABLE)
    result = verify_container(container, key)
    assert result["integrity"] == "key-authenticated"
    assert result["ok"] is True


def test_eq_integrity_levels_digest_only(tmp_path: Path) -> None:
    """eq:integrity_levels branch 2: no key, digests present -> digest-only."""
    key = generate_master_key()
    container = _pack_tmp(tmp_path, key, ObservabilityLevel.AUDITABLE)
    result = verify_container(container)  # keyless
    assert result["integrity"] == "digest-only"
    assert result["ciphertext_digests_present"] is True


def test_eq_integrity_levels_unverified_fails_closed(tmp_path: Path) -> None:
    """eq:integrity_levels branch 3: no key, digests absent (sealed) -> unverified,
    and require_integrity makes ok=False (fail closed)."""
    key = generate_master_key()
    container = _pack_tmp(tmp_path, key, ObservabilityLevel.SEALED)
    assert verify_container(container)["integrity"] == "unverified"
    strict = verify_container(container, require_integrity=True)
    assert strict["integrity"] == "unverified"
    assert strict["ok"] is False


# ---- eq:observability_monotone — |mu_l1| <= |mu_l2| for l1 <= l2 ------------------


def test_eq_observability_monotone_holds_on_fixtures() -> None:
    """eq:observability_monotone: exported manifest size is non-decreasing in the
    observability level under the current URI registry."""
    key = generate_master_key()
    fixtures = load_fixture_tracks(require_all=True)
    # pack_container returns the FULL internal manifest; redact it per level.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        full = pack_container(
            Path(td) / "c.zip",
            key,
            fixtures,
            observability_level=ObservabilityLevel.AUDITABLE,
        )
    levels = [
        ObservabilityLevel.SEALED,
        ObservabilityLevel.TYPED,
        ObservabilityLevel.RESOLVED,
        ObservabilityLevel.AUDITABLE,
    ]
    sizes = [
        len(manifest_to_json(filter_manifest(full, lvl)).encode("utf-8"))
        for lvl in levels
    ]
    assert sizes == sorted(sizes), f"monotonicity violated: {list(zip(levels, sizes, strict=False))}"
    assert sizes[0] < sizes[-1]  # redaction actually removes bytes


# ---- eq:container_map — typed, heterogeneous, many-track (omnitrack) ---------------


def test_eq_container_map_is_typed_and_heterogeneous() -> None:
    """eq:container_map: a single container binds many independently-typed tracks."""
    fixtures = load_fixture_tracks(require_all=True)
    ids = {t.track_id for t in fixtures}
    types = {t.track_type for t in fixtures}
    assert len(ids) >= 3
    assert len(types) >= 3, f"expected heterogeneous track types, got {types}"
