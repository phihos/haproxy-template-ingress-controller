"""
Tests for haproxy_template_ic.__main__ module.

This module contains tests for CLI functionality and main application entry point.
"""

from unittest.mock import patch, MagicMock
import logging
from click.testing import CliRunner

from haproxy_template_ic.__main__ import setup_logging, main


# =============================================================================
# Logging Setup Tests
# =============================================================================


def test_setup_logging_warning_level():
    """Test logging setup with warning level (default)."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(0)
        mock_basic_config.assert_called_once_with(level=logging.WARNING)


def test_setup_logging_info_level():
    """Test logging setup with info level."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(1)
        mock_basic_config.assert_called_once_with(level=logging.INFO)


def test_setup_logging_debug_level():
    """Test logging setup with debug level."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(2)
        mock_basic_config.assert_called_once_with(level=logging.DEBUG)


# =============================================================================
# Main Function Tests
# =============================================================================


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_with_defaults(mock_run_operator_loop):
    """Test main CLI command with default arguments."""
    runner = CliRunner()

    with patch("haproxy_template_ic.__main__.setup_logging") as mock_setup_logging:
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Run CLI with minimal required args
            result = runner.invoke(main, ["--configmap-name", "test-config"])

            # Verify command succeeded
            assert result.exit_code == 0

            # Verify logging setup was called with default verbose level (0)
            mock_setup_logging.assert_called_once_with(0)

            # Verify logger was obtained
            mock_get_logger.assert_called_once_with("haproxy_template_ic.__main__")

            # Verify run_operator_loop was called with correct CLI options
            mock_run_operator_loop.assert_called_once()
            args, _ = mock_run_operator_loop.call_args
            cli_options, logger = args

            assert cli_options.configmap_name == "test-config"
            assert cli_options.healthz_port == 8080  # default
            assert cli_options.verbose == 0  # default
            assert (
                cli_options.socket_path == "/run/haproxy-template-ic/management.sock"
            )  # default
            assert logger == mock_logger


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_with_custom_args(mock_run_operator_loop):
    """Test main CLI command with custom arguments."""
    runner = CliRunner()

    with patch("haproxy_template_ic.__main__.setup_logging") as mock_setup_logging:
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Run CLI with custom args
            result = runner.invoke(
                main,
                [
                    "--configmap-name",
                    "custom-config",
                    "--healthz-port",
                    "9000",
                    "--verbose",
                    "--verbose",  # -vv for debug
                    "--socket-path",
                    "/custom/socket",
                ],
            )

            # Verify command succeeded
            assert result.exit_code == 0

            # Verify logging setup was called with verbose level 2 (debug)
            mock_setup_logging.assert_called_once_with(2)

            # Verify run_operator_loop was called with custom CLI options
            mock_run_operator_loop.assert_called_once()
            args, _ = mock_run_operator_loop.call_args
            cli_options, logger = args

            assert cli_options.configmap_name == "custom-config"
            assert cli_options.healthz_port == 9000
            assert cli_options.verbose == 2
            assert cli_options.socket_path == "/custom/socket"


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_with_env_vars(mock_run_operator_loop):
    """Test main CLI command with environment variables."""
    runner = CliRunner()

    env_vars = {"HEALTHZ_PORT": "9999", "VERBOSE": "1", "SOCKET_PATH": "/env/socket"}

    with patch("haproxy_template_ic.__main__.setup_logging") as mock_setup_logging:
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Run CLI with env vars
            result = runner.invoke(
                main, ["--configmap-name", "env-config"], env=env_vars
            )

            # Verify command succeeded
            assert result.exit_code == 0

            # Verify logging setup was called with env verbose level
            mock_setup_logging.assert_called_once_with(1)

            # Verify run_operator_loop was called with env CLI options
            mock_run_operator_loop.assert_called_once()
            args, _ = mock_run_operator_loop.call_args
            cli_options, logger = args

            assert cli_options.configmap_name == "env-config"
            assert cli_options.healthz_port == 9999
            assert cli_options.verbose == 1
            assert cli_options.socket_path == "/env/socket"
