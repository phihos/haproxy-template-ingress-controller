"""
Regression test for pod IP attribute access in HAProxyPodDiscovery.

This test specifically verifies that the code correctly uses pod.status.podIP
(the actual Kubernetes API field name) rather than pod.status.pod_ip.
"""

import pytest
from unittest.mock import patch
from box import Box

from haproxy_template_ic.dataplane import HAProxyPodDiscovery, DataplaneAPIError
from haproxy_template_ic.config_models import PodSelector


class TestPodIPAttributeRegression:
    """Test for pod IP attribute access regression."""

    @pytest.fixture
    def pod_selector(self):
        """Create a PodSelector for testing."""
        return PodSelector(match_labels={"app": "haproxy", "component": "loadbalancer"})

    @pytest.fixture
    def discovery(self, pod_selector):
        """Create HAProxyPodDiscovery instance."""
        return HAProxyPodDiscovery(pod_selector, namespace="default")

    def test_pod_ip_attribute_uses_correct_field_name(self, discovery):
        """
        Test that _build_dataplane_url correctly accesses pod.status.podIP.

        This test ensures we use the correct Kubernetes API field name (podIP)
        and not the incorrect snake_case version (pod_ip).
        """
        # Create a mock pod that simulates kr8s Box behavior
        # Box objects will raise AttributeError for non-existent attributes
        pod_data = {
            "namespace": "default",
            "name": "test-pod",
            "status": {
                "podIP": "192.168.1.100",  # Correct field name from Kubernetes API
                # Note: pod_ip does NOT exist in the actual API
            },
            "metadata": {"annotations": {}},
        }

        # Use Box to simulate kr8s behavior - it will only allow access to existing keys
        pod = Box(pod_data)

        # This should work with the correct attribute name
        url = discovery._build_dataplane_url(pod)
        assert url == "http://192.168.1.100:5555"

        # Verify that accessing pod.status.pod_ip would fail (as it should)
        with pytest.raises(AttributeError):
            _ = pod.status.pod_ip  # This should fail because pod_ip doesn't exist

    def test_pod_ip_attribute_with_custom_port(self, discovery):
        """Test that custom port annotation works with correct podIP field."""
        pod_data = {
            "namespace": "default",
            "name": "test-pod",
            "status": {
                "podIP": "192.168.1.100",
            },
            "metadata": {"annotations": {"haproxy-template-ic/dataplane-port": "8080"}},
        }

        pod = Box(pod_data)
        url = discovery._build_dataplane_url(pod)
        assert url == "http://192.168.1.100:8080"

    def test_pod_without_ip_raises_error(self, discovery):
        """Test that pods without IP addresses raise appropriate errors."""
        pod_data = {
            "namespace": "default",
            "name": "test-pod",
            "status": {
                # No podIP field - simulates pending pod
            },
            "metadata": {"annotations": {}},
        }

        pod = Box(pod_data, default_box=True, default_box_attr=None)

        with pytest.raises(DataplaneAPIError, match="has no IP address"):
            discovery._build_dataplane_url(pod)

    @pytest.mark.asyncio
    @patch("kr8s.get")
    async def test_discover_instances_uses_correct_pod_ip_field(
        self, mock_kr8s_get, discovery
    ):
        """
        Integration test that discover_instances works with correct podIP field.

        This test simulates the full discovery flow with kr8s-style pod objects.
        """
        # Create mock pods with Box to simulate kr8s behavior
        pod1_data = {
            "namespace": "default",
            "name": "haproxy-pod-1",
            "status": {
                "phase": "Running",
                "podIP": "192.168.1.10",  # Correct field name
            },
            "metadata": {
                "labels": {},
                "annotations": {},
            },
        }

        pod2_data = {
            "namespace": "default",
            "name": "haproxy-pod-2",
            "status": {
                "phase": "Running",
                "podIP": "192.168.1.11",  # Correct field name
            },
            "metadata": {
                "labels": {"haproxy-template-ic/role": "validation"},
                "annotations": {},
            },
        }

        # Create Box objects to simulate kr8s Pod objects
        mock_pods = [Box(pod1_data), Box(pod2_data)]
        mock_kr8s_get.return_value = mock_pods

        # This should work without AttributeError
        instances = await discovery.discover_instances()

        assert len(instances) == 2
        assert instances[0].dataplane_url == "http://192.168.1.10:5555"
        assert instances[1].dataplane_url == "http://192.168.1.11:5555"
        assert instances[0].is_validation_sidecar is False
        assert instances[1].is_validation_sidecar is True

    @pytest.mark.asyncio
    @patch("kr8s.get")
    async def test_discover_instances_with_mixed_pod_states(
        self, mock_kr8s_get, discovery
    ):
        """Test that discovery correctly handles pods in various states."""
        pods_data = [
            {
                "namespace": "default",
                "name": "running-pod",
                "status": {
                    "phase": "Running",
                    "podIP": "192.168.1.20",
                },
                "metadata": {"labels": {}, "annotations": {}},
            },
            {
                "namespace": "default",
                "name": "pending-pod",
                "status": {
                    "phase": "Pending",
                    # No podIP for pending pods
                },
                "metadata": {"labels": {}, "annotations": {}},
            },
            {
                "namespace": "default",
                "name": "terminating-pod",
                "status": {
                    "phase": "Terminating",
                    "podIP": "192.168.1.21",  # May still have IP but shouldn't be discovered
                },
                "metadata": {"labels": {}, "annotations": {}},
            },
        ]

        mock_pods = [Box(pod_data) for pod_data in pods_data]
        mock_kr8s_get.return_value = mock_pods

        instances = await discovery.discover_instances()

        # Should only discover the running pod
        assert len(instances) == 1
        assert instances[0].dataplane_url == "http://192.168.1.20:5555"
