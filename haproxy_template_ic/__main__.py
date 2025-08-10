import asyncio
import logging

import click
import kopf
import uvloop
from deepdiff import DeepDiff
from kr8s.objects import ConfigMap

from haproxy_template_ic.config import config_from_dict
from haproxy_template_ic.utils import get_current_namespace


def signal_reload(memo):
    """Shut down the operator, but signal the main() loop to restart is again with updated config."""
    memo.config_reload_flag.set_result(None)
    memo.stop_flag.set_result(
        None
    )  # see kopf._cogs.aiokits.aioadapters about how to raise stop-flags


async def check_config_change(memo, event, name, type, logger, **kwargs):
    logger.info(f'Configmap "{name}" changed with type {type}.')
    config = config_from_dict(event["object"]["data"])
    if memo.config != config:
        logger.info(
            f"Config has changed: {DeepDiff(memo.config, config, verbose_level=2)}. Reloading..."
        )
        signal_reload(memo)


async def init_config(memo, logger, **kwargs):
    configmap_name = memo.configmap_name
    logger.info(f"Initializing config data structure from configmap {configmap_name}.")
    current_namespace = get_current_namespace()
    try:
        configmap = await ConfigMap.get(
            configmap_name,
            namespace=current_namespace,
        )
    except Exception as e:
        raise kopf.TemporaryError(
            f'Failed to retrieve ConfigMap "{configmap_name}": {e}'
        ) from e
    try:
        memo.config = config_from_dict(configmap["data"])
    except Exception as e:
        raise kopf.TemporaryError(
            f'Failed to parse ConfigMap "{configmap_name}": {e}'
        ) from e
    kopf.on.event(
        "configmap",
        when=lambda name, namespace, type, **_: name == configmap_name
        and namespace == current_namespace
        # Return early if this is just the initial invocation without an event type.
        # This run is obsolete since we already initialized the config at startup.
        and type,
    )(check_config_change)
    logger.info("Config initialization complete.")


def init_logging(verbose):
    if verbose == 0:
        log_level = logging.WARNING
    elif verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)


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
    help="Name of the Kubernetes ConfigMap used for configuration.",
)
@click.option(
    "-v",
    "--verbose",
    envvar="VERBOSE",
    count=True,
    help="Set log level to INFO via -v and DEBUG via -vv. Use numbers when using the env var.",
)
def main(configmap_name, healthz_port, verbose):
    init_logging(verbose)
    logger = logging.getLogger(__name__)
    while True:
        kopf.on.startup()(init_config)
        loop = uvloop.EventLoopPolicy().new_event_loop()
        stop_flag = asyncio.Future(loop=loop)
        config_reload_flag = asyncio.Future(loop=loop)
        memo = kopf.Memo(
            stop_flag=stop_flag,
            configmap_name=configmap_name,
            config_reload_flag=config_reload_flag,
        )
        kopf.run(
            clusterwide=True,
            loop=loop,
            liveness_endpoint=f"http://0.0.0.0:{healthz_port}/healthz",
            stop_flag=stop_flag,
            memo=memo,
        )

        if not memo.config_reload_flag.done():
            break  # if the operator shut down to reload its config we stay in the loop and reinit kopf
        logger.info("Config change detected. Reinitializing...")
    logger.info("Shutdown complete. Goodbye.")


if __name__ == "__main__":
    main()
