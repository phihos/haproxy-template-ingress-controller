"""
Shared test fixtures and utilities for models unit tests.

This module provides common fixtures and factory functions to eliminate
duplication across model test files.
"""

import pytest
from typing import Dict, Any, Optional


def create_base_config_dict(
    app_label: str = "myapp",
    template: str = "global\\n    daemon",
    watched_resources: Optional[Dict[str, Any]] = None,
    maps: Optional[Dict[str, Any]] = None,
    include_optional_fields: bool = False,
) -> Dict[str, Any]:
    """
    Create a base config dictionary with common test patterns.

    This eliminates the 65+ instances of repeated config dict structures
    across model tests.

    Args:
        app_label: Label for pod selector (default: "myapp")
        template: HAProxy config template (default: basic global daemon)
        watched_resources: Optional watched resources dict
        maps: Optional maps dict
        include_optional_fields: Whether to include empty optional fields

    Returns:
        Base config dictionary for testing
    """
    config = {
        "pod_selector": {"match_labels": {"app": app_label}},
        "haproxy_config": {"template": template},
    }

    if include_optional_fields or watched_resources is not None:
        config["watched_resources"] = watched_resources or {}

    if include_optional_fields or maps is not None:
        config["maps"] = maps or {}

    return config


def create_ingress_watch_config() -> Dict[str, Any]:
    """Create a watched resources config for ingresses."""
    return {
        "ingresses": {
            "api_version": "networking.k8s.io/v1",
            "kind": "Ingress",
        },
        "services": {"api_version": "v1", "kind": "Service"},
    }


def create_configmap_watch_config() -> Dict[str, Any]:
    """Create a watched resources config for configmaps."""
    return {
        "configmaps": {
            "api_version": "v1",
            "kind": "ConfigMap",
            "field_selector": "metadata.name=my-config",
        }
    }


def create_template_maps_config() -> Dict[str, Any]:
    """Create a maps config with template-based maps."""
    return {
        "path-prefix.map": {
            "template": "server {{ name }} {{ ip }}:{{ port }}",
        },
        "backend-servers.map": {
            "template": "server {{ name }} {{ ip }}:{{ port }}",
        },
    }


@pytest.fixture(scope="module")
def base_config_dict():
    """Fixture providing basic config dict for testing."""
    return create_base_config_dict()


@pytest.fixture(scope="module")
def config_with_resources():
    """Fixture providing config dict with watched resources."""
    return create_base_config_dict(watched_resources=create_ingress_watch_config())


@pytest.fixture(scope="module")
def config_with_maps():
    """Fixture providing config dict with maps."""
    return create_base_config_dict(maps={"geo.map": "US 1\\nEU 2"})
