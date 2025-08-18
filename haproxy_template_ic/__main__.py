"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface with proper subcommand structure
for clear separation between operator mode and utility commands.
"""

from dataclasses import dataclass
from pathlib import Path

import click

from haproxy_template_ic.operator import run_operator_loop
from haproxy_template_ic.structured_logging import setup_structured_logging
from haproxy_template_ic.tracing import (
    initialize_tracing,
    create_tracing_config_from_env,
    shutdown_tracing,
)
from haproxy_template_ic.config_models import (
    export_config_schema,
    export_all_schemas,
    validate_config_against_schema,
    get_schema_version,
)
from haproxy_template_ic.settings import export_settings_schema


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
# Command Line Interface
# =============================================================================


@click.group()
@click.option(
    "-v",
    "--verbose",
    envvar="VERBOSE",
    count=True,
    help="Set log level to INFO via -v and DEBUG via -vv. "
    "Use numbers when using the env var.",
)
@click.option(
    "--structured-logging",
    envvar="STRUCTURED_LOGGING",
    is_flag=True,
    help="Enable structured JSON logging output.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: int,
    structured_logging: bool,
) -> None:
    """HAProxy Template IC - Kubernetes operator for HAProxy configuration management.

    Use 'run' subcommand to start the operator, 'schema' for validation/export,
    or 'docs' for documentation generation.
    """
    # Store common options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["structured_logging"] = structured_logging

    # Setup logging with common options
    setup_structured_logging(verbose, use_json=structured_logging)


@cli.command()
@click.option(
    "-c",
    "--configmap-name",
    envvar="CONFIGMAP_NAME",
    required=True,
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
    "--tracing-enabled",
    envvar="TRACING_ENABLED",
    is_flag=True,
    help="Enable distributed tracing with OpenTelemetry.",
)
@click.pass_context
def run(
    ctx: click.Context,
    configmap_name: str,
    healthz_port: int,
    socket_path: str,
    metrics_port: int,
    tracing_enabled: bool,
) -> None:
    """Run the HAProxy Template IC operator.

    This starts the Kubernetes operator that watches resources and manages
    HAProxy configurations via the Dataplane API.
    """
    # Get common options from parent context
    verbose = ctx.obj["verbose"]
    structured_logging = ctx.obj["structured_logging"]

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
# Schema Management Commands
# =============================================================================


@cli.group()
def schema() -> None:
    """Schema management commands for configuration validation and export."""
    pass


@schema.command()
@click.argument("output_path", type=click.Path())
def export(output_path: str) -> None:
    """Export configuration schema to file.

    Supports both JSON and YAML formats based on file extension.

    Examples:
        haproxy-template-ic schema export config-schema.json
        haproxy-template-ic schema export config-schema.yaml
    """
    _handle_export_schema(Path(output_path))


@schema.command("export-all")
@click.argument("output_dir", type=click.Path())
def export_all(output_dir: str) -> None:
    """Export all schemas to directory.

    Creates separate JSON files for each schema type.

    Example:
        haproxy-template-ic schema export-all ./schemas/
    """
    _handle_export_all_schemas(Path(output_dir))


@schema.command()
@click.argument("config_path", type=click.Path(exists=True))
def validate(config_path: str) -> None:
    """Validate configuration file against schema.

    Supports both YAML and JSON configuration files.

    Examples:
        haproxy-template-ic schema validate my-config.yaml
        haproxy-template-ic schema validate config.json
    """
    _handle_validate_config(Path(config_path))


# =============================================================================
# Documentation Commands
# =============================================================================


@cli.group()
def docs() -> None:
    """Documentation generation commands."""
    pass


@docs.command()
@click.argument("output_path", type=click.Path())
def generate(output_path: str) -> None:
    """Generate configuration documentation.

    Creates comprehensive documentation for configuration schema.

    Example:
        haproxy-template-ic docs generate CONFIG.md
    """
    _handle_generate_docs(Path(output_path))


# =============================================================================
# Schema and Utility Command Handlers
# =============================================================================


def _handle_export_schema(output_path: Path) -> None:
    """Handle schema export command."""
    import json
    import yaml

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
    """Handle export all schemas command."""
    import json

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
    """Handle configuration validation command."""
    import json
    import yaml

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
    """Handle documentation generation command."""

    try:
        doc_content = f"""# HAProxy Template IC Configuration Reference

Schema Version: {get_schema_version()}

This document provides reference for configuring HAProxy Template IC.

## Configuration Schema

The main configuration is provided via a Kubernetes ConfigMap.

For detailed schema information, use: `haproxy-template-ic schema export config-schema.json`

## Validation

Configuration can be validated using:

```bash
haproxy-template-ic schema validate my-config.yaml
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
    cli()
