"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface and application startup logic.
"""

import logging
from dataclasses import dataclass

import click

from haproxy_template_ic.operator import run_operator_loop


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
def main(
    configmap_name: str, healthz_port: int, verbose: int, socket_path: str
) -> None:
    """HAProxy Template IC Operator - Kubernetes operator for HAProxy configuration
    management."""
    setup_logging(verbose)

    # Create CLI options object
    cli_options = CliOptions(
        configmap_name=configmap_name,
        healthz_port=healthz_port,
        verbose=verbose,
        socket_path=socket_path,
    )

    run_operator_loop(cli_options)


if __name__ == "__main__":
    main()
