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


@cli.command()
@click.option(
    "-n",
    "--namespace",
    help="Kubernetes namespace where the operator is deployed. If not specified, uses current kubectl context default.",
)
@click.option(
    "--context", help="Kubectl context to use. If not specified, uses current context."
)
@click.option(
    "-r",
    "--refresh",
    default=5,
    type=click.IntRange(1, 60),
    help="Refresh interval in seconds (1-60). Default: 5",
)
@click.option(
    "--deployment-name",
    default="haproxy-template-ic",
    help="Name of the operator deployment. Default: haproxy-template-ic",
)
@click.pass_context
def dashboard(
    ctx: click.Context,
    namespace: str,
    context: str,
    refresh: int,
    deployment_name: str,
) -> None:
    """Launch live status dashboard for monitoring HAProxy Template IC.

    The dashboard provides real-time monitoring of operator status, HAProxy pods,
    template rendering, resource synchronization, and performance metrics.

    The dashboard connects to your Kubernetes cluster using kubectl and displays
    information in a beautiful terminal interface. It automatically detects the
    operator version and adapts its functionality accordingly.

    Examples:
    \b
        # Basic usage with current context
        haproxy-template-ic dashboard

        # Specific namespace and context
        haproxy-template-ic dashboard -n production --context prod-cluster

        # Custom refresh interval
        haproxy-template-ic dashboard -r 3
    """
    import asyncio
    from haproxy_template_ic.dashboard import DashboardLauncher

    # Get namespace from current kubectl context if not provided
    if not namespace:
        try:
            import subprocess

            result = subprocess.run(
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
            namespace = result.stdout.strip() or "default"
        except (subprocess.CalledProcessError, FileNotFoundError):
            namespace = "default"

    # Launch the dashboard
    launcher = DashboardLauncher(
        namespace=namespace,
        context=context,
        refresh_interval=refresh,
        deployment_name=deployment_name,
    )

    try:
        asyncio.run(launcher.launch())
    except KeyboardInterrupt:
        click.echo("\nDashboard stopped by user.")
    except Exception as e:
        click.echo(f"\nDashboard error: {e}", err=True)
        import traceback

        if hasattr(ctx, "obj") and ctx.obj.get("debug", False):
            traceback.print_exc()
        click.echo(
            "Please check your Kubernetes configuration and try again.", err=True
        )
        ctx.exit(1)


if __name__ == "__main__":
    cli()
