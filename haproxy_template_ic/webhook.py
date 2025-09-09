"""
Kubernetes Validating Admission Webhook for HAProxy Template IC ConfigMaps.

This module implements validating admission webhook handlers using the kopf
framework to validate HAProxy Template IC ConfigMaps before they are applied
to the cluster, providing immediate feedback on configuration errors.
"""

import logging
from typing import Any, Dict, List, Optional

import kopf
import yaml


logger = logging.getLogger(__name__)


def _is_haproxy_template_ic_configmap(configmap_data: Dict[str, Any]) -> bool:
    """Check if this ConfigMap is intended for HAProxy Template IC."""
    # Check for specific labels or annotations that identify our ConfigMaps
    metadata = configmap_data.get("metadata", {})
    labels = metadata.get("labels", {})
    annotations = metadata.get("annotations", {})

    # Check for our specific labels/annotations
    if (
        labels.get("app.kubernetes.io/name") == "haproxy-template-ic"
        or labels.get("haproxy-template-ic/config") == "true"
        or "haproxy-template-ic" in annotations
    ):
        return True

    # Check if the ConfigMap has our expected config structure
    data = configmap_data.get("data", {})
    if "config" in data:
        try:
            config_dict = yaml.safe_load(data["config"])
            # Look for HAProxy Template IC specific keys
            expected_keys = {
                "pod_selector",
                "watch_resources",
                "maps",
                "haproxy_config",
                "certificates",
            }
            if any(key in config_dict for key in expected_keys):
                return True
        except (yaml.YAMLError, TypeError):
            pass

    return False


def _extract_config_data(configmap_data: Dict[str, Any]) -> Optional[str]:
    """Extract the config data from ConfigMap."""
    return configmap_data.get("data", {}).get("config")


async def _validate_resource_structure(
    spec: Dict[str, Any], meta: Dict[str, Any], kind: str, warnings: List[str]
) -> None:
    """Validate basic resource structure."""
    # Basic metadata validation
    if not meta.get("name"):
        raise kopf.AdmissionError(f"{kind} resource must have a name")

    name = meta["name"]

    # Validate name format
    if not name.replace("-", "").replace(".", "").replace("_", "").isalnum():
        warnings.append(
            f"{kind} name '{name}' contains special characters that may cause issues"
        )

    # Add kind-specific validations
    if kind.lower() == "ingress":
        await _validate_ingress_specific(spec, warnings)
    elif kind.lower() == "service":
        await _validate_service_specific(spec, warnings)
    elif kind.lower() == "secret":
        await _validate_secret_specific(spec, warnings)


async def _validate_ingress_specific(spec: Dict[str, Any], warnings: List[str]) -> None:
    """Validate Ingress-specific fields."""
    rules = spec.get("rules", [])
    if not rules:
        warnings.append(
            "Ingress has no rules defined. Add at least one rule with host or path configuration."
        )

    for i, rule in enumerate(rules):
        if not rule.get("host") and not rule.get("http"):
            warnings.append(f"Ingress rule {i} has neither host nor http configuration")


async def _validate_service_specific(spec: Dict[str, Any], warnings: List[str]) -> None:
    """Validate Service-specific fields."""
    ports = spec.get("ports", [])
    if not ports:
        warnings.append(
            "Service has no ports defined. Add at least one port configuration with 'port' and 'targetPort'."
        )

    for i, port in enumerate(ports):
        if not port.get("port"):
            raise kopf.AdmissionError(f"Service port {i} is missing 'port' field")


async def _validate_secret_specific(spec: Dict[str, Any], warnings: List[str]) -> None:
    """Validate Secret-specific fields."""
    data = spec.get("data", {})
    if not data:
        warnings.append(
            "Secret has no data entries defined. Add key-value pairs to the 'data' field."
        )


# Resource-Specific Validation (Configuration-Based Only)

# Note: We intentionally do NOT register a blanket ConfigMap webhook as that
# would make all ConfigMap operations in the cluster dependent on this service.
# Instead, we only validate specific resources as configured in watch_resources.
#
# Webhook registration is handled by the kopf framework based on configuration
# in the configure_webhook_server function in operator.py. This module provides
# the stateless validation functions that can be called by webhook handlers.


def register_validation_webhooks_from_config(operator_config) -> None:
    """Register validation webhooks based on operator configuration.

    This function is now stateless and does not maintain any global registry.
    Webhook registration is handled by the kopf framework through the
    configure_webhook_server function in operator.py.

    This function logs the webhook configuration for visibility but does not
    perform actual webhook registration to avoid persistence across operator reloads.
    """
    if not hasattr(operator_config, "watched_resources"):
        logger.debug("No watched_resources configuration found")
        return

    enabled_webhooks = []
    for resource_id, resource_config in operator_config.watched_resources.items():
        if resource_config.enable_validation_webhook:
            enabled_webhooks.append(f"{resource_config.kind} (id: {resource_id})")

    if enabled_webhooks:
        logger.info(f"Webhook validation configured for: {', '.join(enabled_webhooks)}")
        logger.debug(
            "Webhook handlers will be registered by kopf framework during server setup"
        )
    else:
        logger.debug("No validation webhooks enabled in configuration")
