"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface with proper subcommand structure
for clear separation between operator mode and utility commands.
"""

import re
from dataclasses import dataclass
from importlib import metadata
from importlib.metadata import PackageNotFoundError

import click

from haproxy_template_ic.operator import run_operator_loop
from haproxy_template_ic.structured_logging import setup_structured_logging
from haproxy_template_ic.tracing import (
    initialize_tracing,
    create_tracing_config_from_env,
    shutdown_tracing,
)
import haproxy_template_ic.webhook  # Import webhook handlers to register them with kopf  # noqa: F401


# =============================================================================
# CLI Options
# =============================================================================


@dataclass(frozen=True)
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

    Use 'run' subcommand to start the operator.
    """
    # Store common options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["structured_logging"] = structured_logging

    # Setup logging with common options
    setup_structured_logging(verbose, use_json=structured_logging)


def validate_configmap_name(
    _ctx: click.Context, _param: click.Parameter, value: str
) -> str:
    """Validate ConfigMap name follows Kubernetes naming conventions.

    Kubernetes names must follow DNS-1123 subdomain specification:
    - Be lowercase
    - Contain only alphanumeric characters and hyphens
    - Start and end with alphanumeric characters
    - Be at most 253 characters long (DNS-1123 limit)
    """
    if len(value) > 253:
        raise click.BadParameter("ConfigMap name must be at most 253 characters long")

    # Fixed regex: allows single chars and properly handles 2+ character names
    if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", value):
        raise click.BadParameter(
            "ConfigMap name must follow Kubernetes naming conventions: "
            "lowercase alphanumeric characters or hyphens, starting and ending with alphanumeric"
        )

    return value


@cli.command()
@click.option(
    "-c",
    "--configmap-name",
    envvar="CONFIGMAP_NAME",
    required=True,
    callback=validate_configmap_name,
    help="Name of the Kubernetes ConfigMap used for configuration.",
)
@click.option(
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

        run_operator_loop(cli_options)
    finally:
        # Ensure tracing is properly shutdown
        shutdown_tracing()


@cli.command()
def version() -> None:
    """Display the application version."""
    try:
        app_version = metadata.version("haproxy-template-ic")
        click.echo(f"haproxy-template-ic {app_version}")
    except PackageNotFoundError:
        click.echo("haproxy-template-ic (development)")


if __name__ == "__main__":
    cli()
