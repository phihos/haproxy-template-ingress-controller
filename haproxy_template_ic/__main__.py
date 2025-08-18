"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface and application startup logic.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click

from haproxy_template_ic.operator import run_operator_loop
from haproxy_template_ic.structured_logging import setup_structured_logging
from haproxy_template_ic.tracing import (
    initialize_tracing,
    create_tracing_config_from_env,
    shutdown_tracing,
)


# =============================================================================
# CLI Options
# =============================================================================


@dataclass
class CliOptions:
    """Container for all CLI options."""

    configmap_name: str
    healthz_port: int
    verbose: int
    socket_path: str
    metrics_port: int
    structured_logging: bool
    tracing_enabled: bool


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(verbose_level: int) -> None:
    """Configure logging based on verbosity level."""
    log_levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(level=log_levels.get(verbose_level, logging.DEBUG))


# =============================================================================
# Command Line Interface
# =============================================================================


@click.command()
@click.option(
    "-c",
    "--configmap-name",
    envvar="CONFIGMAP_NAME",
    required=False,
    help="Name of the Kubernetes ConfigMap used for configuration.",
)
@click.option(
    "-h",
    "--healthz-port",
    envvar="HEALTHZ_PORT",
    default=8080,
    help="Port for health check endpoint.",
)
@click.option(
    "-v",
    "--verbose",
    envvar="VERBOSE",
    count=True,
    help="Set log level to INFO via -v and DEBUG via -vv. "
    "Use numbers when using the env var.",
)
@click.option(
    "-s",
    "--socket-path",
    envvar="SOCKET_PATH",
    default="/run/haproxy-template-ic/management.sock",
    help="Path for management socket to expose internal state.",
)
@click.option(
    "-m",
    "--metrics-port",
    envvar="METRICS_PORT",
    default=9090,
    help="Port for Prometheus metrics endpoint.",
)
@click.option(
    "--structured-logging",
    envvar="STRUCTURED_LOGGING",
    is_flag=True,
    help="Enable structured JSON logging output.",
)
@click.option(
    "--tracing-enabled",
    envvar="TRACING_ENABLED",
    is_flag=True,
    help="Enable distributed tracing with OpenTelemetry.",
)
@click.option(
    "--export-schema",
    type=click.Path(),
    help="Export configuration schema to file and exit (supports .json and .yaml).",
)
@click.option(
    "--export-all-schemas",
    type=click.Path(),
    help="Export all schemas to directory and exit.",
)
@click.option(
    "--validate-config",
    type=click.Path(exists=True),
    help="Validate configuration file against schema and exit.",
)
@click.option(
    "--generate-docs",
    type=click.Path(),
    help="Generate configuration documentation and exit.",
)
def main(
    configmap_name: str,
    healthz_port: int,
    verbose: int,
    socket_path: str,
    metrics_port: int,
    structured_logging: bool,
    tracing_enabled: bool,
    export_schema: Optional[Path],
    export_all_schemas: Optional[Path],
    validate_config: Optional[Path],
    generate_docs: Optional[Path],
) -> None:
    """HAProxy Template IC Operator - Kubernetes operator for HAProxy configuration
    management."""
    setup_structured_logging(verbose, use_json=structured_logging)

    # Handle schema and utility commands (exit after execution)
    if export_schema:
        _handle_export_schema(Path(export_schema))
        return

    if export_all_schemas:
        _handle_export_all_schemas(Path(export_all_schemas))
        return

    if validate_config:
        _handle_validate_config(Path(validate_config))
        return

    if generate_docs:
        _handle_generate_docs(Path(generate_docs))
        return

    # Check required configmap_name for operator mode
    if not configmap_name:
        click.echo(
            "❌ Error: Missing option '-c' / '--configmap-name' (required for operator mode).",
            err=True,
        )
        raise click.Abort()

    # Initialize distributed tracing
    tracing_config = create_tracing_config_from_env()
    tracing_config.enabled = tracing_enabled or tracing_config.enabled
    initialize_tracing(tracing_config)

    try:
        # Create CLI options object
        cli_options = CliOptions(
            configmap_name=configmap_name,
            healthz_port=healthz_port,
            verbose=verbose,
            socket_path=socket_path,
            metrics_port=metrics_port,
            structured_logging=structured_logging,
            tracing_enabled=tracing_enabled,
        )

        # Import webhook handlers to register them with kopf
        import haproxy_template_ic.webhook  # noqa: F401

        run_operator_loop(cli_options)
    finally:
        # Ensure tracing is properly shutdown
        shutdown_tracing()


# =============================================================================
# Schema and Utility Command Handlers
# =============================================================================


def _handle_export_schema(output_path: Path) -> None:
    """Handle --export-schema command."""
    import json
    import yaml
    from haproxy_template_ic.config_models import (
        export_config_schema,
        get_schema_version,
    )
    from haproxy_template_ic.settings import export_settings_schema

    try:
        schema_data = {
            "schema_version": get_schema_version(),
            "config_schema": export_config_schema(include_examples=True),
            "settings_schema": export_settings_schema(),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            if output_path.suffix.lower() in [".yaml", ".yml"]:
                yaml.dump(schema_data, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(schema_data, f, indent=2, ensure_ascii=False)

        click.echo(f"✅ Configuration schema exported to {output_path}")
    except Exception as e:
        click.echo(f"❌ Failed to export schema: {e}", err=True)
        raise click.Abort()


def _handle_export_all_schemas(output_dir: Path) -> None:
    """Handle --export-all-schemas command."""
    import json
    from haproxy_template_ic.config_models import export_all_schemas

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        all_schemas = export_all_schemas()

        for schema_name, schema_data in all_schemas.items():
            schema_path = output_dir / f"{schema_name.lower()}.json"
            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(schema_data, f, indent=2, ensure_ascii=False)

        click.echo(f"✅ All schemas exported to {output_dir}")
    except Exception as e:
        click.echo(f"❌ Failed to export schemas: {e}", err=True)
        raise click.Abort()


def _handle_validate_config(config_path: Path) -> None:
    """Handle --validate-config command."""
    import json
    import yaml
    from haproxy_template_ic.config_models import validate_config_against_schema

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == ".json":
                config_data = json.load(f)
            else:
                click.echo(
                    f"❌ Unsupported file format: {config_path.suffix}", err=True
                )
                raise click.Abort()

        errors = validate_config_against_schema(config_data)

        if not errors:
            click.echo(f"✅ Configuration file {config_path} is valid")
        else:
            click.echo(f"❌ Configuration file {config_path} is invalid")
            click.echo("\nErrors:")
            for error in errors:
                click.echo(f"  - {error}")
            raise click.Abort()

    except Exception as e:
        click.echo(f"❌ Failed to validate configuration: {e}", err=True)
        raise click.Abort()


def _handle_generate_docs(output_path: Path) -> None:
    """Handle --generate-docs command."""
    from haproxy_template_ic.config_models import get_schema_version

    try:
        doc_content = f"""# HAProxy Template IC Configuration Reference

Schema Version: {get_schema_version()}

This document provides reference for configuring HAProxy Template IC.

## Configuration Schema

The main configuration is provided via a Kubernetes ConfigMap.

For detailed schema information, use: `haproxy-template-ic --export-schema config-schema.json`

## Validation

Configuration can be validated using:

```bash
haproxy-template-ic --validate-config my-config.yaml
```
"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(doc_content)

        click.echo(f"✅ Configuration documentation generated at {output_path}")
    except Exception as e:
        click.echo(f"❌ Failed to generate documentation: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
