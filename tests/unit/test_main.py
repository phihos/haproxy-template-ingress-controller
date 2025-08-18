"""
Tests for haproxy_template_ic.__main__ module.

This module contains tests for CLI functionality and main application entry point
with the new subcommand structure.
"""

import json
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import click
from click.testing import CliRunner

from haproxy_template_ic.__main__ import cli


# =============================================================================
# CLI Group Tests
# =============================================================================


def test_cli_help():
    """Test main CLI help message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "HAProxy Template IC" in result.output
    assert "run" in result.output
    assert "schema" in result.output
    assert "docs" in result.output


def test_cli_no_command():
    """Test CLI without any subcommand shows help."""
    runner = CliRunner()
    result = runner.invoke(cli, [])

    assert result.exit_code != 0
    assert "Usage:" in result.output


# =============================================================================
# Run Subcommand Tests
# =============================================================================


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_run_command_with_defaults(mock_run_operator_loop):
    """Test run subcommand with default arguments."""
    runner = CliRunner()

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        result = runner.invoke(cli, ["run", "--configmap-name", "test-config"])

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
def test_run_command_with_custom_args(mock_run_operator_loop):
    """Test run subcommand with custom arguments."""
    runner = CliRunner()

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        result = runner.invoke(
            cli,
            [
                "--verbose",
                "--verbose",  # -vv for debug
                "--structured-logging",
                "run",
                "--configmap-name",
                "custom-config",
                "--healthz-port",
                "9000",
                "--socket-path",
                "/custom/socket",
            ],
        )

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify logging setup was called with verbose level 2 (debug) and structured logging
        mock_setup_logging.assert_called_once_with(2, use_json=True)

        # Verify run_operator_loop was called with custom CLI options
        mock_run_operator_loop.assert_called_once()
        args, _ = mock_run_operator_loop.call_args
        cli_options = args[0]

        assert cli_options.configmap_name == "custom-config"
        assert cli_options.healthz_port == 9000
        assert cli_options.verbose == 2
        assert cli_options.socket_path == "/custom/socket"
        assert cli_options.structured_logging is True


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_run_command_with_env_vars(mock_run_operator_loop):
    """Test run subcommand with environment variables."""
    runner = CliRunner()

    env_vars = {"HEALTHZ_PORT": "9999", "VERBOSE": "1", "SOCKET_PATH": "/env/socket"}

    with patch(
        "haproxy_template_ic.__main__.setup_structured_logging"
    ) as mock_setup_logging:
        result = runner.invoke(
            cli, ["run", "--configmap-name", "env-config"], env=env_vars
        )

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


def test_run_command_missing_configmap_name():
    """Test run subcommand without required configmap name."""
    runner = CliRunner()

    result = runner.invoke(cli, ["run"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


@patch("haproxy_template_ic.__main__.run_operator_loop")
@patch("haproxy_template_ic.__main__.initialize_tracing")
@patch("haproxy_template_ic.__main__.shutdown_tracing")
@patch("haproxy_template_ic.__main__.create_tracing_config_from_env")
def test_run_command_with_tracing_enabled(
    mock_create_tracing_config,
    mock_shutdown_tracing,
    mock_initialize_tracing,
    mock_run_operator_loop,
):
    """Test run subcommand with tracing enabled."""
    runner = CliRunner()

    # Mock tracing config
    mock_tracing_config = Mock()
    mock_tracing_config.enabled = False  # Initially disabled from env
    mock_create_tracing_config.return_value = mock_tracing_config

    with patch("haproxy_template_ic.__main__.setup_structured_logging"):
        result = runner.invoke(
            cli,
            [
                "run",
                "--configmap-name",
                "test-config",
                "--tracing-enabled",
            ],
        )

        assert result.exit_code == 0

        # Verify tracing was initialized
        mock_create_tracing_config.assert_called_once()
        mock_initialize_tracing.assert_called_once_with(mock_tracing_config)

        # Verify tracing config was updated to enabled
        assert mock_tracing_config.enabled is True

        # Verify tracing shutdown was called
        mock_shutdown_tracing.assert_called_once()


# =============================================================================
# Schema Subcommand Tests
# =============================================================================


def test_schema_help():
    """Test schema subcommand help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["schema", "--help"])

    assert result.exit_code == 0
    assert "Schema management commands" in result.output
    assert "export" in result.output
    assert "export-all" in result.output
    assert "validate" in result.output


@patch("haproxy_template_ic.__main__._handle_export_schema")
def test_schema_export_command(mock_handle_export):
    """Test schema export subcommand."""
    runner = CliRunner()

    with patch("haproxy_template_ic.__main__.setup_structured_logging"):
        result = runner.invoke(cli, ["schema", "export", "/tmp/schema.json"])

        assert result.exit_code == 0
        mock_handle_export.assert_called_once()
        args = mock_handle_export.call_args[0]
        assert str(args[0]) == "/tmp/schema.json"


@patch("haproxy_template_ic.__main__._handle_export_all_schemas")
def test_schema_export_all_command(mock_handle_export_all):
    """Test schema export-all subcommand."""
    runner = CliRunner()

    with patch("haproxy_template_ic.__main__.setup_structured_logging"):
        result = runner.invoke(cli, ["schema", "export-all", "/tmp/schemas"])

        assert result.exit_code == 0
        mock_handle_export_all.assert_called_once()
        args = mock_handle_export_all.call_args[0]
        assert str(args[0]) == "/tmp/schemas"


@patch("haproxy_template_ic.__main__._handle_validate_config")
def test_schema_validate_command(mock_handle_validate):
    """Test schema validate subcommand."""
    runner = CliRunner()

    with patch("haproxy_template_ic.__main__.setup_structured_logging"):
        with runner.isolated_filesystem():
            # Create a test config file
            with open("test-config.yaml", "w") as f:
                f.write("test: config")

            result = runner.invoke(cli, ["schema", "validate", "test-config.yaml"])

            assert result.exit_code == 0
            mock_handle_validate.assert_called_once()


# =============================================================================
# Docs Subcommand Tests
# =============================================================================


def test_docs_help():
    """Test docs subcommand help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["docs", "--help"])

    assert result.exit_code == 0
    assert "Documentation generation commands" in result.output
    assert "generate" in result.output


@patch("haproxy_template_ic.__main__._handle_generate_docs")
def test_docs_generate_command(mock_handle_generate):
    """Test docs generate subcommand."""
    runner = CliRunner()

    with patch("haproxy_template_ic.__main__.setup_structured_logging"):
        result = runner.invoke(cli, ["docs", "generate", "/tmp/docs.md"])

        assert result.exit_code == 0
        mock_handle_generate.assert_called_once()
        args = mock_handle_generate.call_args[0]
        assert str(args[0]) == "/tmp/docs.md"


# =============================================================================
# Schema and Utility Handler Tests
# =============================================================================


def test_handle_export_schema_json(tmp_path):
    """Test _handle_export_schema with JSON output."""
    from haproxy_template_ic.__main__ import _handle_export_schema

    output_path = tmp_path / "schema.json"

    with patch("haproxy_template_ic.__main__.export_config_schema") as mock_export:
        with patch(
            "haproxy_template_ic.__main__.get_schema_version", return_value="1.0.0"
        ):
            with patch(
                "haproxy_template_ic.__main__.export_settings_schema"
            ) as mock_settings:
                mock_export.return_value = {"type": "object"}
                mock_settings.return_value = {"type": "object"}

                _handle_export_schema(output_path)

                assert output_path.exists()
                with open(output_path) as f:
                    data = json.load(f)
                assert data["schema_version"] == "1.0.0"
                assert "config_schema" in data
                assert "settings_schema" in data


def test_handle_export_schema_yaml(tmp_path):
    """Test _handle_export_schema with YAML output."""
    from haproxy_template_ic.__main__ import _handle_export_schema

    output_path = tmp_path / "schema.yaml"

    with patch("haproxy_template_ic.__main__.export_config_schema") as mock_export:
        with patch(
            "haproxy_template_ic.__main__.get_schema_version", return_value="1.0.0"
        ):
            with patch(
                "haproxy_template_ic.__main__.export_settings_schema"
            ) as mock_settings:
                mock_export.return_value = {"type": "object"}
                mock_settings.return_value = {"type": "object"}

                _handle_export_schema(output_path)

                assert output_path.exists()
                with open(output_path) as f:
                    data = yaml.safe_load(f)
                assert data["schema_version"] == "1.0.0"


def test_handle_export_schema_error():
    """Test _handle_export_schema with error."""
    from haproxy_template_ic.__main__ import _handle_export_schema

    output_path = Path("/invalid/path/schema.json")

    with patch(
        "haproxy_template_ic.__main__.export_config_schema",
        side_effect=RuntimeError("Export error"),
    ):
        with pytest.raises(click.Abort):
            _handle_export_schema(output_path)


def test_handle_export_all_schemas(tmp_path):
    """Test _handle_export_all_schemas."""
    from haproxy_template_ic.__main__ import _handle_export_all_schemas

    output_dir = tmp_path / "schemas"

    with patch("haproxy_template_ic.__main__.export_all_schemas") as mock_export:
        mock_export.return_value = {
            "Config": {"type": "object"},
            "PodSelector": {"type": "object"},
        }

        _handle_export_all_schemas(output_dir)

        assert output_dir.exists()
        assert (output_dir / "config.json").exists()
        assert (output_dir / "podselector.json").exists()


def test_handle_validate_config_valid_yaml(tmp_path):
    """Test _handle_validate_config with valid YAML."""
    from haproxy_template_ic.__main__ import _handle_validate_config

    config_path = tmp_path / "config.yaml"
    config_path.write_text("pod_selector:\n  match_labels:\n    app: haproxy")

    with patch(
        "haproxy_template_ic.__main__.validate_config_against_schema"
    ) as mock_validate:
        mock_validate.return_value = []  # No errors

        _handle_validate_config(config_path)
        mock_validate.assert_called_once()


def test_handle_validate_config_invalid(tmp_path):
    """Test _handle_validate_config with invalid configuration."""
    from haproxy_template_ic.__main__ import _handle_validate_config

    config_path = tmp_path / "config.yaml"
    config_path.write_text("invalid: config")

    with patch(
        "haproxy_template_ic.__main__.validate_config_against_schema"
    ) as mock_validate:
        mock_validate.return_value = ["Field required: pod_selector"]

        with pytest.raises(click.Abort):
            _handle_validate_config(config_path)


def test_handle_generate_docs(tmp_path):
    """Test _handle_generate_docs."""
    from haproxy_template_ic.__main__ import _handle_generate_docs

    output_path = tmp_path / "docs.md"

    with patch("haproxy_template_ic.__main__.get_schema_version", return_value="1.0.0"):
        _handle_generate_docs(output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Schema Version: 1.0.0" in content
        assert "Configuration Reference" in content
