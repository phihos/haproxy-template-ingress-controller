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

from haproxy_template_ic.metrics import get_metrics_collector

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


# =============================================================================
# Dynamic Webhook Registration
# =============================================================================


class WebhookRegistry:
    """Manages dynamic registration of validation webhooks based on configuration."""

    def __init__(self):
        self.registered_handlers: Dict[str, Any] = {}

    def register_resource_validation_webhook(
        self, group: str, version: str, kind: str, resource_id: str
    ) -> None:
        """Register a validation webhook for a specific resource type."""
        handler_key = f"{group}/{version}/{kind}"

        if handler_key in self.registered_handlers:
            logger.debug(f"Webhook handler already registered for {handler_key}")
            return

        # Create the validation handler function
        async def resource_validation_handler(**kwargs: Any) -> None:
            """Dynamically created validation handler."""
            metrics = get_metrics_collector()

            try:
                with metrics.time_webhook_request():
                    # Extract kopf parameters
                    warnings = kwargs.get("warnings", [])
                    spec = kwargs.get("spec", {})
                    meta = kwargs.get("meta", {})

                    # Handle None values from kopf
                    if spec is None or meta is None:
                        logger.debug(
                            f"Skipping validation - missing spec or meta for {kind}"
                        )
                        return

                    # Add resource-specific validation logic here
                    logger.info(
                        f"Validating {kind} resource: {meta.get('name', 'unknown')}"
                    )

                    # For now, we'll add basic structural validation
                    # In the future, this could include template rendering validation
                    # or other resource-specific checks

                    await self._validate_resource_structure(spec, meta, kind, warnings)

            except kopf.AdmissionError as e:
                logger.warning(f"{kind} validation failed: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {kind} webhook validation: {e}")
                raise kopf.AdmissionError(f"Internal validation error: {e}")

        # Build a DNS-1123 compliant handler id for webhook naming
        safe_group = (group or "core").replace("/", ".").replace("_", "-")
        safe_version = (version or "v1").replace("_", "-")
        base_id = resource_id or kind.lower()
        # only allow lowercase alnum and hyphen in id
        import re

        safe_base = re.sub(r"[^a-z0-9-]", "-", base_id.lower())
        handler_id = (
            f"validate-{safe_base}-{safe_group.replace('.', '-')}-{safe_version}"
        )

        # Register the handler with kopf using a stable, valid id
        kopf.on.validate(group, version, kind, id=handler_id)(
            resource_validation_handler
        )

        self.registered_handlers[handler_key] = resource_validation_handler
        logger.info(f"Registered validation webhook for {handler_key}")

    async def _validate_resource_structure(
        self, spec: Dict[str, Any], meta: Dict[str, Any], kind: str, warnings: List[str]
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
            await self._validate_ingress_specific(spec, warnings)
        elif kind.lower() == "service":
            await self._validate_service_specific(spec, warnings)
        elif kind.lower() == "secret":
            await self._validate_secret_specific(spec, warnings)

    async def _validate_ingress_specific(
        self, spec: Dict[str, Any], warnings: List[str]
    ) -> None:
        """Validate Ingress-specific fields."""
        rules = spec.get("rules", [])
        if not rules:
            warnings.append(
                "Ingress has no rules defined. Add at least one rule with host or path configuration."
            )

        for i, rule in enumerate(rules):
            if not rule.get("host") and not rule.get("http"):
                warnings.append(
                    f"Ingress rule {i} has neither host nor http configuration"
                )

    async def _validate_service_specific(
        self, spec: Dict[str, Any], warnings: List[str]
    ) -> None:
        """Validate Service-specific fields."""
        ports = spec.get("ports", [])
        if not ports:
            warnings.append(
                "Service has no ports defined. Add at least one port configuration with 'port' and 'targetPort'."
            )

        for i, port in enumerate(ports):
            if not port.get("port"):
                raise kopf.AdmissionError(f"Service port {i} is missing 'port' field")

    async def _validate_secret_specific(
        self, spec: Dict[str, Any], warnings: List[str]
    ) -> None:
        """Validate Secret-specific fields."""
        data = spec.get("data", {})
        if not data:
            warnings.append(
                "Secret has no data entries defined. Add key-value pairs to the 'data' field."
            )


# Global webhook registry
_webhook_registry = WebhookRegistry()


# =============================================================================
# Resource-Specific Validation (Configuration-Based Only)
# =============================================================================

# Note: We intentionally do NOT register a blanket ConfigMap webhook as that
# would make all ConfigMap operations in the cluster dependent on this service.
# Instead, we only validate specific resources as configured in watch_resources.


# =============================================================================
# Configuration-based Webhook Registration
# =============================================================================


def register_validation_webhooks_from_config(operator_config) -> None:
    """Register validation webhooks based on operator configuration."""
    if not hasattr(operator_config, "watched_resources"):
        logger.debug("No watched_resources configuration found")
        return

    for resource_id, resource_config in operator_config.watched_resources.items():
        if not resource_config.enable_validation_webhook:
            logger.debug(f"Validation webhook disabled for {resource_config.kind}")
            continue

        # Parse group and version from api_version
        if "/" in resource_config.api_version:
            group, version = resource_config.api_version.rsplit("/", 1)
        else:
            group = ""
            version = resource_config.api_version
        kind = resource_config.kind

        logger.info(
            f"Enabling validation webhook for {resource_config.kind} (id: {resource_id})"
        )

        _webhook_registry.register_resource_validation_webhook(
            group=group, version=version, kind=kind, resource_id=resource_id
        )
