"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface with proper subcommand structure
for clear separation between operator mode and utility commands.
"""

import asyncio
import logging
import os
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from importlib import metadata
from importlib.metadata import PackageNotFoundError
from typing import Optional

import click

from haproxy_template_ic.credentials import validate_k8s_name
from haproxy_template_ic.core.logging import setup_structured_logging
from haproxy_template_ic.k8s import get_current_namespace
from haproxy_template_ic.operator import run_operator_loop
from haproxy_template_ic.tui import TuiLauncher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CliOptions:
    """Container for bootstrap CLI options (configmap and secret location)."""

    configmap_name: str
    secret_name: str


def _get_namespace_fallback() -> str:
    """Get namespace from kubectl context as fallback."""
    try:
        result = subprocess.run(  # nosec B603, B607
            [
                "kubectl",
                "config",
                "view",
                "--minify",
                "--output",
                "jsonpath={.contexts[0].context.namespace}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or "default"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "default"


def _detect_namespace(namespace: str) -> str:
    """Detect the namespace using multiple fallback methods."""
    if namespace:
        return namespace

    try:
        return get_current_namespace()
    except Exception:
        return _get_namespace_fallback()


def _cleanup_console_loggers() -> None:
    """Remove console handlers from root logger."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            if handler.stream in (sys.stderr, sys.stdout):
                root_logger.removeHandler(handler)


def _detect_socket_path(socket_path: Optional[str]) -> Optional[str]:
    """Detect management socket path with fallbacks."""
    if socket_path:
        return socket_path

    socket_path = os.environ.get("MANAGEMENT_SOCKET_PATH")
    if socket_path:
        return socket_path

    default_socket = "/run/haproxy-template-ic/management.sock"
    if os.path.exists(default_socket):
        return default_socket

    return None


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """HAProxy Template IC - Kubernetes operator for HAProxy configuration management.

    Use 'run' subcommand to start the operator.

    Logging, tracing, and other runtime settings are configured
    via ConfigMap rather than CLI options or environment variables.
    """
    ctx.ensure_object(dict)

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


@cli.command()
@click.option(
    "-n",
    "--namespace",
    default="",
    help="Kubernetes namespace to monitor. Defaults to current kubectl context namespace.",
)
@click.option(
    "--context",
    default=None,
    help="Kubernetes context to use. Defaults to current kubectl context.",
)
@click.option(
    "-r",
    "--refresh",
    default=5,
    help="Refresh interval in seconds. Default: 5",
)
@click.option(
    "--deployment-name",
    default="haproxy-template-ic",
    help="Name of the operator deployment. Default: haproxy-template-ic",
)
@click.option(
    "--socket-path",
    default=None,
    help="Path to management socket for direct connection. Auto-detects if running in container.",
)
@click.pass_context
def tui(
    ctx: click.Context,
    namespace: str,
    context: str,
    refresh: int,
    deployment_name: str,
    socket_path: Optional[str],
) -> None:
    """Launch Textual TUI dashboard for monitoring HAProxy Template IC.

    The TUI dashboard provides a modern terminal user interface for real-time
    monitoring of operator status, HAProxy pods, template rendering, resource
    synchronization, and performance metrics.

    This is an alternative to the Rich-based dashboard with better interactivity,
    reactive data updates, and a more organized widget-based architecture.

    Examples:
    \b
        # Basic usage with current context
        haproxy-template-ic tui

        # Specific namespace and context
        haproxy-template-ic tui -n production --context prod-cluster

        # Custom refresh interval
        haproxy-template-ic tui -r 3
    """
    namespace = _detect_namespace(namespace)
    _cleanup_console_loggers()
    socket_path = _detect_socket_path(socket_path)

    launcher = TuiLauncher(
        namespace=namespace,
        context=context,
        refresh_interval=refresh,
        deployment_name=deployment_name,
        socket_path=socket_path,
    )

    try:
        asyncio.run(launcher.launch())
    except KeyboardInterrupt:
        logger.info("TUI dashboard terminated by user")
    except Exception as e:
        logger.error(f"TUI dashboard failed: {e}")
        ctx.exit(1)


if __name__ == "__main__":
    cli()
