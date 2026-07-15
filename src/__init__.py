"""ENTO reference implementation (default 0.4.0; 0.2.0/0.3.x compatible).

Public API:
    Container: pack_container, unpack_container, inspect_container, verify_container
    Crypto: encrypt_payload, decrypt_payload, generate_master_key, derive_track_key,
            hkdf_sha256, FORMAT_VERSION, SUPPORTED_FORMAT_VERSIONS
    Models: Manifest, PlainTrack, TrackDescriptor, ObservabilityLevel, ProofExport
    Proof: export_proof, verify_proof_chain, verify_proof_export
    Security: validate_track_id, validate_zip_archive, safe_output_path
"""

from __future__ import annotations

from .container import inspect_container, pack_container, unpack_container, verify_container
from .crypto import (
    FORMAT_VERSION,
    FORMAT_VERSION_LATEST,
    SUPPORTED_FORMAT_VERSIONS,
    decrypt_payload,
    derive_track_key,
    encrypt_payload,
    generate_master_key,
    hkdf_sha256,
)
from .errors import (
    ArtifactError,
    ConfigurationError,
    ContainerError,
    EntofileError,
    IntegrityError,
    ManifestError,
    PipelineError,
)
from .models import Manifest, ObservabilityLevel, PlainTrack, ProofExport, TrackDescriptor
from .proof import export_proof, verify_proof_chain, verify_proof_export
from .security import safe_output_path, validate_track_id, validate_zip_archive

__version__ = "0.4.0"

__all__ = [
    "FORMAT_VERSION",
    "FORMAT_VERSION_LATEST",
    "SUPPORTED_FORMAT_VERSIONS",
    "ArtifactError",
    "ConfigError",
    "ConfigurationError",
    "ContainerError",
    "EntofileError",
    "IntegrityError",
    "Manifest",
    "ManifestError",
    "ObservabilityLevel",
    "PipelineError",
    "PlainTrack",
    "ProofExport",
    "TrackDescriptor",
    "decrypt_payload",
    "derive_track_key",
    "encrypt_payload",
    "export_proof",
    "generate_master_key",
    "hkdf_sha256",
    "inspect_container",
    "pack_container",
    "safe_output_path",
    "unpack_container",
    "validate_track_id",
    "validate_zip_archive",
    "verify_container",
    "verify_proof_chain",
    "verify_proof_export",
]

ConfigError = ConfigurationError
