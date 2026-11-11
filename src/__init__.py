"""ENTO reference implementation for wire format 0.5.0.

Public API:
    Container: pack_container, unpack_container, inspect_container, verify_container
    Crypto: encrypt_payload, decrypt_payload, generate_master_key, derive_track_key,
            hkdf_sha256, FORMAT_VERSION, SUPPORTED_FORMAT_VERSIONS
    Models: Manifest, PlainTrack, TrackDescriptor, ObservabilityLevel, ProofExport
    Proof: export_proof, verify_proof_chain, verify_proof_export
    Security: validate_track_id, validate_zip_archive, safe_output_path
"""

from __future__ import annotations

from .container import (
    inspect_container,
    pack_container,
    pack_container_stream,
    unpack_container,
    unpack_container_stream,
    verify_container,
)
from .crypto import (
    FORMAT_VERSION,
    SUPPORTED_FORMAT_VERSIONS,
    decrypt_payload,
    derive_track_key,
    detect_hardware_acceleration,
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
from .manifest_binding import compute_manifest_binding
from .models import Manifest, ObservabilityLevel, PlainTrack, ProofExport, TrackDescriptor
from .proof import export_proof, verify_proof_chain, verify_proof_export
from .security import safe_output_path, validate_track_id, validate_zip_archive

__version__ = "0.5.0"

__all__ = [
    "FORMAT_VERSION",
    "SUPPORTED_FORMAT_VERSIONS",
    "ArtifactError",
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
    "compute_manifest_binding",
    "decrypt_payload",
    "derive_track_key",
    "detect_hardware_acceleration",
    "encrypt_payload",
    "export_proof",
    "generate_master_key",
    "hkdf_sha256",
    "inspect_container",
    "pack_container",
    "pack_container_stream",
    "safe_output_path",
    "unpack_container",
    "unpack_container_stream",
    "validate_track_id",
    "validate_zip_archive",
    "verify_container",
    "verify_proof_chain",
    "verify_proof_export",
]
