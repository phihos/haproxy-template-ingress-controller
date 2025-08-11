import asyncio
import logging

import click
import kopf
import uvloop
import yaml
from deepdiff import DeepDiff
from kr8s.objects import ConfigMap

from haproxy_template_ic.config import config_from_dict
from haproxy_template_ic.utils import get_current_namespace


# =============================================================================
# Configuration Management
# =============================================================================


async def load_config_from_configmap(configmap):
    """Load configuration from a Kubernetes ConfigMap."""
    return config_from_dict(yaml.load(configmap["data"]["config"], Loader=yaml.CLoader))


async def fetch_configmap(name, namespace):
    """Fetch ConfigMap from Kubernetes cluster."""
    try:
        return await ConfigMap.get(name, namespace=namespace)
    except Exception as e:
        raise kopf.TemporaryError(f'Failed to retrieve ConfigMap "{name}": {e}') from e


async def parse_configmap(configmap, name):
    """Parse configuration from ConfigMap."""
    try:
        return await load_config_from_configmap(configmap)
    except Exception as e:
        raise kopf.TemporaryError(f'Failed to parse ConfigMap "{name}": {e}') from e


# =============================================================================
# Event Handlers
# =============================================================================


def trigger_reload(memo):
    """Signal the operator to reload with updated configuration."""
    memo.config_reload_flag.set_result(None)
    memo.stop_flag.set_result(None)


async def handle_configmap_change(memo, event, name, type, logger, **kwargs):
    """Handle ConfigMap change events."""
    logger.info(f'📋 Configmap "{name}" changed with type {type}.')

    new_config = await load_config_from_configmap(event["object"])
    if memo.config != new_config:
        diff = DeepDiff(memo.config, new_config, verbose_level=2)
        logger.info(f"🔄 Config has changed: {diff}. Reloading...")
        trigger_reload(memo)


async def update_resource_index(param, namespace, name, spec, logger, **kwargs_):
    """Update resource index for tracking."""
    logger.debug(f"📝 Updating index {param} for {namespace}/{name}...")
    return {(namespace, name): spec}


# =============================================================================
# Initialization
# =============================================================================


async def setup_resource_watchers(memo, logger, **kwargs):
    """Set up watchers for Kubernetes resources."""
    for index_name in memo.config.watch_resources:
        kopf.index("pods", id=index_name, param=index_name)(update_resource_index)


async def initialize_configuration(memo, logger, **kwargs):
    """Initialize operator configuration from ConfigMap."""
    configmap_name = memo.configmap_name
    logger.info(f"⚙️ Initializing config from configmap {configmap_name}.")

    namespace = get_current_namespace()
    configmap = await fetch_configmap(configmap_name, namespace)
    memo.config = await parse_configmap(configmap, configmap_name)

    # Set up event handlers
    kopf.on.startup()(setup_resource_watchers)
    kopf.on.event(
        "configmap",
        when=lambda name, namespace, type, **_: (
            name == configmap_name
            and namespace == get_current_namespace()
            and type  # Skip initial invocation
        ),
    )(handle_configmap_change)

    logger.info("✅ Configuration initialized successfully.")


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(verbose_level):
    """Configure logging based on verbosity level."""
    log_levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(level=log_levels.get(verbose_level, logging.DEBUG))


# =============================================================================
# Main Application
# =============================================================================


def create_operator_memo(configmap_name):
    """Create memo object for operator state."""
    loop = uvloop.EventLoopPolicy().new_event_loop()
    stop_flag = asyncio.Future(loop=loop)
    config_reload_flag = asyncio.Future(loop=loop)

    return (
        kopf.Memo(
            stop_flag=stop_flag,
            configmap_name=configmap_name,
            config_reload_flag=config_reload_flag,
        ),
        loop,
        stop_flag,
    )


def run_operator_loop(configmap_name, healthz_port, logger):
    """Run the main operator loop with config reload capability."""
    while True:
        # Set up operator
        kopf.on.startup()(initialize_configuration)
        memo, loop, stop_flag = create_operator_memo(configmap_name)

        # Run operator
        kopf.run(
            clusterwide=True,
            loop=loop,
            liveness_endpoint=f"http://0.0.0.0:{healthz_port}/healthz",
            stop_flag=stop_flag,
            memo=memo,
        )

        # Check if we should exit or reload
        if not memo.config_reload_flag.done():
            break  # Normal shutdown

        logger.info("🔄 Configuration changed. Reinitializing...")

    logger.info("👋 Operator shutdown complete.")


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
    help="Set log level to INFO via -v and DEBUG via -vv. Use numbers when using the env var.",
)
def main(configmap_name, healthz_port, verbose):
    """HAProxy Template IC Operator - Kubernetes operator for HAProxy configuration management."""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    run_operator_loop(configmap_name, healthz_port, logger)


if __name__ == "__main__":
    main()
