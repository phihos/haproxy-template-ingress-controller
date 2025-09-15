"""
Main entry point for HAProxy Template IC.

This module provides the CLI interface with proper subcommand structure
for clear separation between operator mode and utility commands.
"""

import logging
import subprocess  # nosec B404
import sys
from importlib import metadata
from importlib.metadata import PackageNotFoundError

import click

from haproxy_template_ic.core.logging import setup_structured_logging
from haproxy_template_ic.credentials import validate_k8s_name
from haproxy_template_ic.initialization import run_operator_loop
from haproxy_template_ic.k8s.resource_utils import get_current_namespace
from haproxy_template_ic.models.cli import CliOptions

logger = logging.getLogger(__name__)


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


if __name__ == "__main__":
    cli()
