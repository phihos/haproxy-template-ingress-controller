"""
Regression test for pod IP attribute access in get_production_urls_from_index.

This test specifically verifies that the code correctly uses pod.status.podIP
(the actual Kubernetes API field name) rather than pod.status.pod_ip.
"""

from haproxy_template_ic.dataplane import get_production_urls_from_index


class TestPodIPAttributeRegression:
    """Test for pod IP attribute access regression."""

    def test_pod_ip_attribute_uses_correct_field_name(self):
        """
        Test that get_production_urls_from_index correctly accesses pod.status.podIP.

        This test ensures we use the correct Kubernetes API field name (podIP)
        and not the incorrect snake_case version (pod_ip).
        """
        indexed_pods = {
            ("default", "test-pod"): {
                "status": {
                    "phase": "Running",
                    "podIP": "192.168.1.100",  # Correct field name from Kubernetes API
                    # Note: pod_ip does NOT exist in the actual API
                },
                "metadata": {"annotations": {}, "name": "test-pod"},
            }
        }

        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
        assert urls == ["http://192.168.1.100:5555"]
        assert url_to_pod_name == {"http://192.168.1.100:5555": "test-pod"}

    def test_pod_ip_attribute_with_custom_port(self):
        """Test that custom port annotation works with correct podIP field."""
        indexed_pods = {
            ("default", "test-pod"): {
                "status": {
                    "phase": "Running",
                    "podIP": "192.168.1.100",
                },
                "metadata": {
                    "annotations": {"haproxy-template-ic/dataplane-port": "8080"},
                    "name": "test-pod-custom",
                },
            }
        }

        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
        assert urls == ["http://192.168.1.100:8080"]
        assert url_to_pod_name == {"http://192.168.1.100:8080": "test-pod-custom"}

    def test_pod_without_ip_excluded(self):
        """Test that pods without IP addresses are excluded."""
        indexed_pods = {
            ("default", "test-pod"): {
                "status": {
                    "phase": "Running",
                    # No podIP field - simulates pending pod
                },
                "metadata": {"annotations": {}, "name": "test-pod"},
            }
        }

        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)
        assert urls == []
        assert url_to_pod_name == {}

    def test_mixed_pod_states(self):
        """Test that function correctly handles pods in various states."""
        indexed_pods = {
            ("default", "running-pod"): {
                "status": {
                    "phase": "Running",
                    "podIP": "192.168.1.20",
                },
                "metadata": {"annotations": {}, "name": "running-pod"},
            },
            ("default", "pending-pod"): {
                "status": {
                    "phase": "Pending",
                    # No podIP for pending pods
                },
                "metadata": {"annotations": {}, "name": "pending-pod"},
            },
            ("default", "terminating-pod"): {
                "status": {
                    "phase": "Terminating",
                    "podIP": "192.168.1.21",  # Has IP but not Running
                },
                "metadata": {"annotations": {}, "name": "terminating-pod"},
            },
        }

        urls, url_to_pod_name = get_production_urls_from_index(indexed_pods)

        # Should only include the running pod
        assert urls == ["http://192.168.1.20:5555"]
        assert url_to_pod_name == {"http://192.168.1.20:5555": "running-pod"}
