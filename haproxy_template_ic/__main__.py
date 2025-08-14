"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface and application startup logic.
"""

import logging
from dataclasses import dataclass

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
def main(
    configmap_name: str,
    healthz_port: int,
    verbose: int,
    socket_path: str,
    metrics_port: int,
    structured_logging: bool,
    tracing_enabled: bool,
) -> None:
    """HAProxy Template IC Operator - Kubernetes operator for HAProxy configuration
    management."""
    setup_structured_logging(verbose, use_json=structured_logging)

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


if __name__ == "__main__":
    main()
