"""
End-to-end acceptance test for HAProxy pod discovery.

This test verifies that the controller correctly discovers HAProxy instances
and reports them through operator logs, including proper handling
of deployment scaling and pod deletion operations.
"""

import ast
import asyncio
import logging
import re
import time

import pytest

from tests.e2e.utils import wait_for_operator_ready

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.acceptance


def get_running_haproxy_pods(k8s_client, namespace):
    """Get list of running HAProxy pods with assigned IPs, excluding terminating pods."""
    pods = k8s_client.get(
        "pods",
        label_selector="app=haproxy,component=loadbalancer",
        namespace=namespace,
    )
    running_pods = []
    for pod in pods:
        # Skip pods that are being deleted (have deletionTimestamp)
        if getattr(pod.metadata, "deletionTimestamp", None):
            continue
        # Only include pods that are Running with assigned IPs
        if (getattr(pod.status, "phase", None) == "Running" 
            and getattr(pod.status, "podIP", None)):
            running_pods.append(pod)
    return running_pods


def extract_production_urls_from_logs(operator):
    """Extract production URLs from operator logs.
    
    Returns:
        List of URLs found in the latest log entry, or empty list if none found
    """
    try:
        logs = operator.get_logs()
        # Look for log lines like: 🔍 Found 2 production URLs: ['http://10.244.0.66:5555', 'http://10.244.0.67:5555']
        pattern = r"🔍 Found \d+ production URLs: (\[.*?\])"
        matches = re.findall(pattern, logs)
        
        if matches:
            # Parse the latest match as a Python list
            latest_urls_str = matches[-1]
            try:
                # Use ast.literal_eval to safely parse the list
                urls = ast.literal_eval(latest_urls_str)
                return urls if isinstance(urls, list) else []
            except (ValueError, SyntaxError):
                # Fallback: extract URLs using regex
                url_pattern = r"http://[\d\.]+:\d+"
                return re.findall(url_pattern, latest_urls_str)
        return []
    except Exception as e:
        logger.debug(f"Error extracting production URLs: {e}")
        return []


def extract_ips_from_urls(urls):
    """Extract IP addresses from production URLs.
    
    Args:
        urls: List of URLs like ['http://10.244.0.66:5555', 'http://10.244.0.67:5555']
        
    Returns:
        Set of IP addresses like {'10.244.0.66', '10.244.0.67'}
    """
    ips = set()
    for url in urls:
        # Extract IP from URL using regex
        ip_match = re.search(r"http://([\d\.]+):", url)
        if ip_match:
            ips.add(ip_match.group(1))
    return ips


def verify_discovered_ips_match_pods(operator, expected_pods, description=""):
    """Verify that discovered production URLs match the expected pods.
    
    Args:
        operator: Operator instance to get logs from
        expected_pods: List of pod objects with podIP in status
        description: Description for error messages
        
    Returns:
        bool: True if discovered IPs match expected pod IPs exactly
    """
    try:
        discovered_urls = extract_production_urls_from_logs(operator)
        discovered_ips = extract_ips_from_urls(discovered_urls)
        
        expected_ips = set(getattr(pod.status, "podIP") for pod in expected_pods)
        
        logger.debug(f"{description} - Discovered IPs: {discovered_ips}, Expected IPs: {expected_ips}")
        
        return discovered_ips == expected_ips
    except Exception as e:
        logger.debug(f"Error verifying discovered IPs {description}: {e}")
        return False


async def wait_for_pod_discovery(operator, expected_pods, description, timeout=60):
    """Wait for operator to discover the expected pods and verify IPs match."""
    async def check_discovery():
        return verify_discovered_ips_match_pods(operator, expected_pods, description)
    
    success = await wait_for_condition(check_discovery, timeout=timeout)
    return success


def assert_operator_discovers_pods(operator, expected_pods, description):
    """Assert that operator has discovered the correct pod IPs with detailed error info."""
    discovered_urls = extract_production_urls_from_logs(operator)
    discovered_ips = extract_ips_from_urls(discovered_urls)
    expected_ips = set(getattr(pod.status, "podIP") for pod in expected_pods)
    
    assert discovered_ips == expected_ips, (
        f"{description}: Operator discovered wrong IPs. "
        f"Expected: {expected_ips}, Discovered: {discovered_ips}, URLs: {discovered_urls}"
    )


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

async def wait_for_pod_count(k8s_client, namespace, expected_count, timeout=60):
    """Wait for exactly the expected number of running HAProxy pods."""
    async def check_count():
        running_pods = get_running_haproxy_pods(k8s_client, namespace)
        return len(running_pods) == expected_count
    
    return await wait_for_condition(check_count, timeout=timeout)


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
    operator,
    haproxy_deployment,
    enhanced_configmap_with_pod_selector,
    k8s_client,
    k8s_namespace,
):
    """Test HAProxy pod discovery and scaling operations."""
    wait_for_operator_ready(operator)

    # Wait for initial 2 pods and verify discovery
    pods_ready = await wait_for_pod_count(k8s_client, k8s_namespace, 2)
    assert pods_ready, "HAProxy pods failed to become ready within 60 seconds"
    
    initial_pods = get_running_haproxy_pods(k8s_client, k8s_namespace)
    discovery_success = await wait_for_pod_discovery(operator, initial_pods, "Initial discovery")
    assert discovery_success, f"Controller failed to discover initial pods: {[getattr(p.status, 'podIP') for p in initial_pods]}"

    # Scale down to 1 replica and verify
    haproxy_deployment.scale(1)
    wait_for_deployment_replicas(haproxy_deployment, 1)
    
    scaled_ready = await wait_for_pod_count(k8s_client, k8s_namespace, 1)
    assert scaled_ready, "Scaling to 1 replica failed within 60 seconds"
    
    remaining_pods = get_running_haproxy_pods(k8s_client, k8s_namespace)
    scaling_detected = await wait_for_pod_discovery(operator, remaining_pods, "After scaling")
    assert scaling_detected, f"Controller failed to detect scaling: {[getattr(p.status, 'podIP') for p in remaining_pods]}"


@pytest.mark.asyncio
async def test_pod_discovery_with_pod_deletion(
    operator,
    haproxy_deployment,
    enhanced_configmap_with_pod_selector,
    k8s_client,
    k8s_namespace,
):
    """Test HAProxy pod discovery with individual pod deletion and recreation."""
    wait_for_operator_ready(operator)

    # Wait for initial 2 pods and verify discovery
    pods_ready = await wait_for_pod_count(k8s_client, k8s_namespace, 2)
    assert pods_ready, "HAProxy pods failed to become ready within 60 seconds"
    
    initial_pods = get_running_haproxy_pods(k8s_client, k8s_namespace)
    initial_ips = [getattr(pod.status, "podIP") for pod in initial_pods]
    
    discovery_success = await wait_for_pod_discovery(operator, initial_pods, "Initial discovery")
    assert discovery_success, f"Controller failed to discover initial pods: {initial_ips}"

    # Delete one pod and wait for removal
    pod_to_delete = initial_pods[0]
    deleted_pod_name = pod_to_delete.metadata.name
    deleted_pod_ip = getattr(pod_to_delete.status, "podIP")
    pod_to_delete.delete()
    
    logger.info(f"Deleted pod {deleted_pod_name} with IP {deleted_pod_ip}")

    # Wait for pod to be completely removed
    async def check_pod_deleted():
        current_pods = get_running_haproxy_pods(k8s_client, k8s_namespace)
        current_names = [p.metadata.name for p in current_pods]
        return deleted_pod_name not in current_names

    pod_deleted = await wait_for_condition(check_pod_deleted, timeout=60)
    assert pod_deleted, f"Deleted pod {deleted_pod_name} did not disappear within 60 seconds"

    # Wait for deployment to recreate and verify discovery
    wait_for_deployment_replicas(haproxy_deployment, 2)
    
    recreation_ready = await wait_for_pod_count(k8s_client, k8s_namespace, 2, timeout=120)
    assert recreation_ready, "Pod recreation failed within 120 seconds"
    
    final_pods = get_running_haproxy_pods(k8s_client, k8s_namespace)
    recreation_detected = await wait_for_pod_discovery(operator, final_pods, "After recreation")
    assert recreation_detected, "Controller failed to discover recreated pods"

    # Final verification
    final_ips = [getattr(pod.status, "podIP") for pod in final_pods]
    assert_operator_discovers_pods(operator, final_pods, "Final verification")
    
    # Check if deleted IP was reused
    if deleted_pod_ip in final_ips:
        logger.info(f"Pod IP {deleted_pod_ip} was reused by new pod")
    else:
        discovered_urls = extract_production_urls_from_logs(operator)
        discovered_ips = extract_ips_from_urls(discovered_urls)
        assert deleted_pod_ip not in discovered_ips, f"Operator still discovering deleted pod IP {deleted_pod_ip}"
    
    logger.info(f"✅ Pod deletion test passed: {initial_ips} → {final_ips}")
