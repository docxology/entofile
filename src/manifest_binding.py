"""Canonical authenticated-context binding for ENTO format 0.5.0.

The binding is a digest of the manifest view that is actually exported. It
intentionally excludes ciphertext digests because those are outputs of the
AEAD operation whose associated data contains this digest. Ciphertext bytes
remain authenticated by GCM and are checked separately by the manifest digest.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import unicodedata
from typing import Any

from .errors import IntegrityError
from .models import Manifest

MANIFEST_BINDING_FORMAT = "0.5.0"
MANIFEST_BINDING_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def manifest_binding_payload(manifest: Manifest) -> dict[str, Any]:
    """Return the canonical manifest projection authenticated by format 0.5.0."""
    payload = manifest.to_dict()
    payload.pop("manifest_binding", None)
    for track in payload["tracks"]:
        track.pop("sha256_ciphertext", None)
    return payload


def canonical_manifest_binding_bytes(manifest: Manifest) -> bytes:
    """Serialize the authenticated projection with a stable UTF-8 encoding."""
    return json.dumps(
        _normalize_numbers(manifest_binding_payload(manifest)),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def _normalize_numbers(value: Any) -> Any:
    """Apply the ENTO numeric canonicalization rule before JSON encoding.

    Resolution values are metadata, not arbitrary-precision scientific data. An
    integral float is represented as an integer (so 256 and 256.0 bind alike);
    all other floats must be finite and are emitted by the strict JSON encoder.
    """
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("manifest binding does not permit non-finite numbers")
        if value == 0.0:
            return 0
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        return {key: _normalize_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_numbers(item) for item in value]
    return value


def compute_manifest_binding(manifest: Manifest) -> str:
    """Compute the lowercase SHA-256 binding for a manifest context."""
    return hashlib.sha256(canonical_manifest_binding_bytes(manifest)).hexdigest()


def validate_manifest_binding(manifest: Manifest) -> None:
    """Validate the required 0.5.0 binding, failing closed on mismatch."""
    if manifest.format_version != MANIFEST_BINDING_FORMAT:
        return
    binding = manifest.manifest_binding
    if binding is None or not MANIFEST_BINDING_PATTERN.fullmatch(binding):
        raise IntegrityError("0.5.0 manifest_binding is missing or malformed")
    expected = compute_manifest_binding(manifest)
    if not hmac.compare_digest(binding, expected):
        raise IntegrityError(
            f"manifest binding mismatch: expected {expected}, got {binding}"
        )
