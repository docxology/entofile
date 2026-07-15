"""Public ENTO domain errors for the breaking API surface."""

from __future__ import annotations


class EntofileError(Exception):
    """Base class for errors intentionally exposed by the ENTO API."""


class ManifestError(EntofileError, ValueError):
    """Manifest JSON/schema/semantic validation failed."""


class ContainerError(EntofileError, ValueError):
    """Container structure or ZIP policy failed."""


class IntegrityError(ContainerError):
    """Authenticated content, digest, proof, or length binding failed."""


class ConfigurationError(EntofileError, ValueError):
    """Project or experiment configuration is invalid."""


class PipelineError(EntofileError):
    """A certifying pipeline stage could not produce its required artifact."""


class ArtifactError(EntofileError):
    """A generated artifact is missing, malformed, stale, unsafe, or inconsistent."""
