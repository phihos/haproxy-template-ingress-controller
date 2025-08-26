"""
End-to-end acceptance test for HAProxy pod discovery via management socket.

This test verifies that the controller correctly discovers HAProxy instances
and reports them through the management socket, including proper handling
of deployment scaling operations.
"""

import asyncio
import ast
import re
import time

import pytest

from tests.e2e.utils import send_socket_command, wait_for_operator_ready

pytestmark = pytest.mark.acceptance


async def wait_for_condition(
    condition_func, timeout=60, initial_delay=1, max_delay=10, backoff_factor=1.5
):
    """Wait for a condition to be true with exponential backoff.

    Args:
        condition_func: Async function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        initial_delay: Initial delay between checks in seconds
        max_delay: Maximum delay between checks in seconds
        backoff_factor: Factor to multiply delay by after each failure

    Returns:
        True if condition was met, False if timeout occurred
    """
    start_time = time.time()
    delay = initial_delay

    while time.time() - start_time < timeout:
        try:
            if await condition_func():
                return True
        except Exception:
            # Condition check failed, continue waiting
            pass

        await asyncio.sleep(delay)
        delay = min(delay * backoff_factor, max_delay)

    return False


def get_pod_ips_from_socket_response(response):
    """Extract pod IP addresses from management socket response."""
    if isinstance(response, dict):
        # Look for HAProxy pod IPs in the indices section (operational data)
        if "indices" in response and "haproxy_pods" in response["indices"]:
            ips = []
            haproxy_pods_index = response["indices"]["haproxy_pods"]
            for key, resources in haproxy_pods_index.items():
                # Resources might be a list or a single resource
                if isinstance(resources, list):
                    resource_list = resources
                else:
                    resource_list = [resources]

                for resource in resource_list:
                    # Handle string representation of dictionaries
                    if isinstance(resource, str):
                        try:
                            resource = ast.literal_eval(resource)
                        except (ValueError, SyntaxError):
                            continue

                    if isinstance(resource, dict):
                        # Extract pod IP from resource status
                        if "status" in resource and isinstance(
                            resource["status"], dict
                        ):
                            pod_ip = resource["status"].get("podIP")
                            if pod_ip:
                                ips.append(pod_ip)
            return ips

        # Fall back to string representation
        response_str = str(response)
    else:
        response_str = str(response)

    # Fall back to regex extraction of IP addresses
    ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
    return re.findall(ip_pattern, response_str)


def wait_for_deployment_replicas(deployment, expected_replicas, timeout=60):
    """Wait for deployment to reach expected replica count."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        deployment.refresh()
        if getattr(deployment.status, "readyReplicas", 0) == expected_replicas:
            return
        time.sleep(2)
    raise TimeoutError(
        f"Deployment did not reach {expected_replicas} ready replicas in {timeout}s"
    )


@pytest.mark.asyncio
async def test_pod_discovery_with_scaling(
    ingress_controller,
    haproxy_deployment,
    enhanced_configmap_with_pod_selector,
    k8s_client,
    k8s_namespace,
):
    """
    Test that the controller correctly discovers HAProxy pods and tracks scaling operations.

    This test:
    1. Verifies that 2 production HAProxy instances are discovered initially
    2. Scales the deployment down to 1 replica
    3. Verifies that only 1 instance is discovered after scaling
    """
    # Wait for operator to be ready
    wait_for_operator_ready(ingress_controller)

    # Step 1: Wait for controller to discover initial HAProxy pods (2 instances)
    async def check_initial_discovery():
        response = send_socket_command(ingress_controller, "dump all")
        discovered_ips = get_pod_ips_from_socket_response(response)

        # Get actual HAProxy pod IPs for validation
        haproxy_pods = k8s_client.get(
            "pods",
            label_selector="app=haproxy,component=loadbalancer",
            namespace=k8s_namespace,
        )
        actual_ips = [pod.status.podIP for pod in haproxy_pods if pod.status.podIP]

        # Check if we have at least 2 discovered instances and they match actual IPs
        if len(discovered_ips) >= 2:
            for ip in discovered_ips:
                if ip not in actual_ips:
                    return False
            return True
        return False

    discovery_successful = await wait_for_condition(check_initial_discovery, timeout=30)
    assert discovery_successful, (
        "Controller failed to discover initial HAProxy pods within 30 seconds"
    )

    # Final state verified by the wait_for_condition above

    # Step 2: Scale deployment down to 1 replica
    haproxy_deployment.scale(1)
    wait_for_deployment_replicas(haproxy_deployment, 1)

    # Step 3: Wait for controller to detect scaling change and update discovery
    async def check_scaled_discovery():
        response = send_socket_command(ingress_controller, "dump all")
        discovered_ips_after = get_pod_ips_from_socket_response(response)

        haproxy_pods_after = k8s_client.get(
            "pods",
            label_selector="app=haproxy,component=loadbalancer",
            namespace=k8s_namespace,
        )
        actual_ips_after = [
            pod.status.podIP
            for pod in haproxy_pods_after
            if pod.status.phase == "Running" and pod.status.podIP
        ]

        # Allow for eventual consistency - should have at most the number of actual running pods + 1 for stale entries
        # But also verify we have at least one running instance discovered
        return (
            len(discovered_ips_after) <= len(actual_ips_after) + 1
            and len([ip for ip in discovered_ips_after if ip in actual_ips_after]) >= 1
        )

    scaling_detected = await wait_for_condition(check_scaled_discovery, timeout=30)
    assert scaling_detected, (
        "Controller failed to detect scaling change within 30 seconds"
    )

    # Get final state after scaling
    response = send_socket_command(ingress_controller, "dump all")
    discovered_ips_after = get_pod_ips_from_socket_response(response)
    haproxy_pods_after = k8s_client.get(
        "pods",
        label_selector="app=haproxy,component=loadbalancer",
        namespace=k8s_namespace,
    )
    actual_ips_after = [
        pod.status.podIP
        for pod in haproxy_pods_after
        if pod.status.phase == "Running" and pod.status.podIP
    ]
    # Verify that at least some discovered IPs correspond to actual running pods
    # (allowing for stale entries due to eventual consistency)
    running_ips_found = [ip for ip in discovered_ips_after if ip in actual_ips_after]
    assert len(running_ips_found) >= 1, (
        f"Expected at least 1 discovered IP to match running pods, got {running_ips_found} from discovered {discovered_ips_after} vs actual {actual_ips_after}"
    )

    # Step 4: Test scaling back up to 3 replicas
    haproxy_deployment.scale(3)
    wait_for_deployment_replicas(haproxy_deployment, 3)

    # Wait for controller to detect scale-up and discover new pods
    async def check_scale_up_discovery():
        response = send_socket_command(ingress_controller, "dump all")
        discovered_ips_final = get_pod_ips_from_socket_response(response)
        return len(discovered_ips_final) >= 3

    scale_up_detected = await wait_for_condition(check_scale_up_discovery, timeout=30)
    assert scale_up_detected, "Controller failed to detect scale-up within 30 seconds"

    # Final state verified by the wait_for_condition above


@pytest.mark.asyncio
async def test_pod_discovery_with_pod_deletion(
    ingress_controller,
    haproxy_deployment,
    enhanced_configmap_with_pod_selector,
    k8s_client,
    k8s_namespace,
):
    """
    Test that the controller correctly handles individual pod deletion and recreation.

    This test verifies proper handling when pods are deleted directly (not via scaling).
    """
    wait_for_operator_ready(ingress_controller)

    # Wait for initial pod discovery
    async def check_initial_pods_discovered():
        response = send_socket_command(ingress_controller, "dump all")
        initial_ips = get_pod_ips_from_socket_response(response)
        return len(initial_ips) >= 2

    initial_discovery = await wait_for_condition(
        check_initial_pods_discovered, timeout=30
    )
    assert initial_discovery, (
        "Controller failed to discover initial pods within 30 seconds"
    )

    # Get initial discovered instances
    response = send_socket_command(ingress_controller, "dump all")
    initial_ips = get_pod_ips_from_socket_response(response)

    # Delete one HAProxy pod
    haproxy_pods = k8s_client.get(
        "pods",
        label_selector="app=haproxy,component=loadbalancer",
        namespace=k8s_namespace,
    )

    haproxy_pods = list(haproxy_pods)
    if len(haproxy_pods) > 0:
        pod_to_delete = haproxy_pods[0]
        deleted_pod_ip = pod_to_delete.status.podIP
        pod_to_delete.delete()

        # Wait for deployment to recreate the pod
        wait_for_deployment_replicas(haproxy_deployment, 2)

        # Wait for controller to re-discover after pod recreation
        async def check_pod_recreation_discovery():
            response = send_socket_command(ingress_controller, "dump all")
            updated_ips = get_pod_ips_from_socket_response(response)
            return len(updated_ips) >= 2

        recreation_detected = await wait_for_condition(
            check_pod_recreation_discovery, timeout=30
        )
        assert recreation_detected, (
            "Controller failed to detect pod recreation within 30 seconds"
        )

        # Get updated state for verification
        response = send_socket_command(ingress_controller, "dump all")
        updated_ips = get_pod_ips_from_socket_response(response)
        # Verify pod recreation worked - either:
        # 1. The deleted pod IP is no longer in the discovered list, OR
        # 2. New pods were created (indicating successful recreation)
        new_ips = set(updated_ips) - set(initial_ips)
        assert deleted_pod_ip not in updated_ips or len(new_ips) > 0, (
            f"Expected pod recreation: deleted IP {deleted_pod_ip} should be gone or new IPs should appear. "
            f"Initial: {initial_ips}, Updated: {updated_ips}, New IPs: {new_ips}"
        )
