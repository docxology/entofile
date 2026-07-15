"""Public exception hierarchy and compatibility-alias contract."""

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


def test_compatibility_config_error_is_public_and_value_error_compatible() -> None:
    assert src.ConfigError is ConfigurationError
    assert issubclass(src.ConfigError, ValueError)


def test_integrity_and_configuration_boundaries_remain_value_error_compatible() -> None:
    assert issubclass(IntegrityError, ValueError)
    assert issubclass(ConfigurationError, ValueError)
