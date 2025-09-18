"""
Regression test for pod IP attribute access in get_production_urls_from_index.

This test specifically verifies that the code correctly uses pod.status.podIP
(the actual Kubernetes API field name) rather than pod.status.pod_ip.
"""

from haproxy_template_ic.dataplane import get_production_urls_from_index
from tests.unit.conftest import create_k8s_pod_resource


def test_pod_ip_attribute_uses_correct_field_name():
    """
    Test that get_production_urls_from_index correctly accesses pod.status.podIP.

    This test ensures we use the correct Kubernetes API field name (podIP)
    and not the incorrect snake_case version (pod_ip).
    """
    indexed_pods = {
        ("default", "test-pod"): create_k8s_pod_resource(
            name="test-pod",
            namespace="default",
            phase="Running",
            additional_status={"podIP": "192.168.1.100"},
            additional_metadata={"annotations": {}},
        )
    }

    urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
    assert urls == ["http://192.168.1.100:5555"]
    assert url_to_pod_name == {"http://192.168.1.100:5555": "test-pod"}


def test_pod_ip_attribute_with_custom_port():
    """Test that custom port annotation works with correct podIP field."""
    indexed_pods = {
        ("default", "test-pod"): create_k8s_pod_resource(
            name="test-pod-custom",
            namespace="default",
            phase="Running",
            additional_status={"podIP": "192.168.1.100"},
            additional_metadata={
                "annotations": {"haproxy-template-ic/dataplane-port": "8080"}
            },
        )
    }

    urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
    assert urls == ["http://192.168.1.100:8080"]
    assert url_to_pod_name == {"http://192.168.1.100:8080": "test-pod-custom"}


def test_pod_without_ip_excluded():
    """Test that pods without IP addresses are excluded."""
    indexed_pods = {
        ("default", "test-pod"): create_k8s_pod_resource(
            name="test-pod",
            namespace="default",
            phase="Running",
            additional_metadata={"annotations": {}},
            # No podIP field - simulates pending pod
        )
    }

    urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
    assert urls == []
    assert url_to_pod_name == {}


def test_mixed_pod_states():
    """Test that function correctly handles pods in various states."""
    indexed_pods = {
        ("default", "running-pod"): create_k8s_pod_resource(
            name="running-pod",
            namespace="default",
            phase="Running",
            additional_status={"podIP": "192.168.1.20"},
            additional_metadata={"annotations": {}},
        ),
        ("default", "pending-pod"): create_k8s_pod_resource(
            name="pending-pod",
            namespace="default",
            phase="Pending",
            additional_metadata={"annotations": {}},
            # No podIP for pending pods
        ),
        ("default", "terminating-pod"): create_k8s_pod_resource(
            name="terminating-pod",
            namespace="default",
            phase="Terminating",
            additional_status={"podIP": "192.168.1.21"},  # Has IP but not Running
            additional_metadata={"annotations": {}},
        ),
    }

    urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)

    # Should only include the running pod
    assert urls == ["http://192.168.1.20:5555"]
    assert url_to_pod_name == {"http://192.168.1.20:5555": "running-pod"}
