"""
Tests for haproxy_template_ic.__main__ module.

This module contains tests for CLI functionality and main application entry point.
"""

from unittest.mock import patch, Mock
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

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        # Run CLI with minimal required args
        result = runner.invoke(main, ["--configmap-name", "test-config"])

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify logging setup was called with default verbose level (0)
        mock_setup_logging.assert_called_once_with(0, use_json=False)

        # Verify run_operator_loop was called with correct CLI options
        mock_run_operator_loop.assert_called_once()
        args, _ = mock_run_operator_loop.call_args
        cli_options = args[0]

        assert cli_options.configmap_name == "test-config"
        assert cli_options.healthz_port == 8080  # default
        assert cli_options.verbose == 0  # default
        assert (
            cli_options.socket_path == "/run/haproxy-template-ic/management.sock"
        )  # default


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_with_custom_args(mock_run_operator_loop):
    """Test main CLI command with custom arguments."""
    runner = CliRunner()

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
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
        mock_setup_logging.assert_called_once_with(2, use_json=False)

        # Verify run_operator_loop was called with custom CLI options
        mock_run_operator_loop.assert_called_once()
        args, _ = mock_run_operator_loop.call_args
        cli_options = args[0]

        assert cli_options.configmap_name == "custom-config"
        assert cli_options.healthz_port == 9000
        assert cli_options.verbose == 2
        assert cli_options.socket_path == "/custom/socket"


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_with_env_vars(mock_run_operator_loop):
    """Test main CLI command with environment variables."""
    runner = CliRunner()

    env_vars = {"HEALTHZ_PORT": "9999", "VERBOSE": "1", "SOCKET_PATH": "/env/socket"}

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        # Run CLI with env vars
        result = runner.invoke(main, ["--configmap-name", "env-config"], env=env_vars)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify logging setup was called with env verbose level
        mock_setup_logging.assert_called_once_with(1, use_json=False)

        # Verify run_operator_loop was called with env CLI options
        mock_run_operator_loop.assert_called_once()
        args, _ = mock_run_operator_loop.call_args
        cli_options = args[0]

        assert cli_options.configmap_name == "env-config"
        assert cli_options.healthz_port == 9999
        assert cli_options.verbose == 1
        assert cli_options.socket_path == "/env/socket"


# =============================================================================
# Additional CLI Options Tests
# =============================================================================


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_with_metrics_port(mock_run_operator_loop):
    """Test main CLI command with custom metrics port."""
    runner = CliRunner()

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        result = runner.invoke(
            main,
            [
                "--configmap-name",
                "test-config",
                "--metrics-port",
                "9091",
            ],
        )

        assert result.exit_code == 0
        mock_setup_logging.assert_called_once_with(0, use_json=False)

        # Verify CLI options contain custom metrics port
        mock_run_operator_loop.assert_called_once()
        args, _ = mock_run_operator_loop.call_args
        cli_options = args[0]

        assert cli_options.metrics_port == 9091


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_with_structured_logging(mock_run_operator_loop):
    """Test main CLI command with structured logging enabled."""
    runner = CliRunner()

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        result = runner.invoke(
            main,
            [
                "--configmap-name",
                "test-config",
                "--structured-logging",
            ],
        )

        assert result.exit_code == 0

        # Verify structured logging was enabled
        mock_setup_logging.assert_called_once_with(0, use_json=True)

        # Verify CLI options contain structured logging flag
        mock_run_operator_loop.assert_called_once()
        args, _ = mock_run_operator_loop.call_args
        cli_options = args[0]

        assert cli_options.structured_logging is True


@patch("haproxy_template_ic.__main__.run_operator_loop")
@patch("haproxy_template_ic.__main__.initialize_tracing")
@patch("haproxy_template_ic.__main__.shutdown_tracing")
@patch("haproxy_template_ic.__main__.create_tracing_config_from_env")
def test_main_cli_with_tracing_enabled(
    mock_create_tracing_config,
    mock_shutdown_tracing,
    mock_initialize_tracing,
    mock_run_operator_loop,
):
    """Test main CLI command with tracing enabled."""
    runner = CliRunner()

    # Mock tracing config
    mock_tracing_config = Mock()
    mock_tracing_config.enabled = False  # Initially disabled from env
    mock_create_tracing_config.return_value = mock_tracing_config

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        result = runner.invoke(
            main,
            [
                "--configmap-name",
                "test-config",
                "--tracing-enabled",
            ],
        )

        assert result.exit_code == 0
        mock_setup_logging.assert_called_once_with(0, use_json=False)

        # Verify tracing was initialized
        mock_create_tracing_config.assert_called_once()
        mock_initialize_tracing.assert_called_once_with(mock_tracing_config)

        # Verify tracing config was updated to enabled
        assert mock_tracing_config.enabled is True

        # Verify tracing shutdown was called
        mock_shutdown_tracing.assert_called_once()

        # Verify CLI options contain tracing flag
        mock_run_operator_loop.assert_called_once()
        args, _ = mock_run_operator_loop.call_args
        cli_options = args[0]

        assert cli_options.tracing_enabled is True


@patch("haproxy_template_ic.__main__.run_operator_loop")
@patch("haproxy_template_ic.__main__.initialize_tracing")
@patch("haproxy_template_ic.__main__.shutdown_tracing")
@patch("haproxy_template_ic.__main__.create_tracing_config_from_env")
def test_main_cli_tracing_already_enabled_in_env(
    mock_create_tracing_config,
    mock_shutdown_tracing,
    mock_initialize_tracing,
    mock_run_operator_loop,
):
    """Test main CLI when tracing is already enabled via environment."""
    runner = CliRunner()

    # Mock tracing config already enabled from environment
    mock_tracing_config = Mock()
    mock_tracing_config.enabled = True  # Already enabled from env
    mock_create_tracing_config.return_value = mock_tracing_config

    with patch("haproxy_template_ic.__main__.setup_structured_logging"):
        result = runner.invoke(
            main,
            [
                "--configmap-name",
                "test-config",
                # No --tracing-enabled flag
            ],
        )

        assert result.exit_code == 0

        # Verify tracing was still initialized (already enabled from env)
        mock_initialize_tracing.assert_called_once_with(mock_tracing_config)

        # Verify tracing config remained enabled
        assert mock_tracing_config.enabled is True

        # Verify tracing shutdown was called
        mock_shutdown_tracing.assert_called_once()


@patch("haproxy_template_ic.__main__.shutdown_tracing")
@patch("haproxy_template_ic.__main__.initialize_tracing")
@patch("haproxy_template_ic.__main__.create_tracing_config_from_env")
@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_tracing_shutdown_on_error(
    mock_run_operator_loop,
    mock_create_tracing_config,
    mock_initialize_tracing,
    mock_shutdown_tracing,
):
    """Test that tracing is properly shutdown even when operator fails."""
    runner = CliRunner()

    # Mock tracing config
    mock_tracing_config = Mock()
    mock_tracing_config.enabled = False
    mock_create_tracing_config.return_value = mock_tracing_config

    # Mock operator to raise an exception
    mock_run_operator_loop.side_effect = Exception("Operator failed")

    with patch("haproxy_template_ic.__main__.setup_structured_logging"):
        result = runner.invoke(
            main,
            [
                "--configmap-name",
                "test-config",
                "--tracing-enabled",
            ],
        )

        # The CLI should handle the exception and still exit cleanly
        # (Click handles exceptions and converts them to exit codes)
        assert result.exit_code != 0

        # Verify tracing was initialized
        mock_initialize_tracing.assert_called_once()

        # Verify tracing shutdown was called despite the error
        mock_shutdown_tracing.assert_called_once()


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_main_cli_all_options_combined(mock_run_operator_loop):
    """Test main CLI command with all options combined."""
    runner = CliRunner()

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        with patch("haproxy_template_ic.__main__.initialize_tracing"):
            with patch("haproxy_template_ic.__main__.shutdown_tracing"):
                with patch(
                    "haproxy_template_ic.__main__.create_tracing_config_from_env"
                ) as mock_create_config:
                    mock_config = Mock()
                    mock_config.enabled = False
                    mock_create_config.return_value = mock_config

                    result = runner.invoke(
                        main,
                        [
                            "--configmap-name",
                            "full-test-config",
                            "--healthz-port",
                            "8888",
                            "--verbose",
                            "--verbose",  # -vv for debug
                            "--socket-path",
                            "/tmp/test.sock",
                            "--metrics-port",
                            "9999",
                            "--structured-logging",
                            "--tracing-enabled",
                        ],
                    )

                    assert result.exit_code == 0

                    # Verify structured logging setup
                    mock_setup_logging.assert_called_once_with(2, use_json=True)

                    # Verify all CLI options
                    mock_run_operator_loop.assert_called_once()
                    args, _ = mock_run_operator_loop.call_args
                    cli_options = args[0]

                    assert cli_options.configmap_name == "full-test-config"
                    assert cli_options.healthz_port == 8888
                    assert cli_options.verbose == 2
                    assert cli_options.socket_path == "/tmp/test.sock"
                    assert cli_options.metrics_port == 9999
                    assert cli_options.structured_logging is True
                    assert cli_options.tracing_enabled is True


def test_setup_logging_invalid_level():
    """Test logging setup with invalid level (should default to DEBUG)."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(99)  # Invalid level
        mock_basic_config.assert_called_once_with(level=logging.DEBUG)


def test_setup_logging_negative_level():
    """Test logging setup with negative level (should default to DEBUG)."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(-1)  # Negative level
        mock_basic_config.assert_called_once_with(level=logging.DEBUG)
