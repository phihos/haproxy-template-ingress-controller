"""
Tests for haproxy_template_ic.__main__ module.

This module contains tests for CLI functionality and main application entry point
with the simplified CLI structure (run command only).
"""

import click
import pytest
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch
from click.testing import CliRunner

from haproxy_template_ic.__main__ import cli
from haproxy_template_ic.credentials import validate_k8s_name


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
    # Only run command should be available
    assert "schema" not in result.output
    assert "docs" not in result.output


def test_cli_no_command():
    """Test CLI without any subcommand shows help."""
    runner = CliRunner()
    result = runner.invoke(cli, [])

    # Click shows usage help when no command is provided, which exits with code 0
    # But when there are required subcommands, it exits with code 2
    assert result.exit_code == 2 or result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_help_mentions_configmap_only():
    """Test that CLI help mentions ConfigMap-based configuration."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    # Should mention that settings are now in ConfigMap
    assert "ConfigMap" in result.output or "configmap" in result.output


# =============================================================================
# Run Command Tests
# =============================================================================


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_run_command_with_defaults(mock_run):
    """Test run command with default parameters."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "--configmap-name", "test-config", "--secret-name", "test-credentials"],
    )

    assert result.exit_code == 0
    mock_run.assert_called_once()

    # Check that the CLI options were passed correctly (only bootstrap parameters)
    cli_options = mock_run.call_args[0][0]
    assert cli_options.configmap_name == "test-config"
    assert cli_options.secret_name == "test-credentials"
    # Runtime settings are no longer in CLI options - they're in the ConfigMap


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_run_command_bootstrap_params_only(mock_run):
    """Test run command only accepts bootstrap parameters (configmap and secret names)."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--configmap-name",
            "my-config",
            "--secret-name",
            "my-credentials",
        ],
    )

    assert result.exit_code == 0
    cli_options = mock_run.call_args[0][0]
    assert cli_options.configmap_name == "my-config"
    assert cli_options.secret_name == "my-credentials"
    # Runtime settings are configured via ConfigMap, not CLI


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_run_command_with_env_vars(mock_run):
    """Test run command with environment variables for bootstrap parameters only."""
    runner = CliRunner(
        env={
            "CONFIGMAP_NAME": "env-config",
            "SECRET_NAME": "env-credentials",
        }
    )
    result = runner.invoke(cli, ["run"])

    assert result.exit_code == 0
    cli_options = mock_run.call_args[0][0]
    assert cli_options.configmap_name == "env-config"
    assert cli_options.secret_name == "env-credentials"
    # Runtime settings are configured via ConfigMap, not environment variables


def test_run_command_missing_configmap_name():
    """Test run command without required configmap name."""
    runner = CliRunner()
    result = runner.invoke(cli, ["run"])

    assert result.exit_code == 2
    assert "Missing option" in result.output
    assert "configmap-name" in result.output


def test_run_command_help_mentions_configmap():
    """Test run command help mentions ConfigMap configuration."""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    # Should mention that runtime settings come from ConfigMap
    assert (
        "ConfigMap" in result.output
        or "configmap" in result.output
        or "runtime settings" in result.output
    )


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_run_command_basic_functionality(mock_run):
    """Test that run command executes successfully."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "--configmap-name", "test-config", "--secret-name", "test-credentials"],
    )

    assert result.exit_code == 0
    mock_run.assert_called_once()
    # Tracing is now configured from ConfigMap, not CLI


# =============================================================================
# ConfigMap Name Validation Tests
# =============================================================================


def test_run_command_invalid_configmap_name():
    """Test run command with invalid ConfigMap name."""
    runner = CliRunner()

    # Test with uppercase letters
    result = runner.invoke(cli, ["run", "--configmap-name", "Invalid-Name"])
    assert result.exit_code == 2
    assert "Invalid K8s name format" in result.output

    # Test with invalid characters
    result = runner.invoke(cli, ["run", "--configmap-name", "invalid_name"])
    assert result.exit_code == 2
    assert "Invalid K8s name format" in result.output

    # Test starting with hyphen
    result = runner.invoke(cli, ["run", "--configmap-name", "-invalid"])
    assert result.exit_code == 2
    assert "Invalid K8s name format" in result.output

    # Test ending with hyphen
    result = runner.invoke(cli, ["run", "--configmap-name", "invalid-"])
    assert result.exit_code == 2
    assert "Invalid K8s name format" in result.output


@patch("haproxy_template_ic.__main__.run_operator_loop")
def test_run_command_valid_configmap_names(mock_run):
    """Test run command with valid ConfigMap names."""
    runner = CliRunner()

    valid_names = [
        "valid-name",
        "valid123",
        "123valid",
        "v",  # Single character
        "a1b2c3",
        "my-app-config",
        "haproxy-template-ic-config",
    ]

    for name in valid_names:
        result = runner.invoke(
            cli, ["run", "--configmap-name", name, "--secret-name", "test-credentials"]
        )
        assert result.exit_code == 0, f"Failed for valid name: {name}"


def test_configmap_validation_edge_cases():
    """Test unified Kubernetes name validation edge cases."""

    # Test maximum length (253 characters)
    valid_long_name = "a" * 253
    assert validate_k8s_name(None, None, valid_long_name) == valid_long_name

    # Test too long name (254 characters)
    with pytest.raises(click.BadParameter, match="Invalid K8s name format"):
        validate_k8s_name(None, None, "a" * 254)

    # Test single character names
    assert validate_k8s_name(None, None, "a") == "a"
    assert validate_k8s_name(None, None, "1") == "1"

    # Test empty string
    with pytest.raises(click.BadParameter):
        validate_k8s_name(None, None, "")

    # Test consecutive hyphens (allowed by Kubernetes DNS-1123)
    assert validate_k8s_name(None, None, "valid--name") == "valid--name"

    # Test Unicode/international characters (should fail)
    with pytest.raises(click.BadParameter):
        validate_k8s_name(None, None, "café")


# =============================================================================
# Version Command Tests
# =============================================================================


def test_version_command():
    """Test version command displays version information."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])

    assert result.exit_code == 0
    assert "haproxy-template-ic" in result.output
    # Should contain either version number or "(development)"
    assert "0.1.0" in result.output or "(development)" in result.output


@patch("haproxy_template_ic.__main__.metadata.version")
def test_version_command_development_fallback(mock_version):
    """Test version command fallback when package not found."""

    mock_version.side_effect = PackageNotFoundError()
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])

    assert result.exit_code == 0
    assert "haproxy-template-ic (development)" in result.output
