"""
Tests for schema export and validation utilities.
"""

import json
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from haproxy_template_ic.config_models import (
    export_config_schema,
    export_all_schemas,
    validate_config_against_schema,
    get_schema_version,
)
from haproxy_template_ic.schema_export import (
    export_schema_to_file,
    export_all_schemas_to_directory,
    validate_config_file,
    generate_config_documentation,
)


class TestConfigSchemaExport:
    """Test configuration schema export functions."""

    def test_export_config_schema_basic(self):
        """Test basic schema export."""
        schema = export_config_schema(include_examples=False)

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "pod_selector" in schema["properties"]
        assert "haproxy_config" in schema["properties"]
        assert "watched_resources" in schema["properties"]
        assert "maps" in schema["properties"]
        assert "template_snippets" in schema["properties"]
        assert "certificates" in schema["properties"]

    def test_export_config_schema_with_examples(self):
        """Test schema export with examples."""
        schema = export_config_schema(include_examples=True)

        assert isinstance(schema, dict)
        properties = schema["properties"]

        # Check for examples in properties
        assert "example" in properties["pod_selector"]
        assert "example" in properties["watched_resources"]
        assert "example" in properties["maps"]
        assert "example" in properties["template_snippets"]
        assert "example" in properties["haproxy_config"]

    def test_export_all_schemas(self):
        """Test exporting all model schemas."""
        schemas = export_all_schemas()

        assert isinstance(schemas, dict)

        # Check that all expected schemas are present
        expected_schemas = [
            "Config",
            "WatchResourceConfig",
            "MapConfig",
            "TemplateSnippet",
            "CertificateConfig",
            "PodSelector",
            "ResourceFilter",
            "RenderedMap",
            "RenderedConfig",
            "RenderedCertificate",
            "TemplateContext",
            "HAProxyConfigContext",
        ]

        for schema_name in expected_schemas:
            assert schema_name in schemas
            assert isinstance(schemas[schema_name], dict)
            assert "properties" in schemas[schema_name]

    def test_get_schema_version(self):
        """Test schema version retrieval."""
        version = get_schema_version()
        assert isinstance(version, str)
        assert version == "1.0.0"

    def test_validate_config_against_schema_valid(self):
        """Test config validation with valid configuration."""
        valid_config = {
            "pod_selector": {
                "match_labels": {"app": "haproxy", "component": "loadbalancer"}
            },
            "haproxy_config": {
                "template": "global\n    daemon\n\ndefaults\n    mode http"
            },
        }

        errors = validate_config_against_schema(valid_config)
        assert errors == []

    def test_validate_config_against_schema_invalid(self):
        """Test config validation with invalid configuration."""
        invalid_config = {
            "pod_selector": {
                "match_labels": {}  # Empty labels not allowed
            },
            "haproxy_config": {
                "template": ""  # Empty template not allowed
            },
        }

        errors = validate_config_against_schema(invalid_config)
        assert len(errors) > 0
        assert any("match_labels cannot be empty" in error for error in errors)

    def test_validate_config_against_schema_missing_required(self):
        """Test config validation with missing required fields."""
        incomplete_config = {
            "haproxy_config": {"template": "global\n    daemon"}
            # Missing required pod_selector
        }

        errors = validate_config_against_schema(incomplete_config)
        assert len(errors) > 0
        assert any("pod_selector" in error for error in errors)


class TestSchemaFileExport:
    """Test file-based schema export functions."""

    def test_export_schema_to_file_json(self):
        """Test exporting schema to JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "schema.json"

            export_schema_to_file(
                output_path=output_path,
                format="json",
                include_examples=True,
                include_settings=True,
            )

            assert output_path.exists()

            with open(output_path, "r") as f:
                data = json.load(f)

            assert "schema_version" in data
            assert "config_schema" in data
            assert "settings_schema" in data
            assert data["schema_version"] == "1.0.0"

    def test_export_schema_to_file_yaml(self):
        """Test exporting schema to YAML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "schema.yaml"

            export_schema_to_file(
                output_path=output_path,
                format="yaml",
                include_examples=True,
                include_settings=False,
            )

            assert output_path.exists()

            with open(output_path, "r") as f:
                data = yaml.safe_load(f)

            assert "schema_version" in data
            assert "config_schema" in data
            assert "settings_schema" not in data  # Excluded

    def test_export_schema_to_file_unsupported_format(self):
        """Test error handling for unsupported format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "schema.xml"

            with pytest.raises(ValueError) as exc_info:
                export_schema_to_file(output_path=output_path, format="xml")
            assert "Unsupported format" in str(exc_info.value)

    def test_export_all_schemas_to_directory(self):
        """Test exporting all schemas to directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "schemas"

            export_all_schemas_to_directory(output_dir=output_dir, format="json")

            assert output_dir.exists()

            # Check that individual schema files were created
            config_file = output_dir / "config.json"
            assert config_file.exists()

            with open(config_file, "r") as f:
                config_schema = json.load(f)
            assert "properties" in config_schema

    def test_validate_config_file_valid_yaml(self):
        """Test validating a valid YAML config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            valid_config = {
                "pod_selector": {
                    "match_labels": {"app": "haproxy", "component": "loadbalancer"}
                },
                "haproxy_config": {
                    "template": "global\n    daemon\n\ndefaults\n    mode http"
                },
            }

            with open(config_path, "w") as f:
                yaml.dump(valid_config, f)

            result = validate_config_file(config_path)

            assert result["valid"] is True
            assert result["errors"] == []
            assert isinstance(result["warnings"], list)

    def test_validate_config_file_invalid_yaml(self):
        """Test validating an invalid YAML config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            invalid_config = {
                "pod_selector": {
                    "match_labels": {}  # Invalid: empty labels
                },
                "haproxy_config": {
                    "template": ""  # Invalid: empty template
                },
            }

            with open(config_path, "w") as f:
                yaml.dump(invalid_config, f)

            result = validate_config_file(config_path)

            assert result["valid"] is False
            assert len(result["errors"]) > 0

    def test_validate_config_file_json(self):
        """Test validating a JSON config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            valid_config = {
                "pod_selector": {"match_labels": {"app": "haproxy"}},
                "haproxy_config": {"template": "global\n    daemon"},
            }

            with open(config_path, "w") as f:
                json.dump(valid_config, f)

            result = validate_config_file(config_path)

            assert result["valid"] is True
            assert result["errors"] == []

    def test_validate_config_file_unsupported_format(self):
        """Test validation error for unsupported file format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.xml"

            with open(config_path, "w") as f:
                f.write("<config></config>")

            result = validate_config_file(config_path)

            assert result["valid"] is False
            assert any("Unsupported file format" in error for error in result["errors"])

    def test_validate_config_file_parse_error(self):
        """Test validation with malformed file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            # Write malformed YAML
            with open(config_path, "w") as f:
                f.write("invalid: yaml: content: [")

            result = validate_config_file(config_path)

            assert result["valid"] is False
            assert any("Failed to parse" in error for error in result["errors"])


class TestConfigurationWarnings:
    """Test configuration warning generation."""

    def test_warnings_for_empty_watched_resources(self):
        """Test warnings for empty watched resources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            config = {
                "pod_selector": {"match_labels": {"app": "haproxy"}},
                "haproxy_config": {"template": "global\n    daemon"},
                "watched_resources": {},  # Empty - should trigger warning
            }

            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = validate_config_file(config_path)

            assert result["valid"] is True
            warnings = result["warnings"]
            assert any(
                "No watched resources configured" in warning for warning in warnings
            )

    def test_warnings_for_unused_snippets(self):
        """Test warnings for unused template snippets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            config = {
                "pod_selector": {"match_labels": {"app": "haproxy"}},
                "haproxy_config": {
                    "template": "global\n    daemon"  # Doesn't use snippet
                },
                "template_snippets": {
                    "unused-snippet": {
                        "name": "unused-snippet",
                        "template": "backend {{ name }}",
                    }
                },
            }

            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = validate_config_file(config_path)

            warnings = result["warnings"]
            assert any(
                "unused-snippet" in warning and "not used" in warning
                for warning in warnings
            )

    def test_warnings_for_missing_health_endpoint(self):
        """Test warnings for missing health endpoint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            config = {
                "pod_selector": {"match_labels": {"app": "haproxy"}},
                "haproxy_config": {
                    "template": "global\n    daemon\n\nfrontend main\n    bind *:80"  # No health endpoint
                },
            }

            with open(config_path, "w") as f:
                yaml.dump(config, f)

            result = validate_config_file(config_path)

            warnings = result["warnings"]
            assert any("health endpoint" in warning for warning in warnings)


class TestDocumentationGeneration:
    """Test configuration documentation generation."""

    def test_generate_config_documentation(self):
        """Test generating configuration documentation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "config-reference.md"

            generate_config_documentation(
                output_path=output_path, include_examples=True
            )

            assert output_path.exists()

            with open(output_path, "r") as f:
                content = f.read()

            # Check for expected sections
            assert "# HAProxy Template IC Configuration Reference" in content
            assert "## Configuration Schema" in content
            assert "## Environment Variables" in content
            assert "## Validation" in content

            # Check for specific configuration fields
            assert "pod_selector" in content
            assert "haproxy_config" in content
            assert "watched_resources" in content

    def test_generate_config_documentation_without_examples(self):
        """Test generating documentation without examples."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "config-reference.md"

            generate_config_documentation(
                output_path=output_path, include_examples=False
            )

            assert output_path.exists()

            with open(output_path, "r") as f:
                content = f.read()

            # Should still have main sections but fewer examples
            assert "# HAProxy Template IC Configuration Reference" in content
            assert "## Configuration Schema" in content


class TestSchemaIntegration:
    """Test integration between different schema components."""

    def test_schema_roundtrip_validation(self):
        """Test that exported schemas can validate example configurations."""
        # Export schema
        schema = export_config_schema(include_examples=True)

        # Get example from schema
        examples = schema.get("json_schema_extra", {}).get("examples", [])
        assert len(examples) > 0

        example_config = examples[0]

        # Validate the example against the schema
        errors = validate_config_against_schema(example_config)
        assert errors == [], f"Example config should be valid, but got errors: {errors}"

    def test_settings_schema_export(self):
        """Test that settings schema can be exported and is valid."""
        from haproxy_template_ic.settings import export_settings_schema

        schema = export_settings_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "configmap_name" in schema["properties"]
        assert "tracing" in schema["properties"]
        assert "webhook" in schema["properties"]

    @patch("haproxy_template_ic.schema_export.yaml.dump")
    def test_documentation_generation_error_handling(self, mock_yaml_dump):
        """Test error handling in documentation generation."""
        mock_yaml_dump.side_effect = Exception("YAML error")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "config-reference.md"

            # Should not raise exception, but handle error gracefully
            with pytest.raises(Exception):
                generate_config_documentation(output_path=output_path)
