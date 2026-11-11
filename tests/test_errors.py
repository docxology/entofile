"""Public exception hierarchy contract."""

from __future__ import annotations

import pytest

import src
from src.errors import (
    ArtifactError,
    ConfigurationError,
    ContainerError,
    EntofileError,
    IntegrityError,
    ManifestError,
    PipelineError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        ArtifactError,
        ConfigurationError,
        ContainerError,
        IntegrityError,
        ManifestError,
        PipelineError,
    ],
)
def test_public_domain_errors_share_stable_root(error_type: type[Exception]) -> None:
    assert issubclass(error_type, EntofileError)


@pytest.mark.parametrize(
    "error_type",
    [ConfigurationError, ContainerError, IntegrityError, ManifestError],
)
def test_domain_errors_are_not_value_errors(error_type: type[Exception]) -> None:
    assert not issubclass(error_type, ValueError)


def test_compatibility_exports_are_absent() -> None:
    for name in (
        "ConfigError",
        "FORMAT_VERSION_LATEST",
        "FORMAT_VERSION_NEXT",
        "FORMAT_VERSION_PREVIOUS",
    ):
        assert not hasattr(src, name)
