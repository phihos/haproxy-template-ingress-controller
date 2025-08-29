"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface with proper subcommand structure
for clear separation between operator mode and utility commands.
"""

from dataclasses import dataclass
from importlib import metadata
from importlib.metadata import PackageNotFoundError

import click

# Constants are now defined in the ConfigMap via the Config model
from haproxy_template_ic.credentials import validate_k8s_name
from haproxy_template_ic.operator import run_operator_loop
from haproxy_template_ic.structured_logging import setup_structured_logging
import haproxy_template_ic.webhook  # Import webhook handlers to register them with kopf  # noqa: F401


# =============================================================================
# CLI Options
# =============================================================================


@dataclass(frozen=True)
class CliOptions:
    """Container for bootstrap CLI options (configmap and secret location)."""

    configmap_name: str
    secret_name: str


# =============================================================================
# Command Line Interface
# =============================================================================


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """HAProxy Template IC - Kubernetes operator for HAProxy configuration management.

    Use 'run' subcommand to start the operator.

    NOTE: Logging, tracing, and other runtime settings are now configured
    via ConfigMap rather than CLI options or environment variables.
    """
    # Initialize context for subcommands
    ctx.ensure_object(dict)

    # Basic logging setup (will be reconfigured from ConfigMap during operator startup)
    setup_structured_logging(verbose_level=0, use_json=False)


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
@click.pass_context
def run(
    ctx: click.Context,
    configmap_name: str,
    secret_name: str,
) -> None:
    """Run the HAProxy Template IC operator.

    This starts the Kubernetes operator that watches resources and manages
    HAProxy configurations via the Dataplane API.

    All runtime settings (logging, tracing, ports, etc.) are now configured
    via the ConfigMap specified by --configmap-name.
    """
    # Create CLI options object (bootstrap parameters only)
    cli_options = CliOptions(
        configmap_name=configmap_name,
        secret_name=secret_name,
    )

    run_operator_loop(cli_options)


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
