"""
Assertion utilities for HAProxy Template IC tests.

This module contains reusable assertion helpers for validating configurations,
responses, and data structures in end-to-end tests.
"""


def verify_config_contains(actual_config, expected_partial):
    """Verify that actual config contains all expected key-value pairs."""
    for key, expected_value in expected_partial.items():
        assert key in actual_config, f"Missing expected config key: {key}"
        assert actual_config[key] == expected_value, f"Config key '{key}' mismatch"


def verify_response_has_structure(response, required_keys):
    """Verify that response contains all required top-level keys."""
    missing_keys = [key for key in required_keys if key not in response]
    assert not missing_keys, f"Response missing required keys: {missing_keys}"


def assert_config_structure(config):
    """Assert that config has the expected structure and values."""
    expected_config = {
        "pod_selector": {
            "match_labels": {"app": "haproxy", "component": "loadbalancer"}
        },
    }
    verify_config_contains(config, expected_config)

    # Verify required sections exist and have expected nested values
    assert "watched_resources" in config and "maps" in config

    watched_resources = config["watched_resources"]
    if "ingresses" in watched_resources:
        expected_ingress = {"kind": "Ingress", "api_version": "networking.k8s.io/v1"}
        verify_config_contains(watched_resources["ingresses"], expected_ingress)


def assert_dump_all_response_structure(response):
    """Assert that 'dump all' response has the expected structure and values."""
    # Verify response has all required sections
    required_keys = [
        "config",
        "haproxy_config_context",
        "metadata",
        "indices",
        "cli_options",
    ]
    verify_response_has_structure(response, required_keys)

    # Verify config data
    assert_config_structure(response["config"])

    # Verify expected metadata values
    expected_metadata = {
        "configmap_name": "haproxy-template-ic-config",
        "has_config_reload_flag": True,
        "has_stop_flag": True,
    }
    verify_config_contains(response["metadata"], expected_metadata)

    # Verify expected CLI options
    expected_cli_options = {
        "configmap_name": "haproxy-template-ic-config",
    }
    verify_config_contains(response["cli_options"], expected_cli_options)
