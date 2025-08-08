import logging
from functools import partial
import click
import kopf
import uvloop
from kr8s.objects import ConfigMap

from haproxy_template_ic.config import config_from_dict
from haproxy_template_ic.utils import get_current_namespace

config = None


def update_config_from_configmap(configmap):
    global config
    config = config_from_dict(configmap["data"])


async def reload_config(spec, name, namespace, logger, **kwargs):
    update_config_from_configmap(spec)


async def init_config(configmap_name, logger, **kwargs):
    logger.info(f"Initializing config data structure from configmap {configmap_name}.")
    current_namespace = get_current_namespace()
    try:
        config_map = await ConfigMap.get(
            configmap_name,
            namespace=current_namespace,
        )
    except Exception as e:
        raise kopf.TemporaryError(
            f'Failed to retrieve ConfigMap "{configmap_name}": {e}'
        ) from e
    try:
        update_config_from_configmap(config_map)
    except Exception as e:
        raise kopf.TemporaryError(
            f'Failed to parse ConfigMap "{configmap_name}": {e}'
        ) from e
    kopf.on.update(
        "configmap",
        field=[
            f"metadata.name={configmap_name}",
            f"metadata.namespace={current_namespace}",
        ],
    )(reload_config)
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
    kopf.on.startup()(partial(init_config, configmap_name=configmap_name))
    kopf.run(
        clusterwide=True,
        loop=uvloop.EventLoopPolicy().new_event_loop(),
        liveness_endpoint=f"http://0.0.0.0:{healthz_port}/healthz",
    )


if __name__ == "__main__":
    main()
