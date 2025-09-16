"""
Secret handling for the Kubernetes operator.

Contains functions for fetching Secrets from the cluster
and handling Secret change events.
"""

from typing import Any

import kopf
import structlog
from deepdiff import DeepDiff
from kr8s.objects import Secret

from haproxy_template_ic.core.logging import autolog
from haproxy_template_ic.credentials import Credentials
from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.tracing import (
    add_span_attributes,
    record_span_event,
    trace_async_function,
)

__all__ = [
    "fetch_secret",
    "handle_secret_change",
]

logger = structlog.get_logger(__name__)


@trace_async_function(
    span_name="fetch_secret", attributes={"operation.category": "kubernetes"}
)
async def fetch_secret(name: str, namespace: str) -> Secret:
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
    memo: ApplicationState,
    event: dict[str, Any],
    name: str,
    type: str,
    **kwargs: Any,
) -> None:
    """Handle Secret change events."""

    # Create new credentials from secret data
    secret_data = event["object"]["data"]
    new_credentials = Credentials.from_secret(secret_data)

    # Compare with existing credentials
    old_dict = memo.configuration.credentials.model_dump()
    new_dict = new_credentials.model_dump()

    # Use verbose_level=0 to hide password values in diff output
    diff = DeepDiff(old_dict, new_dict, verbose_level=0)
    if not diff:
        logger.debug("Credentials unchanged, skipping update")
        return

    # Credentials have changed - show the diff and trigger update
    # Convert to string efficiently for logging (verbose_level=0 already hides values)
    diff_str = str(diff)
    if len(diff_str) > 500:
        diff_str = diff_str[:500] + "..."
    logger.info("🔄 Credentials changed: updating", credentials_diff=diff_str)

    # Update credentials
    memo.configuration.credentials = new_credentials
