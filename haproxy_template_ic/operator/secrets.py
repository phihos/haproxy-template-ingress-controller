"""
Secret handling for the Kubernetes operator.

Contains functions for fetching Secrets from the cluster
and handling Secret change events.
"""

import logging
from typing import Any

import kopf
import structlog
from kr8s.objects import Secret

from haproxy_template_ic.structured_logging import autolog
from haproxy_template_ic.tracing import (
    add_span_attributes,
    record_span_event,
    trace_async_function,
)

__all__ = [
    "fetch_secret",
    "handle_secret_change",
]


@trace_async_function(
    span_name="fetch_secret", attributes={"operation.category": "kubernetes"}
)
async def fetch_secret(name: str, namespace: str) -> Any:
    """Fetch Secret from Kubernetes cluster."""
    add_span_attributes(secret_name=name, secret_namespace=namespace)
    try:
        result = await Secret.get(name, namespace=namespace)
        record_span_event("secret_fetched")
        return result
    except (ConnectionError, TimeoutError) as e:
        record_span_event("secret_fetch_failed", {"error": str(e)})
        raise kopf.TemporaryError(
            f'Network error retrieving Secret "{name}": {e}'
        ) from e
    except Exception as e:
        record_span_event("secret_fetch_failed", {"error": str(e)})
        raise kopf.PermanentError(
            f'Failed to retrieve Secret "{name}": {e}. Credentials are mandatory for operation.'
        ) from e


@autolog(component="operator")
async def handle_secret_change(
    memo: Any,
    event: dict[str, Any],
    name: str,
    type: str,
    logger: logging.Logger,
    **kwargs: Any,
) -> None:
    """Handle Secret change events."""
    # Logging context is automatically injected by @autolog decorator
    structured_logger = structlog.get_logger(__name__)
    structured_logger.info(f"Kubernetes {type}")

    # Store the new credentials in memo for next sync operation
    memo.credentials = event["object"]
    structured_logger.info("Credentials updated, will be used in next sync")
