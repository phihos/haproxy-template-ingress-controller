"""
Tests for haproxy_template_ic.__main__ schema and utility commands.

This module contains tests for CLI schema export, validation, and documentation
generation commands.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from haproxy_template_ic.__main__ import main


# =============================================================================
# Schema Export Tests
# =============================================================================


@patch("haproxy_template_ic.schema_export.export_schema_to_file")
def test_export_schema_json_success(mock_export_schema):
    """Test successful schema export to JSON file."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        result = runner.invoke(
            main, ["--configmap-name", "test-config", "--export-schema", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "✅ Configuration schema exported to" in result.output
        assert str(tmp_path) in result.output

        # Verify the function was called with correct arguments
        mock_export_schema.assert_called_once_with(
            output_path=tmp_path,
            format="json",
            include_examples=True,
            include_settings=True,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.schema_export.export_schema_to_file")
def test_export_schema_yaml_success(mock_export_schema):
    """Test successful schema export to YAML file."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        result = runner.invoke(
            main, ["--configmap-name", "test-config", "--export-schema", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "✅ Configuration schema exported to" in result.output

        # Verify YAML format was detected from extension
        mock_export_schema.assert_called_once_with(
            output_path=tmp_path,
            format="yaml",
            include_examples=True,
            include_settings=True,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.schema_export.export_schema_to_file")
def test_export_schema_yml_extension_success(mock_export_schema):
    """Test successful schema export to file with .yml extension."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        result = runner.invoke(
            main, ["--configmap-name", "test-config", "--export-schema", str(tmp_path)]
        )

        assert result.exit_code == 0

        # Verify YAML format was detected from .yml extension
        mock_export_schema.assert_called_once_with(
            output_path=tmp_path,
            format="yaml",
            include_examples=True,
            include_settings=True,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.schema_export.export_schema_to_file")
def test_export_schema_failure(mock_export_schema):
    """Test schema export failure handling."""
    runner = CliRunner()

    # Mock function to raise an exception
    mock_export_schema.side_effect = Exception("Export failed")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        result = runner.invoke(
            main, ["--configmap-name", "test-config", "--export-schema", str(tmp_path)]
        )

        assert result.exit_code == 1  # click.Abort() causes exit code 1
        assert "❌ Failed to export schema: Export failed" in result.output

        # Verify the function was called despite the error
        mock_export_schema.assert_called_once()
    finally:
        tmp_path.unlink(missing_ok=True)


# =============================================================================
# Export All Schemas Tests
# =============================================================================


@patch("haproxy_template_ic.schema_export.export_all_schemas_to_directory")
def test_export_all_schemas_success(mock_export_all):
    """Test successful export of all schemas to directory."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        result = runner.invoke(
            main,
            ["--configmap-name", "test-config", "--export-all-schemas", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert "✅ All schemas exported to" in result.output
        assert str(tmp_path) in result.output

        # Verify the function was called with correct arguments
        mock_export_all.assert_called_once_with(output_dir=tmp_path, format="json")


@patch("haproxy_template_ic.schema_export.export_all_schemas_to_directory")
def test_export_all_schemas_failure(mock_export_all):
    """Test export all schemas failure handling."""
    runner = CliRunner()

    # Mock function to raise an exception
    mock_export_all.side_effect = Exception("Directory export failed")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        result = runner.invoke(
            main,
            ["--configmap-name", "test-config", "--export-all-schemas", str(tmp_path)],
        )

        assert result.exit_code == 1  # click.Abort() causes exit code 1
        assert "❌ Failed to export schemas: Directory export failed" in result.output

        # Verify the function was called despite the error
        mock_export_all.assert_called_once_with(output_dir=tmp_path, format="json")


# =============================================================================
# Config Validation Tests
# =============================================================================


@patch("haproxy_template_ic.schema_export.validate_config_file")
def test_validate_config_valid_no_warnings(mock_validate):
    """Test successful config validation with no warnings."""
    runner = CliRunner()

    # Mock validation result - valid config with no warnings
    mock_validate.return_value = {"valid": True, "errors": [], "warnings": []}

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"test config content")

    try:
        result = runner.invoke(
            main,
            ["--configmap-name", "test-config", "--validate-config", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert f"✅ Configuration file {tmp_path} is valid" in result.output
        assert "⚠️  Warnings:" not in result.output

        # Verify the function was called with correct path
        mock_validate.assert_called_once_with(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.schema_export.validate_config_file")
def test_validate_config_valid_with_warnings(mock_validate):
    """Test successful config validation with warnings."""
    runner = CliRunner()

    # Mock validation result - valid config with warnings
    mock_validate.return_value = {
        "valid": True,
        "errors": [],
        "warnings": ["Warning 1: Unused template", "Warning 2: Deprecated option"],
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"test config content")

    try:
        result = runner.invoke(
            main,
            ["--configmap-name", "test-config", "--validate-config", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert f"✅ Configuration file {tmp_path} is valid" in result.output
        assert "⚠️  Warnings:" in result.output
        assert "- Warning 1: Unused template" in result.output
        assert "- Warning 2: Deprecated option" in result.output

        mock_validate.assert_called_once_with(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.schema_export.validate_config_file")
def test_validate_config_invalid(mock_validate):
    """Test config validation with errors."""
    runner = CliRunner()

    # Mock validation result - invalid config with errors and warnings
    mock_validate.return_value = {
        "valid": False,
        "errors": ["Error 1: Missing required field", "Error 2: Invalid syntax"],
        "warnings": ["Warning 1: Deprecated option"],
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"invalid config content")

    try:
        result = runner.invoke(
            main,
            ["--configmap-name", "test-config", "--validate-config", str(tmp_path)],
        )

        assert result.exit_code == 1  # click.Abort() causes exit code 1
        assert f"❌ Configuration file {tmp_path} is invalid" in result.output
        assert "Errors:" in result.output
        assert "- Error 1: Missing required field" in result.output
        assert "- Error 2: Invalid syntax" in result.output
        assert "Warnings:" in result.output
        assert "- Warning 1: Deprecated option" in result.output

        mock_validate.assert_called_once_with(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.schema_export.validate_config_file")
def test_validate_config_invalid_no_warnings(mock_validate):
    """Test config validation with errors but no warnings."""
    runner = CliRunner()

    # Mock validation result - invalid config with only errors
    mock_validate.return_value = {
        "valid": False,
        "errors": ["Error 1: Critical validation failure"],
        "warnings": [],
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"invalid config content")

    try:
        result = runner.invoke(
            main,
            ["--configmap-name", "test-config", "--validate-config", str(tmp_path)],
        )

        assert result.exit_code == 1
        assert f"❌ Configuration file {tmp_path} is invalid" in result.output
        assert "Errors:" in result.output
        assert "- Error 1: Critical validation failure" in result.output
        assert "Warnings:" not in result.output

        mock_validate.assert_called_once_with(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.schema_export.validate_config_file")
def test_validate_config_exception(mock_validate):
    """Test config validation with exception."""
    runner = CliRunner()

    # Mock function to raise an exception
    mock_validate.side_effect = Exception("Validation error")

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"test config content")

    try:
        result = runner.invoke(
            main,
            ["--configmap-name", "test-config", "--validate-config", str(tmp_path)],
        )

        assert result.exit_code == 1  # click.Abort() causes exit code 1
        assert "❌ Failed to validate configuration: Validation error" in result.output

        mock_validate.assert_called_once_with(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


# =============================================================================
# Documentation Generation Tests
# =============================================================================


@patch("haproxy_template_ic.schema_export.generate_config_documentation")
def test_generate_docs_success(mock_generate_docs):
    """Test successful documentation generation."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        result = runner.invoke(
            main, ["--configmap-name", "test-config", "--generate-docs", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "✅ Configuration documentation generated at" in result.output
        assert str(tmp_path) in result.output

        # Verify the function was called with correct arguments
        mock_generate_docs.assert_called_once_with(
            output_path=tmp_path, include_examples=True
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.schema_export.generate_config_documentation")
def test_generate_docs_failure(mock_generate_docs):
    """Test documentation generation failure handling."""
    runner = CliRunner()

    # Mock function to raise an exception
    mock_generate_docs.side_effect = Exception("Documentation generation failed")

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        result = runner.invoke(
            main, ["--configmap-name", "test-config", "--generate-docs", str(tmp_path)]
        )

        assert result.exit_code == 1  # click.Abort() causes exit code 1
        assert (
            "❌ Failed to generate documentation: Documentation generation failed"
            in result.output
        )

        # Verify the function was called despite the error
        mock_generate_docs.assert_called_once_with(
            output_path=tmp_path, include_examples=True
        )
    finally:
        tmp_path.unlink(missing_ok=True)


# =============================================================================
# Early Exit Behavior Tests
# =============================================================================


@patch("haproxy_template_ic.__main__.run_operator_loop")
@patch("haproxy_template_ic.schema_export.export_schema_to_file")
def test_export_schema_exits_early(mock_export_schema, mock_run_operator):
    """Test that export schema command exits early and doesn't run operator."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        result = runner.invoke(
            main,
            [
                "--configmap-name",
                "test-config",  # Required for main
                "--export-schema",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0

        # Verify schema export was called
        mock_export_schema.assert_called_once()

        # Verify operator was NOT called (early exit)
        mock_run_operator.assert_not_called()
    finally:
        tmp_path.unlink(missing_ok=True)


@patch("haproxy_template_ic.__main__.run_operator_loop")
@patch("haproxy_template_ic.schema_export.validate_config_file")
def test_validate_config_exits_early(mock_validate, mock_run_operator):
    """Test that validate config command exits early and doesn't run operator."""
    runner = CliRunner()

    mock_validate.return_value = {"valid": True, "errors": [], "warnings": []}

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"test config")

    try:
        result = runner.invoke(
            main,
            [
                "--configmap-name",
                "test-config",  # Required for main
                "--validate-config",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0

        # Verify validation was called
        mock_validate.assert_called_once()

        # Verify operator was NOT called (early exit)
        mock_run_operator.assert_not_called()
    finally:
        tmp_path.unlink(missing_ok=True)
