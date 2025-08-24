"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface with proper subcommand structure
for clear separation between operator mode and utility commands.
"""

from dataclasses import dataclass
from importlib import metadata
from importlib.metadata import PackageNotFoundError

import click

from haproxy_template_ic.constants import (
    DEFAULT_HEALTHZ_PORT,
    DEFAULT_METRICS_PORT,
    DEFAULT_SOCKET_PATH,
)
from haproxy_template_ic.credentials import validate_k8s_name
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
    secret_name: str
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
    type=click.BOOL,
    default=False,
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


@cli.command()
@click.option(
    "-c",
    "--configmap-name",
    envvar="CONFIGMAP_NAME",
    required=True,
    callback=validate_k8s_name,
    help="Name of the Kubernetes ConfigMap used for configuration.",
)
@click.option(
    "-s",
    "--secret-name",
    envvar="SECRET_NAME",
    required=True,
    callback=validate_k8s_name,
    help="Name of the Kubernetes Secret containing HAProxy credentials.",
)
@click.option(
    "--healthz-port",
    envvar="HEALTHZ_PORT",
    default=DEFAULT_HEALTHZ_PORT,
    help="Port for health check endpoint.",
)
@click.option(
    "--socket-path",
    envvar="SOCKET_PATH",
    default=DEFAULT_SOCKET_PATH,
    help="Path for management socket to expose internal state.",
)
@click.option(
    "-m",
    "--metrics-port",
    envvar="METRICS_PORT",
    default=DEFAULT_METRICS_PORT,
    help="Port for Prometheus metrics endpoint.",
)
@click.option(
    "--tracing-enabled",
    envvar="TRACING_ENABLED",
    type=click.BOOL,
    default=False,
    help="Enable distributed tracing with OpenTelemetry.",
)
@click.pass_context
def run(
    ctx: click.Context,
    configmap_name: str,
    secret_name: str,
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
            secret_name=secret_name,
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
