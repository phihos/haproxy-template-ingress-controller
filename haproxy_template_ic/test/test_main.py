"""
Tests for haproxy_template_ic.__main__ module.

This module contains tests for CLI functionality and main application entry point.
"""

from unittest.mock import patch
import logging

from haproxy_template_ic.__main__ import setup_logging


# =============================================================================
# Logging Setup Tests
# =============================================================================


def test_setup_logging_warning_level():
    """Test logging setup with warning level (default)."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(0)
        mock_basic_config.assert_called_once_with(level=logging.WARNING)


def test_setup_logging_debug_level():
    """Test logging setup with debug level."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(2)
        mock_basic_config.assert_called_once_with(level=logging.DEBUG)
