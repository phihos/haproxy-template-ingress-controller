"""
End-to-end acceptance test for HAProxy pod discovery via management socket.

This test verifies that the controller correctly discovers HAProxy instances
and reports them through the management socket, including proper handling
of deployment scaling operations.
"""

import asyncio
import re
import time

import pytest

from tests.e2e.utils import send_socket_command, wait_for_operator_ready

pytestmark = pytest.mark.acceptance


def get_pod_ips_from_socket_response(response):
    """Extract pod IP addresses from management socket response."""
    if isinstance(response, dict):
        # Try structured response format
        if "instances" in response:
            return [
                instance.get("pod_ip", instance.get("podIP"))
                for instance in response["instances"]
                if instance.get("pod_ip") or instance.get("podIP")
            ]
        # Try other possible formats
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
        if deployment.status.readyReplicas == expected_replicas:
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

    # Give controller time to discover initial HAProxy pods
    await asyncio.sleep(10)

    # Step 1: Verify initial discovery (2 instances)
    response = send_socket_command(ingress_controller, "dump all")
    discovered_ips = get_pod_ips_from_socket_response(response)

    # Get actual HAProxy pod IPs for validation
    haproxy_pods = k8s_client.get(
        "pods",
        label_selector="app=haproxy,component=loadbalancer",
        namespace=k8s_namespace,
    )
    actual_ips = [pod.status.podIP for pod in haproxy_pods if pod.status.podIP]

    assert len(discovered_ips) >= 2, (
        f"Expected at least 2 discovered instances, got {len(discovered_ips)}: {discovered_ips}"
    )
    for ip in discovered_ips:
        assert ip in actual_ips, (
            f"Discovered IP {ip} not found in actual pod IPs {actual_ips}"
        )

    # Step 2: Scale deployment down to 1 replica
    haproxy_deployment.scale(1)
    wait_for_deployment_replicas(haproxy_deployment, 1)

    # Wait for controller to detect scaling change
    await asyncio.sleep(15)

    # Step 3: Verify discovery after scaling down
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

    assert len(discovered_ips_after) == 1, (
        f"Expected 1 discovered instance after scaling, got {len(discovered_ips_after)}: {discovered_ips_after}"
    )
    assert discovered_ips_after[0] in actual_ips_after, (
        f"Discovered IP {discovered_ips_after[0]} not found in actual pod IPs {actual_ips_after}"
    )

    # Verify removed instances
    removed_ips = set(discovered_ips) - set(discovered_ips_after)
    assert len(removed_ips) >= 1, (
        "Should have at least one removed IP after scaling down"
    )

    # Step 4: Test scaling back up
    haproxy_deployment.scale(3)
    wait_for_deployment_replicas(haproxy_deployment, 3)

    await asyncio.sleep(15)

    # Final verification
    response = send_socket_command(ingress_controller, "dump all")
    discovered_ips_final = get_pod_ips_from_socket_response(response)
    assert len(discovered_ips_final) >= 3, (
        f"Expected at least 3 discovered instances after scaling up, got {len(discovered_ips_final)}: {discovered_ips_final}"
    )


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
    await asyncio.sleep(10)

    # Get initial discovered instances
    response = send_socket_command(ingress_controller, "dump all")
    initial_ips = get_pod_ips_from_socket_response(response)
    assert len(initial_ips) >= 2, (
        f"Expected at least 2 discovered instances, got {len(initial_ips)}"
    )

    # Delete one HAProxy pod
    haproxy_pods = k8s_client.get(
        "pods",
        label_selector="app=haproxy,component=loadbalancer",
        namespace=k8s_namespace,
    )

    if len(haproxy_pods) > 0:
        pod_to_delete = haproxy_pods[0]
        deleted_pod_ip = pod_to_delete.status.podIP
        pod_to_delete.delete()

        # Wait for deployment to recreate the pod
        wait_for_deployment_replicas(haproxy_deployment, 2)

        # Wait for controller to re-discover
        await asyncio.sleep(15)

        # Verify discovery after pod recreation
        response = send_socket_command(ingress_controller, "dump all")
        updated_ips = get_pod_ips_from_socket_response(response)

        assert len(updated_ips) >= 2, (
            f"Expected at least 2 instances after pod recreation, got {len(updated_ips)}"
        )
        # The deleted pod IP should be replaced with a new one
        assert deleted_pod_ip not in updated_ips or len(updated_ips) > len(
            initial_ips
        ), (
            f"Deleted pod IP {deleted_pod_ip} should be replaced or total count increased"
        )
