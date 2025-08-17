"""
Schema export utilities for HAProxy Template IC configuration.

This module provides utilities for exporting JSON schemas, generating documentation,
and validating configuration files against schemas.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, Literal

from .config_models import (
    export_config_schema,
    export_all_schemas,
    validate_config_against_schema,
    get_schema_version,
)
from .settings import export_settings_schema


def export_schema_to_file(
    output_path: Path,
    format: Literal["json", "yaml"] = "json",
    include_examples: bool = True,
    include_settings: bool = True,
) -> None:
    """
    Export configuration schemas to a file.

    Args:
        output_path: Path to write the schema file
        format: Output format (json or yaml)
        include_examples: Whether to include example values
        include_settings: Whether to include application settings schema
    """
    schema_data = {
        "schema_version": get_schema_version(),
        "config_schema": export_config_schema(include_examples=include_examples),
    }

    if include_settings:
        schema_data["settings_schema"] = export_settings_schema()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        if format == "json":
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        elif format == "yaml":
            yaml.dump(schema_data, f, default_flow_style=False, sort_keys=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


def export_all_schemas_to_directory(
    output_dir: Path, format: Literal["json", "yaml"] = "json"
) -> None:
    """
    Export all individual schemas to separate files in a directory.

    Args:
        output_dir: Directory to write schema files
        format: Output format (json or yaml)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    all_schemas = export_all_schemas()

    for schema_name, schema_data in all_schemas.items():
        filename = f"{schema_name.lower()}.{format}"
        schema_path = output_dir / filename

        with open(schema_path, "w", encoding="utf-8") as f:
            if format == "json":
                json.dump(schema_data, f, indent=2, ensure_ascii=False)
            elif format == "yaml":
                yaml.dump(schema_data, f, default_flow_style=False)


def validate_config_file(config_path: Path) -> Dict[str, Any]:
    """
    Validate a configuration file against the schema.

    Args:
        config_path: Path to the configuration file to validate

    Returns:
        dict: Validation result with 'valid', 'errors', and 'warnings' keys
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == ".json":
                config_data = json.load(f)
            else:
                return {
                    "valid": False,
                    "errors": [f"Unsupported file format: {config_path.suffix}"],
                    "warnings": [],
                }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to parse configuration file: {e}"],
            "warnings": [],
        }

    # Validate against schema
    validation_errors = validate_config_against_schema(config_data)

    # Generate warnings for best practices
    warnings = _generate_config_warnings(config_data)

    return {
        "valid": len(validation_errors) == 0,
        "errors": validation_errors,
        "warnings": warnings,
    }


def _generate_config_warnings(config_data: Dict[str, Any]) -> list[str]:
    """Generate configuration warnings for best practices."""
    warnings = []

    # Check for common configuration issues
    if "watched_resources" in config_data:
        watched = config_data["watched_resources"]
        if not watched:
            warnings.append(
                "No watched resources configured - controller will not process any Kubernetes resources"
            )

        # Check for webhook validation best practices
        webhook_enabled_count = sum(
            1
            for resource in watched.values()
            if resource.get("enable_validation_webhook", False)
        )
        if webhook_enabled_count == 0:
            warnings.append(
                "No resources have webhook validation enabled - consider enabling for critical resources"
            )

    if "maps" in config_data:
        maps = config_data["maps"]
        if not maps:
            warnings.append(
                "No HAProxy maps configured - consider adding maps for dynamic routing"
            )

        # Check for required map files based on common patterns
        map_paths = set(maps.keys())
        recommended_maps = {
            "/etc/haproxy/maps/host.map",
            "/etc/haproxy/maps/path-exact.map",
        }
        missing_maps = recommended_maps - map_paths
        if missing_maps:
            warnings.append(
                f"Consider adding commonly used maps: {', '.join(missing_maps)}"
            )

    if "template_snippets" in config_data:
        snippets = config_data["template_snippets"]
        if snippets:
            # Check if snippets are used in templates
            haproxy_template = config_data.get("haproxy_config", {}).get("template", "")
            map_templates = [
                map_config.get("template", "")
                for map_config in config_data.get("maps", {}).values()
            ]

            all_templates = [haproxy_template] + map_templates
            for snippet_name in snippets.keys():
                used = any(
                    f'{{% include "{snippet_name}" %}}' in template
                    for template in all_templates
                )
                if not used:
                    warnings.append(
                        f"Template snippet '{snippet_name}' is defined but not used"
                    )

    # Check HAProxy configuration best practices
    haproxy_config = config_data.get("haproxy_config", {})
    if haproxy_config:
        template = haproxy_config.get("template", "")
        if "/healthz" not in template:
            warnings.append(
                "HAProxy template should include health endpoint for readiness probes"
            )
        if "bind *:8404" not in template:
            warnings.append(
                "HAProxy template should bind to port 8404 for health checks"
            )

    return warnings


def generate_config_documentation(
    output_path: Path, include_examples: bool = True
) -> None:
    """
    Generate comprehensive configuration documentation.

    Args:
        output_path: Path to write the documentation (markdown format)
        include_examples: Whether to include configuration examples
    """
    schema = export_config_schema(include_examples=include_examples)
    settings_schema = export_settings_schema()

    # Generate markdown documentation
    doc_content = _generate_markdown_documentation(
        schema, settings_schema, include_examples
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc_content)


def _generate_markdown_documentation(
    config_schema: Dict[str, Any],
    settings_schema: Dict[str, Any],
    include_examples: bool,
) -> str:
    """Generate markdown documentation from schemas."""
    lines = [
        "# HAProxy Template IC Configuration Reference",
        "",
        f"Schema Version: {get_schema_version()}",
        "",
        "This document provides comprehensive reference for configuring HAProxy Template IC.",
        "",
        "## Table of Contents",
        "",
        "- [Configuration Schema](#configuration-schema)",
        "- [Environment Variables](#environment-variables)",
        "- [Examples](#examples)" if include_examples else "",
        "- [Validation](#validation)",
        "",
    ]

    # Configuration Schema section
    lines.extend(
        [
            "## Configuration Schema",
            "",
            "The main configuration is provided via a Kubernetes ConfigMap with the following structure:",
            "",
            "```yaml",
            "apiVersion: v1",
            "kind: ConfigMap",
            "metadata:",
            "  name: haproxy-template-ic-config",
            "data:",
            "  config: |",
            "    # Configuration goes here",
            "```",
            "",
        ]
    )

    # Add property documentation
    properties = config_schema.get("properties", {})
    for prop_name, prop_schema in properties.items():
        lines.extend(_format_property_documentation(prop_name, prop_schema))

    # Environment Variables section
    lines.extend(
        [
            "## Environment Variables",
            "",
            "Runtime behavior can be configured using environment variables:",
            "",
        ]
    )

    # Add settings documentation
    settings_properties = settings_schema.get("properties", {})
    for prop_name, prop_schema in settings_properties.items():
        env_name = prop_name.upper()
        description = prop_schema.get("description", "")
        prop_type = prop_schema.get("type", "string")
        default = prop_schema.get("default")

        lines.append(f"### `{env_name}`")
        lines.append("")
        lines.append(f"- **Type**: {prop_type}")
        if default is not None:
            lines.append(f"- **Default**: `{default}`")
        lines.append(f"- **Description**: {description}")
        lines.append("")

    # Validation section
    lines.extend(
        [
            "## Validation",
            "",
            "Configuration can be validated using the built-in schema validation:",
            "",
            "```bash",
            "# Export schema for validation tools",
            "haproxy-template-ic --export-schema config-schema.json",
            "",
            "# Validate a configuration file",
            "haproxy-template-ic --validate-config my-config.yaml",
            "```",
            "",
        ]
    )

    return "\n".join(line for line in lines if line is not None)


def _format_property_documentation(
    prop_name: str, prop_schema: Dict[str, Any]
) -> list[str]:
    """Format property documentation for markdown."""
    lines = [f"### `{prop_name}`", ""]

    description = prop_schema.get("description", "")
    prop_type = prop_schema.get("type", "object")

    lines.append(f"- **Type**: {prop_type}")
    lines.append(f"- **Description**: {description}")

    # Add required/optional info
    if prop_schema.get("required", False):
        lines.append("- **Required**: Yes")
    else:
        lines.append("- **Required**: No")

    # Add default value if present
    default = prop_schema.get("default")
    if default is not None:
        lines.append(f"- **Default**: `{default}`")

    # Add example if present
    example = prop_schema.get("example")
    if example is not None:
        lines.extend(
            [
                "",
                "**Example**:",
                "",
                "```yaml",
                yaml.dump({prop_name: example}).strip(),
                "```",
            ]
        )

    lines.append("")
    return lines
