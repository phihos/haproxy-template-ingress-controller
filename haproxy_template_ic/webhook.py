"""
Kubernetes Validating Admission Webhook for HAProxy Template IC ConfigMaps.

This module implements validating admission webhook handlers using the kopf
framework to validate HAProxy Template IC ConfigMaps before they are applied
to the cluster, providing immediate feedback on configuration errors.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import jinja2
import kopf
import yaml

from haproxy_template_ic.config_models import config_from_dict
from haproxy_template_ic.metrics import get_metrics_collector
from haproxy_template_ic.tracing import (
    trace_async_function,
    add_span_attributes,
    record_span_event,
    set_span_error,
)

logger = logging.getLogger(__name__)


class ConfigMapValidator:
    """Validates HAProxy Template IC ConfigMaps."""

    def __init__(self):
        self.metrics = get_metrics_collector()

    @trace_async_function(
        span_name="validate_configmap",
        attributes={"operation.category": "webhook_validation"},
    )
    async def validate_configmap(
        self, configmap_data: Dict[str, Any], warnings: List[str]
    ) -> None:
        """Validate a HAProxy Template IC ConfigMap. Raises kopf.AdmissionError on failure."""
        add_span_attributes(
            configmap_name=configmap_data.get("metadata", {}).get("name", "unknown"),
            configmap_namespace=configmap_data.get("metadata", {}).get(
                "namespace", "unknown"
            ),
        )

        try:
            # Check if this is a HAProxy Template IC ConfigMap
            if not self._is_haproxy_template_ic_configmap(configmap_data):
                # Not our ConfigMap, allow it
                record_span_event("validation_skipped_not_haproxy_ic")
                return  # Skip validation for non-HAProxy Template IC ConfigMaps

            # Extract and validate the config data
            config_yaml = self._extract_config_data(configmap_data)
            if not config_yaml:
                raise kopf.AdmissionError("Missing 'config' key in ConfigMap data")

            # Parse YAML configuration
            try:
                config_dict = yaml.safe_load(config_yaml)
            except yaml.YAMLError as e:
                raise kopf.AdmissionError(f"Invalid YAML in config: {e}")

            # Validate configuration structure
            validation_warnings = await self._validate_config_structure(config_dict)
            warnings.extend(validation_warnings)

            # Validate Jinja2 templates
            template_warnings = await self._validate_templates(config_dict)
            warnings.extend(template_warnings)

            # Validate resource references
            resource_warnings = await self._validate_resource_references(config_dict)
            warnings.extend(resource_warnings)

            # Create operator config to catch any structural issues
            try:
                config_from_dict(config_dict)
            except Exception as e:
                raise kopf.AdmissionError(f"Invalid operator configuration: {e}")

            record_span_event(
                "validation_successful", {"warnings_count": len(warnings)}
            )

            logger.info(f"ConfigMap validation passed with {len(warnings)} warnings")

        except kopf.AdmissionError:
            # Re-raise AdmissionError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            record_span_event("validation_error", {"error": str(e)})
            set_span_error(e, "Unexpected validation error")
            raise kopf.AdmissionError(f"Internal validation error: {e}")

    def _is_haproxy_template_ic_configmap(self, configmap_data: Dict[str, Any]) -> bool:
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

    def _extract_config_data(self, configmap_data: Dict[str, Any]) -> Optional[str]:
        """Extract the config data from ConfigMap."""
        return configmap_data.get("data", {}).get("config")

    async def _validate_config_structure(
        self, config_dict: Dict[str, Any]
    ) -> List[str]:
        """Validate the basic structure of the configuration."""
        warnings = []

        # Check for required sections
        if "pod_selector" not in config_dict:
            warnings.append(
                "Missing 'pod_selector' section - HAProxy pods may not be discovered"
            )

        if "watch_resources" not in config_dict:
            warnings.append(
                "Missing 'watch_resources' section - no resources will be watched"
            )

        # Check for at least one template type
        template_sections = ["maps", "haproxy_config", "certificates"]
        if not any(section in config_dict for section in template_sections):
            warnings.append(
                "No template sections found (maps, haproxy_config, certificates)"
            )

        # Validate pod selector structure
        pod_selector = config_dict.get("pod_selector", {})
        if isinstance(pod_selector, dict) and "match_labels" not in pod_selector:
            warnings.append("pod_selector should contain 'match_labels'")

        return warnings

    async def _validate_templates(self, config_dict: Dict[str, Any]) -> List[str]:
        """Validate all Jinja2 templates in the configuration."""
        warnings = []

        # Validate template snippets first
        snippets = config_dict.get("template_snippets", {})
        snippet_env = self._create_template_environment(snippets)

        for snippet_name, snippet_template in snippets.items():
            try:
                snippet_env.from_string(snippet_template)
            except jinja2.TemplateSyntaxError as e:
                warnings.append(
                    f"Invalid template syntax in snippet '{snippet_name}': {e}"
                )
            except Exception as e:
                warnings.append(f"Error in template snippet '{snippet_name}': {e}")

        # Validate maps
        maps = config_dict.get("maps", {})
        for map_path, map_config in maps.items():
            if isinstance(map_config, dict) and "template" in map_config:
                try:
                    template_env = self._create_template_environment(snippets)
                    template_env.from_string(map_config["template"])
                except jinja2.TemplateSyntaxError as e:
                    warnings.append(f"Invalid template syntax in map '{map_path}': {e}")
                except jinja2.TemplateNotFound as e:
                    warnings.append(
                        f"Template snippet not found in map '{map_path}': {e}"
                    )
                except Exception as e:
                    warnings.append(f"Error in map template '{map_path}': {e}")

        # Validate HAProxy config
        haproxy_config = config_dict.get("haproxy_config", {})
        if isinstance(haproxy_config, dict) and "template" in haproxy_config:
            try:
                template_env = self._create_template_environment(snippets)
                template_env.from_string(haproxy_config["template"])
            except jinja2.TemplateSyntaxError as e:
                warnings.append(f"Invalid template syntax in haproxy_config: {e}")
            except jinja2.TemplateNotFound as e:
                warnings.append(f"Template snippet not found in haproxy_config: {e}")
            except Exception as e:
                warnings.append(f"Error in haproxy_config template: {e}")

        # Validate certificates
        certificates = config_dict.get("certificates", {})
        for cert_path, cert_config in certificates.items():
            if isinstance(cert_config, dict) and "template" in cert_config:
                try:
                    template_env = self._create_template_environment(snippets)
                    template_env.from_string(cert_config["template"])
                except jinja2.TemplateSyntaxError as e:
                    warnings.append(
                        f"Invalid template syntax in certificate '{cert_path}': {e}"
                    )
                except jinja2.TemplateNotFound as e:
                    warnings.append(
                        f"Template snippet not found in certificate '{cert_path}': {e}"
                    )
                except Exception as e:
                    warnings.append(f"Error in certificate template '{cert_path}': {e}")

        return warnings

    def _create_template_environment(
        self, snippets: Dict[str, str]
    ) -> jinja2.Environment:
        """Create a Jinja2 environment with snippet support for validation."""

        # Simple dict loader for snippets
        class SnippetLoader(jinja2.BaseLoader):
            def __init__(self, snippets: Dict[str, str]):
                self.snippets = snippets

            def get_source(
                self, environment: jinja2.Environment, template: str
            ) -> Tuple[str, Optional[str], Optional[Any]]:
                if template in self.snippets:
                    return self.snippets[template], None, lambda: True
                raise jinja2.TemplateNotFound(template)

        return jinja2.Environment(  # nosec B701
            loader=SnippetLoader(snippets), undefined=jinja2.StrictUndefined
        )

    async def _validate_resource_references(
        self, config_dict: Dict[str, Any]
    ) -> List[str]:
        """Validate that referenced Kubernetes resources are valid."""
        warnings = []

        watch_resources = config_dict.get("watch_resources", [])

        # Handle both list and dict formats
        if isinstance(watch_resources, dict):
            # Dict format: resource_name -> resource_config
            resource_items = list(watch_resources.items())
        elif isinstance(watch_resources, list):
            # List format: enumerate for resource names
            resource_items = [
                (f"resource_{i}", res) for i, res in enumerate(watch_resources)
            ]
        else:
            warnings.append("watch_resources must be a list or dictionary")
            return warnings

        for resource_name, resource_config in resource_items:
            if not isinstance(resource_config, dict):
                warnings.append(
                    f"Invalid watch_resource '{resource_name}': should be a dictionary"
                )
                continue

            # Validate required fields
            required_fields = {"kind", "group", "version"}
            missing_fields = required_fields - set(resource_config.keys())
            if missing_fields:
                warnings.append(
                    f"Watch resource '{resource_name}' missing required fields: {missing_fields}"
                )

            # Validate field values
            kind = resource_config.get("kind")
            if kind and not isinstance(kind, str):
                warnings.append(
                    f"Watch resource '{resource_name}': 'kind' must be a string"
                )

            group = resource_config.get("group")
            if group is not None and not isinstance(group, str):
                warnings.append(
                    f"Watch resource '{resource_name}': 'group' must be a string"
                )

            version = resource_config.get("version")
            if version and not isinstance(version, str):
                warnings.append(
                    f"Watch resource '{resource_name}': 'version' must be a string"
                )

        return warnings


# Global validator instance for kopf handlers
_validator = ConfigMapValidator()


# =============================================================================
# Dynamic Webhook Registration
# =============================================================================


class WebhookRegistry:
    """Manages dynamic registration of validation webhooks based on configuration."""

    def __init__(self):
        self.registered_handlers: Dict[str, Any] = {}
        self.validator = ConfigMapValidator()

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
