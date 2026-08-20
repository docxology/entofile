"""Tests for hardware acceleration detection and pipeline crypto hooks."""

from __future__ import annotations

from src import crypto


def test_detect_hardware_acceleration() -> None:
    """Verify detect_hardware_acceleration returns a structured diagnostic report."""
    accel = crypto.detect_hardware_acceleration()
    assert isinstance(accel, dict)
    assert "platform" in accel
    assert "backend" in accel
    assert accel["backend"] == "aes-256-gcm"
    assert "backend_accelerated" in accel
    assert isinstance(accel["backend_accelerated"], bool)
    assert "hardware_aes" in accel
    assert isinstance(accel["hardware_aes"], bool)
