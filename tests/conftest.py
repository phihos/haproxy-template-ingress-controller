# =============================================================================
# IMPORTS
# =============================================================================

# Standard library imports
import hashlib
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

# Third-party imports
import httpx
import kr8s
import pytest
import yaml
from pytest import CollectReport, StashKey
from python_on_whales import DockerClient

# Kubernetes objects
from kr8s.objects import (
    APIObject,
    ClusterRoleBinding,
    ConfigMap,
    Deployment,
    Namespace,
    Pod,
    Secret,
    Service,
    ServiceAccount,
)
from kr8s._exceptions import ServerError

# Pytest plugins
from pytest_kind.cluster import KindCluster
from pytest_shared_session_scope import (
    CleanupToken,
    SetupToken,
    shared_session_scope_pickle,
)

# Local imports
from .coverage_extraction import extract_coverage_from_pod
from tests.e2e.utils.k8s_helpers import print_pod_logs_on_failure
from tests.webhook_certs import (
    create_cert_secret_manifest,
    create_validating_webhook_config,
    generate_webhook_certificates,
)


# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

CONTAINER_IMAGE_NAME = "haproxy-template-ic-acceptance-test:test"
CONTAINER_IMAGE_NAME_COVERAGE = "haproxy-template-ic-acceptance-test:test-coverage"

# Constants for timeouts and limits
DEFAULT_STALE_RESOURCE_AGE_HOURS = 24
MAX_NAMESPACE_CLEANUP_ATTEMPTS = 3
NAMESPACE_CLEANUP_RETRY_DELAY = 1
DEFAULT_POD_READY_TIMEOUT = 180
DEFAULT_SERVICEACCOUNT_WAIT_ATTEMPTS = 5

phase_report_key = StashKey[Dict[str, CollectReport]]()

# Module-level logger for better performance
logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def log_test_resource_summary(item: Any) -> None:
    """
    Log a summary of resources created/used during the test.

    This helps with debugging and understanding test resource usage patterns.

    Args:
        item: The pytest test item containing resource information
    """
    # Use module-level logger

    if not hasattr(item, "_test_resources"):
        return

    resources = item._test_resources
    summary_parts = []

    if "namespace" in resources:
        ns_info = resources["namespace"]
        summary_parts.append(f"namespace:{ns_info['name']}")

    if "pods" in resources:
        pod_count = len(resources["pods"])
        created_count = sum(1 for p in resources["pods"] if p.get("created", False))
        reused_count = sum(1 for p in resources["pods"] if p.get("reused", False))
        summary_parts.append(
            f"pods:{pod_count}(created:{created_count},reused:{reused_count})"
        )

    if summary_parts:
        logger.info(f"Test {item.name} resource usage: {', '.join(summary_parts)}")


def cleanup_stale_test_resources(
    k8s_client: Any, max_age_hours: int = DEFAULT_STALE_RESOURCE_AGE_HOURS
) -> None:
    """
    Clean up test resources that may have been left behind from failed test runs.

    This function identifies and removes namespaces and other resources created by
    tests that are older than the specified age.

    Args:
        k8s_client: Kubernetes API client instance
        max_age_hours: Maximum age in hours for resources to be considered stale
    """
    # Use module-level logger

    try:
        # Get all namespaces with our test labels
        namespaces = k8s_client.get(
            "namespaces", label_selector="created-by=haproxy-template-ic-tests"
        )
        stale_count = 0

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for ns in namespaces:
            try:
                # Parse creation timestamp
                created_at = datetime.fromisoformat(
                    ns.metadata.creationTimestamp.replace("Z", "+00:00")
                ).replace(tzinfo=None)

                if created_at < cutoff_time:
                    logger.info(
                        f"Cleaning up stale test namespace: {ns.metadata.name} (age: {datetime.now() - created_at})"
                    )
                    ns.delete()
                    stale_count += 1

            except (ValueError, AttributeError, OSError) as e:
                logger.warning(f"Could not process namespace {ns.metadata.name}: {e}")

        if stale_count > 0:
            logger.info(f"Cleaned up {stale_count} stale test namespace(s)")

    except (OSError, AttributeError) as e:
        logger.warning(f"Stale resource cleanup failed: {e}")


def wait_for_default_serviceaccount(k8s_client, k8s_namespace):
    """Wait for the default serviceaccount to be created in the given namespace."""
    attempt = 0
    while attempt < DEFAULT_SERVICEACCOUNT_WAIT_ATTEMPTS:
        try:
            sa = ServiceAccount.get("default", namespace=k8s_namespace, api=k8s_client)
            if sa:
                return sa
        except Exception:
            pass
        time.sleep(0.2)
        attempt += 1
    raise TimeoutError(
        f"Default serviceaccount in namespace {k8s_namespace} was not created within 1 second"
    )


def setup_webhook_volumes_and_mounts(k8s_client, k8s_namespace, needs_webhook):
    """
    Set up webhook certificate volumes and mounts if webhook functionality is needed.

    Returns:
        tuple: (volume_mounts, volumes, webhook_setup_successful)
    """
    volume_mounts = []
    volumes = []

    if not needs_webhook:
        return volume_mounts, volumes, False

    try:
        # Try to create webhook secret

        webhook_certificates = generate_webhook_certificates(
            "haproxy-template-ic-webhook", k8s_namespace
        )
        manifest = create_cert_secret_manifest(
            webhook_certificates, "haproxy-template-ic-webhook-certs", k8s_namespace
        )
        secret = Secret(manifest, namespace=k8s_namespace, api=k8s_client)
        secret.create()

        # Add volume mount and volume for webhook certificates
        volume_mounts.append(
            {
                "name": "webhook-certs",
                "mountPath": "/tmp/webhook-certs",
                "readOnly": True,
            }
        )
        volumes.append(
            {
                "name": "webhook-certs",
                "secret": {
                    "secretName": "haproxy-template-ic-webhook-certs",
                    "items": [
                        {"key": "tls.crt", "path": "webhook-cert.pem"},
                        {"key": "tls.key", "path": "webhook-key.pem"},
                        {"key": "ca.crt", "path": "webhook-ca.pem"},
                    ],
                },
            }
        )
        return volume_mounts, volumes, True
    except Exception as e:
        # If webhook secret creation fails, continue without it
        print(f"Warning: Failed to create webhook certificates: {e}")
        return volume_mounts, volumes, False


def create_webhook_service(k8s_client, k8s_namespace):
    """Create webhook service for the ingress controller."""
    webhook_service = Service(
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "haproxy-template-ic-webhook",
                "namespace": k8s_namespace,
                "labels": {
                    "app.kubernetes.io/name": "haproxy-template-ic",
                    "app.kubernetes.io/component": "webhook",
                },
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": 9443,
                        "targetPort": "webhook",
                        "protocol": "TCP",
                        "name": "webhook",
                    }
                ],
                "selector": {
                    "app.kubernetes.io/name": "haproxy-template-ic",
                    "app.kubernetes.io/instance": "acceptance-test",
                },
            },
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )
    webhook_service.create()
    return webhook_service


# =============================================================================
# PYTEST HOOKS AND OPTIONS
# =============================================================================


def pytest_addoption(parser):
    parser.addoption(
        "--keep-namespaces",
        action="store_true",
        default=False,
        help="Keep Kubernetes namespaces after testing.",
    )
    parser.addoption(
        "--keep-namespace-on-failure",
        action="store_true",
        default=False,
        help="Keep Kubernetes namespaces after test failure.",
    )
    parser.addoption(
        "--coverage",
        action="store_true",
        default=False,
        help="Enable coverage collection for acceptance tests.",
    )


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """For "--keep-namespace-on-failure" wee need to know the test results in fixtures. This hook provides that information."""
    # execute all other hooks to obtain the report object
    rep = yield
    # store test results for each phase of a call, which can
    # be "setup", "call", "teardown"
    item.stash.setdefault(phase_report_key, {})[rep.when] = rep
    return rep


# =============================================================================
# INFRASTRUCTURE FIXTURES (cluster/docker setup)
# =============================================================================


@shared_session_scope_pickle()
def kind_cluster(request):
    """
    Provide a Kubernetes kind cluster as test fixture that works with pytest-xdist.

    This fixture ensures that only one kind cluster is created even when running
    tests in parallel with pytest-xdist, using a lock file for coordination.
    """
    name = request.config.getoption("cluster_name")
    keep = request.config.getoption("keep_cluster")
    kubeconfig = request.config.getoption("kubeconfig")
    image = request.config.getoption("kind_image")
    kind_path = request.config.getoption("kind_bin")
    kubectl_path = request.config.getoption("kind_kubectl_bin")

    cluster = yield
    if cluster is SetupToken.FIRST:
        cluster = KindCluster(
            name,
            Path(kubeconfig) if kubeconfig else None,
            image=image,
            kind_path=Path(kind_path) if kind_path else None,
            kubectl_path=Path(kubectl_path) if kubectl_path else None,
        )

        # Fix for empty kubeconfig when reusing existing clusters
        # Check if the kind cluster exists and fix kubeconfig before calling create()
        try:
            # Check if cluster exists
            out = subprocess.check_output(["kind", "get", "clusters"], encoding="utf-8")
            cluster_exists = name in out.splitlines()

            if cluster_exists:
                # Check if kubeconfig needs to be exported from existing cluster
                need_export = False

                if not cluster.kubeconfig_path.exists():
                    # Kubeconfig doesn't exist at all
                    need_export = True
                else:
                    # Check if kubeconfig exists but is empty or missing required fields
                    try:
                        with open(cluster.kubeconfig_path, "r") as f:
                            config_content = yaml.safe_load(f)

                        # If kubeconfig is empty, missing clusters, or missing current-context, export from kind
                        if (
                            not config_content
                            or "clusters" not in config_content
                            or not config_content["clusters"]
                            or "current-context" not in config_content
                            or not config_content.get("current-context")
                        ):
                            need_export = True

                    except (yaml.YAMLError, FileNotFoundError):
                        # If kubeconfig is malformed, regenerate it
                        need_export = True

                if need_export:
                    # Export kubeconfig from the existing cluster
                    kubeconfig_output = subprocess.check_output(
                        ["kind", "get", "kubeconfig", "--name", name],
                        encoding="utf-8",
                    )

                    with open(cluster.kubeconfig_path, "w") as f:
                        f.write(kubeconfig_output)

        except subprocess.CalledProcessError:
            # kind command failed, let create() handle cluster creation
            pass

        # Use test-specific config to avoid port conflicts
        config_path = request.config.rootpath / "kind-config-test.yaml"
        cluster.create(config_file=config_path)

    token: CleanupToken = yield cluster

    if token is CleanupToken.LAST and not keep:
        cluster.delete()


@pytest.fixture(scope="session")
def project_root_path(request):
    """Get the project root path from pytest configuration."""
    return request.config.rootpath


@pytest.fixture(scope="session")
def docker_client():
    """Provide a Docker client for container operations."""
    return DockerClient()


@shared_session_scope_pickle()
def container_image(docker_client, project_root_path, kind_cluster, request):
    """
    Build and provide the container image for testing.

    Builds either production or coverage image based on --coverage flag,
    loads it into the Kind cluster, and shares across test sessions.
    """
    use_coverage = request.config.getoption("--coverage")
    image_name = CONTAINER_IMAGE_NAME_COVERAGE if use_coverage else CONTAINER_IMAGE_NAME
    target = "coverage" if use_coverage else "production"

    image = yield
    if image is SetupToken.FIRST:
        image = docker_client.build(
            context_path=str(project_root_path),
            tags=[image_name],
            target=target,
            output={"type": "docker"},
        )
        kind_cluster.load_docker_image(image_name)
    yield image


# =============================================================================
# KUBERNETES CLIENT FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def k8s_client(kind_cluster):
    """Get a Kubernetes client for the Kind cluster."""
    return kr8s.api(kubeconfig=kind_cluster.kubeconfig_path)


@pytest.fixture
def k8s_namespace(request, k8s_client):
    """
    Create a unique Kubernetes namespace for each test.

    Generates a unique namespace name using test name hash, timestamp, and worker ID
    for parallel execution. Automatically cleans up unless --keep-namespaces or
    --keep-namespace-on-failure flags are used.

    Resource tracking ensures proper cleanup and provides debugging information.
    """

    # Use module-level logger

    # Generate a unique but short namespace name for each test (max 64 chars)
    test_name = request.node.name
    # Create a short hash of the test name for uniqueness
    test_hash = hashlib.sha256(test_name.encode()).hexdigest()[:8]
    # Add microseconds and worker ID for parallel execution uniqueness
    worker_id = getattr(request.config, "workerinput", {}).get("workerid", "master")
    timestamp = time.strftime("%m%d-%H%M%S")
    microseconds = str(int(time.time() * 1000000) % 1000000)[
        :3
    ]  # Last 3 digits of microseconds
    ns_name = (
        f"test-{timestamp}-{microseconds}-{worker_id.replace('gw', '')}-{test_hash}"
    )

    ns = Namespace(
        {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": ns_name,
                "labels": {
                    "test-name": test_name[:63],  # Kubernetes label limit
                    "worker-id": worker_id,
                    "created-by": "haproxy-template-ic-tests",
                },
            },
        }
    )

    try:
        ns.create()
        logger.debug(f"Created namespace {ns_name} for test {test_name}")

        # Track namespace creation for debugging
        if not hasattr(request.node, "_test_resources"):
            request.node._test_resources = {}
        request.node._test_resources["namespace"] = {
            "name": ns_name,
            "created_at": timestamp,
            "worker_id": worker_id,
        }

    except Exception as e:
        logger.error(f"Failed to create namespace {ns_name}: {e}")
        raise

    yield ns.name

    # Determine cleanup strategy based on test results and configuration
    report = request.node.stash[phase_report_key]
    test_failed = ("setup" in report and report["setup"].failed) or (
        "call" in report and report["call"].failed
    )

    should_keep_namespace = request.config.getoption("--keep-namespaces") or (
        test_failed and request.config.getoption("--keep-namespace-on-failure")
    )

    if should_keep_namespace:
        logger.info(
            f"Keeping namespace {ns_name} for debugging (test_failed={test_failed})"
        )
        # Add annotation to preserved namespace for identification
        try:
            ns.refresh()
            if not ns.metadata.annotations:
                ns.metadata.annotations = {}
            ns.metadata.annotations.update(
                {
                    "haproxy-template-ic-test/preserved": "true",
                    "haproxy-template-ic-test/test-name": test_name,
                    "haproxy-template-ic-test/failure-reason": "test-failed"
                    if test_failed
                    else "keep-requested",
                }
            )
            ns.patch()
        except Exception as e:
            logger.warning(f"Could not annotate preserved namespace {ns_name}: {e}")
    else:
        # Attempt graceful cleanup with retry
        for attempt in range(MAX_NAMESPACE_CLEANUP_ATTEMPTS):
            try:
                ns.delete()
                logger.debug(f"Successfully deleted namespace {ns_name}")
                break
            except Exception as e:
                if attempt < MAX_NAMESPACE_CLEANUP_ATTEMPTS - 1:
                    logger.warning(
                        f"Cleanup attempt {attempt + 1} failed for namespace {ns_name}: {e}, retrying..."
                    )
                    time.sleep(NAMESPACE_CLEANUP_RETRY_DELAY)
                else:
                    logger.error(
                        f"Failed to cleanup namespace {ns_name} after {MAX_NAMESPACE_CLEANUP_ATTEMPTS} attempts: {e}"
                    )
                    # Don't raise - test already completed, just log the issue


# =============================================================================
# CONFIGURATION FIXTURES
# =============================================================================


@pytest.fixture
def config_dict():
    """Provide basic configuration dictionary for HAProxy template ingress controller."""
    return {
        "pod_selector": {
            "match_labels": {
                "app": "haproxy",
                "component": "loadbalancer",
            }
        },
        "haproxy_config": {
            "template": """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    balance roundrobin
    # Servers configured by controller
"""
        },
        "maps": {
            "host.map": {
                "template": "# Host mapping\n{% for key, ingress in resources.get('ingresses', {}).items() %}\n# {{ ingress.metadata.name }}\n{% endfor %}"
            }
        },
        "watched_resources": {
            "ingresses": {
                "api_version": "networking.k8s.io/v1",
                "kind": "Ingress",
                "enable_validation_webhook": True,
            },
            "secrets": {
                "api_version": "v1",
                "kind": "Secret",
                "enable_validation_webhook": True,
            },
            "endpoints": {
                "api_version": "discovery.k8s.io/v1",
                "kind": "EndpointSlice",
                "enable_validation_webhook": False,
            },
        },
    }


@pytest.fixture
def webhook_config_dict(config_dict):
    """Configuration with webhooks enabled for webhook functionality tests."""
    # Use the same base config as config_dict since webhooks are enabled by default now
    return config_dict


@pytest.fixture
def webhook_configmap(webhook_config_dict, k8s_client, k8s_namespace):
    """ConfigMap with webhook validation enabled for webhook functionality tests."""
    cm = ConfigMap(
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "haproxy-template-ic-webhook-config",
                "namespace": k8s_namespace,
            },
            "data": {
                "config": yaml.dump(webhook_config_dict, Dumper=yaml.CDumper),
            },
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )
    cm.create()
    return cm


@pytest.fixture
def configmap(config_dict, k8s_client, k8s_namespace):
    """Create ConfigMap with basic HAProxy template ingress controller configuration."""
    cm = ConfigMap(
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "haproxy-template-ic-config",
                "namespace": k8s_namespace,
            },
            "data": {
                "config": yaml.dump(config_dict, Dumper=yaml.CDumper),
            },
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )
    cm.create()
    return cm


# =============================================================================
# WEBHOOK-RELATED FIXTURES
# =============================================================================


@pytest.fixture
def webhook_certificates(k8s_namespace):
    """Generate webhook certificates for the test namespace."""

    return generate_webhook_certificates("haproxy-template-ic-webhook", k8s_namespace)


@pytest.fixture
def webhook_secret(webhook_certificates, k8s_client, k8s_namespace):
    """Create Kubernetes Secret with webhook certificates."""

    manifest = create_cert_secret_manifest(
        webhook_certificates, "haproxy-template-ic-webhook-certs", k8s_namespace
    )
    secret = Secret(manifest, namespace=k8s_namespace, api=k8s_client)
    secret.create()
    return secret


@pytest.fixture
def credentials_secret(k8s_client, k8s_namespace):
    """Create Kubernetes Secret with HAProxy Dataplane API credentials."""
    manifest = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": "haproxy-template-ic-credentials",
            "namespace": k8s_namespace,
        },
        "type": "Opaque",
        "stringData": {
            "dataplane_username": "admin",
            "dataplane_password": "adminpass",
            "validation_username": "admin",
            "validation_password": "validationpass",
        },
    }
    secret = Secret(manifest, namespace=k8s_namespace, api=k8s_client)
    secret.create()
    return secret


@pytest.fixture
def validating_webhook_config(webhook_certificates, k8s_namespace, k8s_client):
    """Create ValidatingAdmissionWebhook configuration."""

    manifest = create_validating_webhook_config(
        webhook_name=f"haproxy-template-ic-webhook-{k8s_namespace}",
        service_name="haproxy-template-ic-webhook",
        service_namespace=k8s_namespace,
        ca_bundle=webhook_certificates.ca_bundle,
        target_namespace=k8s_namespace,
    )

    webhook = APIObject(manifest, api=k8s_client)
    webhook.create()

    yield webhook

    try:
        webhook.delete()
    except Exception:
        pass


# =============================================================================
# PRODUCTION HAPROXY FIXTURES
# =============================================================================


@pytest.fixture
def haproxy_config_with_health():
    """Provide HAProxy config template with health endpoint."""
    return """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin
    
userlist dataplaneapi
    user admin password adminpass

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    default_backend servers

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    balance roundrobin
    # Servers configured by controller
"""


@pytest.fixture
def unified_haproxy_configmap(k8s_client, k8s_namespace):
    """
    Create unified ConfigMap with HAProxy startup scripts and templates for E2E tests.

    This provides the same unified approach used in production deployments.
    """

    configmap = ConfigMap(
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "haproxy-universal-test",
                "namespace": k8s_namespace,
                "labels": {
                    "app": "haproxy-template-ic",
                    "component": "universal-config-test",
                },
            },
            "data": {
                "startup.sh": """#!/bin/sh
set -e

echo "Starting HAProxy Universal Script (type: ${CONTAINER_TYPE:-unknown})"

# Create required directories
mkdir -p /etc/haproxy /etc/haproxy/maps /etc/haproxy/certs /etc/haproxy/errors /etc/haproxy/ssl /etc/haproxy/general /etc/haproxy/spoe
mkdir -p /var/lib/dataplaneapi/transactions /var/lib/dataplaneapi/backups
chown -R haproxy:haproxy /etc/haproxy /var/lib/dataplaneapi 2>/dev/null || true

# Generate appropriate config based on container type
if [ "$CONTAINER_TYPE" = "dataplane" ]; then
  echo "Configuring Dataplane API..."
  sed "s/PASSWORD_TOKEN/${HAPROXY_PASSWORD}/g" \\
      /opt/haproxy/dataplane.template > /etc/haproxy/dataplaneapi.yaml
  echo "Starting HAProxy Dataplane API..."
  exec dataplaneapi
else
  echo "Configuring HAProxy..."
  sed "s/PASSWORD_TOKEN/${HAPROXY_PASSWORD}/g" \\
      /opt/haproxy/haproxy.template > /etc/haproxy/haproxy.cfg
  echo "Configuration written to /etc/haproxy/haproxy.cfg"
  echo "Starting HAProxy in master-worker mode..."
  exec haproxy -W -db -S "/etc/haproxy/haproxy-master.sock" -- /etc/haproxy/haproxy.cfg
fi
""",
                "haproxy.template": """global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

userlist dataplaneapi
    user admin insecure-password PASSWORD_TOKEN

defaults
    mode http
    timeout connect 1s
    timeout client 1s
    timeout server 1s

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
        
frontend main
    bind *:80
    default_backend servers
    
backend servers
    balance roundrobin
    # Servers configured by controller
""",
                "dataplane.template": """config_version: 2
name: haproxy-dataplaneapi
dataplaneapi:
  host: 0.0.0.0
  port: 5555
  user:
    - name: admin
      password: PASSWORD_TOKEN
      insecure: true
  transaction:
    transaction_dir: /var/lib/dataplaneapi/transactions
    backups_number: 10
    backups_dir: /var/lib/dataplaneapi/backups
  resources:
    maps_dir: /etc/haproxy/maps
    ssl_certs_dir: /etc/haproxy/ssl
    general_storage_dir: /etc/haproxy/general
    spoe_dir: /etc/haproxy/spoe
haproxy:
  config_file: /etc/haproxy/haproxy.cfg
  haproxy_bin: /usr/local/sbin/haproxy
  reload:
    reload_delay: 1
    reload_cmd: /opt/haproxy/reload.sh
    restart_cmd: /opt/haproxy/reload.sh
    reload_strategy: custom
log_targets:
  - log_to: stdout
    log_level: info
    log_types:
    - access
    - app
""",
                "reload.sh": """#!/bin/sh
echo reload | nc local:/etc/haproxy/haproxy-master.sock
""",
            },
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )

    configmap.create()
    return configmap


@pytest.fixture
def haproxy_deployment(k8s_client, k8s_namespace, unified_haproxy_configmap, request):
    """
    Create scalable HAProxy deployment for testing.

    Creates a deployment with configurable replicas (default 2) that matches
    the controller's pod selector. Each pod has HAProxy + Dataplane API containers.

    Use with parametrize: @pytest.mark.parametrize('haproxy_deployment', [3], indirect=True)
    """
    replicas = getattr(request, "param", 2) if hasattr(request, "param") else 2

    deployment = Deployment(
        {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "haproxy-production",
                "namespace": k8s_namespace,
                "labels": {
                    "app": "haproxy",
                    "component": "loadbalancer",
                },
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "matchLabels": {
                        "app": "haproxy",
                        "component": "loadbalancer",
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "haproxy",
                            "component": "loadbalancer",
                            "haproxy-template-ic/role": "production",
                        },
                        "annotations": {
                            "haproxy-template-ic/dataplane-port": "5555",
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "haproxy",
                                "image": "haproxytech/haproxy-alpine:3.1",
                                "imagePullPolicy": "IfNotPresent",
                                "command": ["/opt/haproxy/startup.sh"],
                                "ports": [
                                    {"containerPort": 80, "name": "http"},
                                    {"containerPort": 8404, "name": "healthz"},
                                ],
                                "env": [
                                    {"name": "HAPROXY_PASSWORD", "value": "adminpass"},
                                    {"name": "CONTAINER_TYPE", "value": "haproxy"},
                                ],
                                "volumeMounts": [
                                    {
                                        "name": "universal-config",
                                        "mountPath": "/opt/haproxy",
                                    },
                                    {
                                        "name": "haproxy-config",
                                        "mountPath": "/etc/haproxy",
                                    },
                                ],
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/healthz",
                                        "port": 8404,
                                    },
                                    "initialDelaySeconds": 2,
                                    "periodSeconds": 2,
                                    "failureThreshold": 5,
                                },
                            },
                            {
                                "name": "dataplane-api",
                                "image": "haproxytech/haproxy-alpine:3.1",
                                "imagePullPolicy": "IfNotPresent",
                                "command": ["/opt/haproxy/startup.sh"],
                                "ports": [{"containerPort": 5555, "name": "dataplane"}],
                                "env": [
                                    {"name": "HAPROXY_PASSWORD", "value": "adminpass"},
                                    {"name": "CONTAINER_TYPE", "value": "dataplane"},
                                ],
                                "volumeMounts": [
                                    {
                                        "name": "universal-config",
                                        "mountPath": "/opt/haproxy",
                                    },
                                    {
                                        "name": "haproxy-config",
                                        "mountPath": "/etc/haproxy",
                                    },
                                ],
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": "/v3/info",
                                        "port": 5555,
                                        "httpHeaders": [
                                            {
                                                "name": "Authorization",
                                                "value": "Basic YWRtaW46YWRtaW5wYXNz",
                                            }
                                        ],
                                    },
                                    "initialDelaySeconds": 15,
                                    "periodSeconds": 10,
                                    "failureThreshold": 3,
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/v3/info",
                                        "port": 5555,
                                        "httpHeaders": [
                                            {
                                                "name": "Authorization",
                                                "value": "Basic YWRtaW46YWRtaW5wYXNz",
                                            }
                                        ],
                                    },
                                    "initialDelaySeconds": 10,
                                    "periodSeconds": 5,
                                },
                            },
                        ],
                        "volumes": [
                            {"name": "haproxy-config", "emptyDir": {}},
                            {
                                "name": "universal-config",
                                "configMap": {
                                    "name": "haproxy-universal-test",
                                    "defaultMode": 0o755,
                                },
                            },
                        ],
                    },
                },
            },
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )

    deployment.create()

    # Wait for deployment to be ready

    max_wait = 60
    start_time = time.time()
    while time.time() - start_time < max_wait:
        deployment.refresh()
        if getattr(deployment.status, "readyReplicas", 0) == replicas:
            break
        time.sleep(2)
    else:
        raise TimeoutError(
            f"HAProxy deployment did not become ready with {replicas} replicas in time"
        )

    return deployment


@pytest.fixture
def haproxy_production_pods(k8s_client, k8s_namespace, request):
    """
    Create production HAProxy pods with 2 containers each (haproxy + dataplane-api).

    Each pod has:
    - HAProxy container with initial config that has no health endpoint
    - Dataplane API container on port 5555
    - Shared emptyDir volume for configuration files
    - Readiness probe that fails until controller pushes config with health endpoint
    - Labels for controller pod selector matching
    """
    # Create 2 production HAProxy pods by default
    num_pods = getattr(request, "param", 2) if hasattr(request, "param") else 2
    pods = []

    for i in range(num_pods):
        pod_name = f"haproxy-production-{i}"

        # Initial HAProxy config without health endpoint (makes pod not ready)
        initial_haproxy_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin
    
userlist dataplaneapi
    user admin password adminpass
    
defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms  
    timeout server 50000ms
    
frontend main
    bind *:80
    default_backend servers
    
backend servers
    balance roundrobin
    # No servers initially - will be configured by controller
"""

        pod = Pod(
            {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "name": pod_name,
                    "namespace": k8s_namespace,
                    "labels": {
                        "app": "haproxy",
                        "component": "loadbalancer",
                        "haproxy-template-ic/role": "production",
                    },
                    "annotations": {
                        "haproxy-template-ic/dataplane-port": "5555",
                    },
                },
                "spec": {
                    "containers": [
                        {
                            "name": "haproxy",
                            "image": "haproxytech/haproxy-alpine:3.1",
                            "ports": [
                                {"containerPort": 80, "name": "http"},
                                {
                                    "containerPort": 8404,
                                    "name": "healthz",
                                },  # Health port (not active initially)
                            ],
                            "volumeMounts": [
                                {
                                    "name": "haproxy-config",
                                    "mountPath": "/usr/local/etc/haproxy",
                                },
                                {
                                    "name": "haproxy-maps",
                                    "mountPath": "/etc/haproxy/maps",
                                },
                                {
                                    "name": "haproxy-certs",
                                    "mountPath": "/etc/haproxy/certs",
                                },
                            ],
                            "command": ["haproxy"],
                            "args": ["-f", "/usr/local/etc/haproxy/haproxy.cfg", "-W"],
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/healthz",
                                    "port": 8404,
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 3,
                                "failureThreshold": 10,
                            },
                        },
                        {
                            "name": "dataplane-api",
                            "image": "haproxytech/haproxy-alpine:3.1",
                            "ports": [{"containerPort": 5555, "name": "dataplane"}],
                            "volumeMounts": [
                                {
                                    "name": "haproxy-config",
                                    "mountPath": "/usr/local/etc/haproxy",
                                },
                                {
                                    "name": "haproxy-maps",
                                    "mountPath": "/etc/haproxy/maps",
                                },
                                {
                                    "name": "haproxy-certs",
                                    "mountPath": "/etc/haproxy/certs",
                                },
                            ],
                            "command": ["dataplaneapi"],
                            "args": [
                                "--host",
                                "0.0.0.0",
                                "--port",
                                "5555",
                                "--haproxy-bin",
                                "/usr/local/sbin/haproxy",
                                "--config-file",
                                "/usr/local/etc/haproxy/haproxy.cfg",
                                "--reload-cmd",
                                "kill -USR2 1",
                                "--reload-delay",
                                "2",
                                "--userlist",
                                "dataplaneapi",
                            ],
                            "env": [
                                {"name": "DATAPLANE_API_USER", "value": "admin"},
                                {
                                    "name": "DATAPLANE_API_PASSWORD",
                                    "value": "adminpass",
                                },
                            ],
                        },
                    ],
                    "volumes": [
                        {"name": "haproxy-config", "emptyDir": {}},
                        {"name": "haproxy-maps", "emptyDir": {}},
                        {"name": "haproxy-certs", "emptyDir": {}},
                    ],
                    "initContainers": [
                        {
                            "name": "init-config",
                            "image": "busybox:1.36",
                            "command": ["sh", "-c"],
                            "args": [
                                f'echo "{initial_haproxy_config}" > /usr/local/etc/haproxy/haproxy.cfg'
                            ],
                            "volumeMounts": [
                                {
                                    "name": "haproxy-config",
                                    "mountPath": "/usr/local/etc/haproxy",
                                }
                            ],
                        }
                    ],
                },
            },
            namespace=k8s_namespace,
            api=k8s_client,
        )

        pod.create()
        pods.append(pod)

        # Note: Pods will NOT be ready initially due to failing health check
        # Controller must push config with health endpoint to make them ready

    return pods


@pytest.fixture
def haproxy_dataplane_clients(haproxy_production_pods, k8s_namespace):
    """
    Create Dataplane API clients for each production HAProxy pod.

    Provides HTTP clients configured to communicate with the Dataplane API
    containers in the production HAProxy pods.
    """

    clients = []
    for pod in haproxy_production_pods:
        pod_ip = pod.status.podIP
        if not pod_ip:
            # Wait for pod IP assignment

            for _ in range(30):
                pod.refresh()
                if pod.status.podIP:
                    pod_ip = pod.status.podIP
                    break
                time.sleep(1)
            else:
                raise TimeoutError(f"Pod {pod.name} did not get IP address")

        client = httpx.AsyncClient(
            base_url=f"http://{pod_ip}:5555",
            auth=("admin", "adminpass"),
            timeout=30.0,
        )
        clients.append(client)

    return clients


# =============================================================================
# MAIN APPLICATION FIXTURES
# =============================================================================


@pytest.fixture
def controller_with_validation_sidecar(
    k8s_client, k8s_namespace, container_image, configmap, credentials_secret, request
):
    """
    Create and deploy HAProxy template ingress controller with validation sidecar.

    Creates a controller pod with 3 containers:
    - Main controller: The HAProxy Template IC operator
    - Validation HAProxy: HAProxy instance for configuration validation
    - Validation Dataplane API: Dataplane API for validation HAProxy

    Sets up RBAC permissions, webhook support, and waits for pod readiness.
    """
    # Wait for the default serviceaccount before proceeding
    wait_for_default_serviceaccount(k8s_client, k8s_namespace)

    # Create or reuse ClusterRoleBinding (idempotent)
    crb_name = f"ingress-controller-cluster-admin-{k8s_namespace}"
    try:
        ClusterRoleBinding(
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRoleBinding",
                "metadata": {
                    "name": crb_name,
                },
                "subjects": [
                    {
                        "kind": "ServiceAccount",
                        "name": "default",
                        "namespace": k8s_namespace,
                    }
                ],
                "roleRef": {
                    "kind": "ClusterRole",
                    "name": "cluster-admin",
                    "apiGroup": "rbac.authorization.k8s.io",
                },
            },
            api=k8s_client,
        ).create()
    except Exception as e:
        # Handle specific k8s errors for idempotent resource creation

        if isinstance(e, ServerError) and "already exists" in str(e):
            # Resource already exists, which is expected in test environments
            # Use module-level logger
            logger.debug(f"Reusing existing ClusterRoleBinding: {crb_name}")
        else:
            # Use module-level logger
            logger.error(f"Failed to create ClusterRoleBinding {crb_name}: {e}")
            raise

    # Check if test needs webhook functionality and set up webhook volumes
    needs_webhook = "webhook" in request.node.name
    volume_mounts, volumes, webhook_setup_successful = setup_webhook_volumes_and_mounts(
        k8s_client, k8s_namespace, needs_webhook
    )
    needs_webhook = needs_webhook and webhook_setup_successful

    # Add shared volumes for validation sidecar
    volumes.extend(
        [
            {"name": "validation-haproxy-config", "emptyDir": {}},
            {"name": "validation-haproxy-maps", "emptyDir": {}},
            {"name": "validation-haproxy-certs", "emptyDir": {}},
            {"name": "management-socket", "emptyDir": {}},
        ]
    )

    # Base HAProxy config for validation sidecar (minimal working config)
    validation_haproxy_config = """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin
    
userlist dataplaneapi
    user admin password adminpass
    
defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    
frontend validation
    bind *:8081
    default_backend validation_backend
    
backend validation_backend
    balance roundrobin
    # Validation backend - no real servers needed
"""

    # Pod specification with 3 containers
    pod_spec = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "haproxy-template-ic",
            "namespace": k8s_namespace,
            "labels": {
                "app.kubernetes.io/name": "haproxy-template-ic",
                "app.kubernetes.io/instance": "acceptance-test",
                "haproxy-template-ic/role": "controller",
            },
        },
        "spec": {
            "containers": [
                # Main controller container
                {
                    "name": "haproxy-template-ic",
                    "image": container_image.repo_tags[0],
                    "args": ["run"],
                    "ports": [
                        {"containerPort": 8080, "name": "healthz"},
                        {"containerPort": 9443, "name": "webhook"}
                        if needs_webhook
                        else {},
                        {"containerPort": 9090, "name": "metrics"},
                    ],
                    "env": [
                        {"name": "CONFIGMAP_NAME", "value": configmap.name},
                        {
                            "name": "SECRET_NAME",
                            "value": "haproxy-template-ic-credentials",
                        },
                        {"name": "VERBOSE", "value": "2"},
                        {
                            "name": "SOCKET_PATH",
                            "value": "/run/haproxy-template-ic/management.sock",
                        },
                    ],
                    "livenessProbe": {
                        "httpGet": {
                            "path": "/healthz",
                            "port": 8080,
                        },
                        "initialDelaySeconds": 30,
                        "periodSeconds": 30,
                        "timeoutSeconds": 5,
                        "failureThreshold": 3,
                    },
                    "readinessProbe": {
                        "httpGet": {
                            "path": "/healthz",
                            "port": 8080,
                        },
                        "initialDelaySeconds": 15,
                        "periodSeconds": 10,
                        "timeoutSeconds": 5,
                        "failureThreshold": 10,
                    },
                    "volumeMounts": [
                        {
                            "name": "management-socket",
                            "mountPath": "/run/haproxy-template-ic",
                        },
                    ]
                    + volume_mounts,
                },
                # Validation HAProxy sidecar
                {
                    "name": "validation-haproxy",
                    "image": "haproxytech/haproxy-alpine:3.1",
                    "ports": [
                        {"containerPort": 8081, "name": "validation-http"},
                    ],
                    "volumeMounts": [
                        {
                            "name": "validation-haproxy-config",
                            "mountPath": "/usr/local/etc/haproxy",
                        },
                        {
                            "name": "validation-haproxy-maps",
                            "mountPath": "/etc/haproxy/maps",
                        },
                        {
                            "name": "validation-haproxy-certs",
                            "mountPath": "/etc/haproxy/certs",
                        },
                    ],
                    "command": ["haproxy"],
                    "args": ["-f", "/usr/local/etc/haproxy/haproxy.cfg", "-W"],
                    "labels": {"haproxy-template-ic/role": "validation"},
                },
                # Validation Dataplane API sidecar
                {
                    "name": "validation-dataplane-api",
                    "image": "haproxytech/haproxy-alpine:3.1",
                    "ports": [
                        {"containerPort": 5556, "name": "validation-api"},
                    ],
                    "volumeMounts": [
                        {
                            "name": "validation-haproxy-config",
                            "mountPath": "/usr/local/etc/haproxy",
                        },
                        {
                            "name": "validation-haproxy-maps",
                            "mountPath": "/etc/haproxy/maps",
                        },
                        {
                            "name": "validation-haproxy-certs",
                            "mountPath": "/etc/haproxy/certs",
                        },
                    ],
                    "command": ["dataplaneapi"],
                    "args": [
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "5556",
                        "--haproxy-bin",
                        "/usr/local/sbin/haproxy",
                        "--config-file",
                        "/usr/local/etc/haproxy/haproxy.cfg",
                        "--reload-cmd",
                        "kill -USR2 $(pgrep -f 'haproxy.*validation')",
                        "--restart-cmd",
                        "kill -TERM $(pgrep -f 'haproxy.*validation') && sleep 1 && /usr/local/sbin/haproxy -f /usr/local/etc/haproxy/haproxy.cfg -W",
                        "--reload-delay",
                        "1",
                        "--userlist",
                        "dataplaneapi",
                    ],
                    "env": [
                        {"name": "DATAPLANE_API_USER", "value": "admin"},
                        {"name": "DATAPLANE_API_PASSWORD", "value": "adminpass"},
                    ],
                },
            ],
            "volumes": volumes,
            "initContainers": [
                {
                    "name": "init-validation-config",
                    "image": "busybox:1.36",
                    "command": ["sh", "-c"],
                    "args": [
                        f'echo "{validation_haproxy_config}" > /usr/local/etc/haproxy/haproxy.cfg'
                    ],
                    "volumeMounts": [
                        {
                            "name": "validation-haproxy-config",
                            "mountPath": "/usr/local/etc/haproxy",
                        }
                    ],
                }
            ],
        },
    }

    # Remove empty webhook port if not needed
    if not needs_webhook:
        pod_spec["spec"]["containers"][0]["ports"] = [
            port for port in pod_spec["spec"]["containers"][0]["ports"] if port
        ]

    pod = Pod(pod_spec, namespace=k8s_namespace, api=k8s_client)

    # Try to create pod, or reuse if it already exists
    # Use module-level logger

    try:
        pod.create()
        logger.debug(f"Created new controller pod in namespace {k8s_namespace}")

        # Track pod creation for resource management
        if hasattr(request, "node") and hasattr(request.node, "_test_resources"):
            if "pods" not in request.node._test_resources:
                request.node._test_resources["pods"] = []
            request.node._test_resources["pods"].append(
                {
                    "name": "haproxy-template-ic",
                    "namespace": k8s_namespace,
                    "created": True,
                    "reused": False,
                }
            )

    except Exception as e:
        # Handle specific k8s errors for idempotent pod creation

        if isinstance(e, ServerError) and "already exists" in str(e):
            # Pod already exists, get the existing one
            logger.debug(
                f"Reusing existing pod: haproxy-template-ic in namespace {k8s_namespace}"
            )
            pod = Pod.get(
                "haproxy-template-ic", namespace=k8s_namespace, api=k8s_client
            )

            # Track pod reuse
            if hasattr(request, "node") and hasattr(request.node, "_test_resources"):
                if "pods" not in request.node._test_resources:
                    request.node._test_resources["pods"] = []
                request.node._test_resources["pods"].append(
                    {
                        "name": "haproxy-template-ic",
                        "namespace": k8s_namespace,
                        "created": False,
                        "reused": True,
                    }
                )
        else:
            logger.error(
                f"Failed to create pod haproxy-template-ic in namespace {k8s_namespace}: {e}"
            )
            raise

    # Wait for pod readiness with enhanced logging
    try:
        logger.debug(
            f"Waiting for controller pod readiness (timeout={DEFAULT_POD_READY_TIMEOUT}s)"
        )
        pod.wait("condition=Ready", timeout=DEFAULT_POD_READY_TIMEOUT)
        logger.debug(f"Controller pod ready in namespace {k8s_namespace}")
    except Exception as e:
        logger.error(f"Controller pod failed to become ready: {e}")
        # Log pod status for debugging
        try:
            pod.refresh()
            logger.error(
                f"Pod status: {pod.status.phase if hasattr(pod.status, 'phase') else 'unknown'}"
            )
            if hasattr(pod.status, "containerStatuses"):
                for container_status in pod.status.containerStatuses or []:
                    logger.error(
                        f"Container {container_status.name}: ready={container_status.ready}"
                    )
        except (AttributeError, OSError):
            logger.error("Could not retrieve pod status for debugging")
        raise

    if needs_webhook:
        create_webhook_service(k8s_client, k8s_namespace)

    return pod


@pytest.fixture
def simple_controller(
    k8s_client, k8s_namespace, container_image, configmap, credentials_secret, request
):
    """
    Create a simplified HAProxy template ingress controller WITHOUT validation sidecars.
    This fixture is optimized for faster startup and should be used for tests that don't
    require the validation functionality.
    """
    # Wait for the default serviceaccount before proceeding
    wait_for_default_serviceaccount(k8s_client, k8s_namespace)

    # Create or reuse ClusterRoleBinding (idempotent)
    crb_name = f"ingress-controller-cluster-admin-{k8s_namespace}"
    try:
        ClusterRoleBinding(
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRoleBinding",
                "metadata": {
                    "name": crb_name,
                },
                "subjects": [
                    {
                        "kind": "ServiceAccount",
                        "name": "default",
                        "namespace": k8s_namespace,
                    }
                ],
                "roleRef": {
                    "kind": "ClusterRole",
                    "name": "cluster-admin",
                    "apiGroup": "rbac.authorization.k8s.io",
                },
            },
            api=k8s_client,
        ).create()
    except Exception as e:
        # Handle specific k8s errors for idempotent resource creation

        if isinstance(e, ServerError) and "already exists" in str(e):
            # Resource already exists, which is expected in test environments
            # Use module-level logger
            logger.debug(f"Reusing existing ClusterRoleBinding: {crb_name}")
        else:
            # Use module-level logger
            logger.error(f"Failed to create ClusterRoleBinding {crb_name}: {e}")
            raise

    # Check if test needs webhook functionality
    needs_webhook = "webhook" in request.node.name
    volume_mounts, volumes, webhook_setup_successful = setup_webhook_volumes_and_mounts(
        k8s_client, k8s_namespace, needs_webhook
    )
    needs_webhook = needs_webhook and webhook_setup_successful

    # Simplified pod specification with only main controller container
    pod_spec = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "haproxy-template-ic",
            "namespace": k8s_namespace,
            "labels": {
                "app.kubernetes.io/name": "haproxy-template-ic",
                "app.kubernetes.io/instance": "acceptance-test",
                "haproxy-template-ic/role": "controller",
            },
        },
        "spec": {
            "containers": [
                # Main controller container only
                {
                    "name": "haproxy-template-ic",
                    "image": container_image.repo_tags[0],
                    "args": ["run"],
                    "ports": [
                        {"containerPort": 8080, "name": "healthz"},
                        {"containerPort": 9443, "name": "webhook"}
                        if needs_webhook
                        else {},
                        {"containerPort": 9090, "name": "metrics"},
                    ],
                    "env": [
                        {"name": "CONFIGMAP_NAME", "value": configmap.name},
                        {
                            "name": "SECRET_NAME",
                            "value": "haproxy-template-ic-credentials",
                        },
                        {"name": "VERBOSE", "value": "2"},
                        {
                            "name": "SOCKET_PATH",
                            "value": "/run/haproxy-template-ic/management.sock",
                        },
                    ],
                    "livenessProbe": {
                        "httpGet": {
                            "path": "/healthz",
                            "port": 8080,
                        },
                        "initialDelaySeconds": 20,
                        "periodSeconds": 30,
                        "timeoutSeconds": 5,
                        "failureThreshold": 3,
                    },
                    "readinessProbe": {
                        "httpGet": {
                            "path": "/healthz",
                            "port": 8080,
                        },
                        "initialDelaySeconds": 10,
                        "periodSeconds": 10,
                        "timeoutSeconds": 5,
                        "failureThreshold": 6,
                    },
                    "volumeMounts": [
                        {
                            "name": "management-socket",
                            "mountPath": "/run/haproxy-template-ic",
                        },
                    ]
                    + volume_mounts,
                },
            ],
            "volumes": volumes + [{"name": "management-socket", "emptyDir": {}}],
        },
    }

    # Remove empty webhook port if not needed
    if not needs_webhook:
        pod_spec["spec"]["containers"][0]["ports"] = [
            port for port in pod_spec["spec"]["containers"][0]["ports"] if port
        ]

    pod = Pod(pod_spec, namespace=k8s_namespace, api=k8s_client)

    # Try to create pod, or reuse if it already exists
    try:
        pod.create()
    except Exception as e:
        # Handle specific k8s errors for idempotent pod creation

        if isinstance(e, ServerError) and "already exists" in str(e):
            # Pod already exists, get the existing one
            # Use module-level logger
            logger.debug(
                f"Reusing existing pod: haproxy-template-ic in namespace {k8s_namespace}"
            )
            pod = Pod.get(
                "haproxy-template-ic", namespace=k8s_namespace, api=k8s_client
            )
        else:
            # Use module-level logger
            logger.error(
                f"Failed to create pod haproxy-template-ic in namespace {k8s_namespace}: {e}"
            )
            raise

    pod.wait("condition=Ready", timeout=90)  # Shorter timeout for simpler pod

    if needs_webhook:
        create_webhook_service(k8s_client, k8s_namespace)

    return pod


# Legacy fixture for backward compatibility
@pytest.fixture
def ingress_controller(controller_with_validation_sidecar):
    """Legacy fixture name for backward compatibility."""
    return controller_with_validation_sidecar


# =============================================================================
# HELPER FIXTURES FOR CONFIGURATION AND TESTING
# =============================================================================


@pytest.fixture
def validation_dataplane_client(controller_with_validation_sidecar):
    """
    Create Dataplane API client for the validation sidecar.

    Provides HTTP client configured to communicate with the validation
    Dataplane API container in the controller pod.
    """

    # Get pod IP
    controller_pod = controller_with_validation_sidecar
    pod_ip = controller_pod.status.podIP
    if not pod_ip:
        # Wait for pod IP assignment
        for _ in range(30):
            controller_pod.refresh()
            if controller_pod.status.podIP:
                pod_ip = controller_pod.status.podIP
                break
            time.sleep(1)
        else:
            raise TimeoutError("Controller pod did not get IP address")

    return httpx.AsyncClient(
        base_url=f"http://{pod_ip}:5556",
        auth=("admin", "adminpass"),
        timeout=30.0,
    )


@pytest.fixture
def enhanced_configmap_with_pod_selector(k8s_client, k8s_namespace):
    """
    ConfigMap with pod selector that matches production HAProxy pods.

    This fixture creates a complete configuration that includes:
    - Pod selector matching production HAProxy pods
    - Template configuration with health endpoint
    - Map templates for routing configuration
    """
    config_dict = {
        "pod_selector": {
            "match_labels": {
                "app": "haproxy",
                "component": "loadbalancer",
            }
        },
        "haproxy_config": {
            "template": """
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin
    
defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    
frontend main
    bind *:80
    default_backend servers
    
frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
    
backend servers
    balance roundrobin
    # Servers configured by controller
"""
        },
        "maps": {
            "host.map": {
                "template": "# Host mapping file\n# Generated by HAProxy Template IC"
            },
            "backends.map": {
                "template": "# Backend mapping file\n# Generated by HAProxy Template IC"
            },
        },
        "watched_resources": {
            "ingresses": {
                "api_version": "networking.k8s.io/v1",
                "kind": "Ingress",
                "enable_validation_webhook": False,
            },
            "services": {
                "api_version": "v1",
                "kind": "Service",
                "enable_validation_webhook": False,
            },
        },
    }

    cm = ConfigMap(
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "haproxy-template-ic-enhanced-config",
                "namespace": k8s_namespace,
            },
            "data": {
                "config": yaml.dump(config_dict, Dumper=yaml.CDumper),
            },
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )
    cm.create()
    return cm


@pytest.fixture(scope="function")
def collect_coverage(request, controller_with_validation_sidecar):
    """
    Collect coverage data from the running container if --coverage flag is enabled.

    Extracts coverage data after test completion and stores the file path
    in the test node stash for potential aggregation.
    """
    yield

    if not request.config.getoption("--coverage"):
        return

    coverage_file = extract_coverage_from_pod(
        controller_with_validation_sidecar, request.node.name, request.config.rootpath
    )

    if coverage_file:
        request.node.stash["coverage_file"] = coverage_file


def pytest_runtest_teardown(item, nextitem):
    """
    Print haproxy-template-ic pod logs when acceptance tests fail.

    This hook runs after each test and checks if it was an acceptance test that failed.
    If so, it attempts to retrieve and print the pod logs for debugging.

    Environment Variables:
        PYTEST_DISABLE_POD_LOG_PRINTING: Set to 'true' to disable automatic log printing
        PYTEST_POD_FIXTURE_NAMES: Comma-separated list of fixture names to search for pods
    """

    # Use module-level logger

    # Check if log printing is globally disabled
    if os.environ.get("PYTEST_DISABLE_POD_LOG_PRINTING", "").lower() == "true":
        return

    # Check if this is an acceptance test
    is_acceptance_test = any(
        marker.name == "acceptance" for marker in item.iter_markers()
    )
    if not is_acceptance_test:
        return

    # Log resource summary for all tests (not just failures)
    log_test_resource_summary(item)

    # Check if the test failed
    reports = item.stash.get(phase_report_key, {})
    test_failed = any(report.failed for report in reports.values())

    if test_failed:
        try:
            # Get configurable fixture names from environment or use defaults
            fixture_names_str = os.environ.get(
                "PYTEST_POD_FIXTURE_NAMES",
                "ingress_controller,controller_with_validation_sidecar,simple_controller",
            )
            fixture_names = [name.strip() for name in fixture_names_str.split(",")]

            # Try to find a controller pod from fixture names
            pod = None
            found_fixture = None

            for fixture_name in fixture_names:
                try:
                    if hasattr(item, "funcargs") and fixture_name in item.funcargs:
                        pod_candidate = item.funcargs[fixture_name]
                        # Basic validation that this looks like a pod object
                        if pod_candidate and hasattr(pod_candidate, "logs"):
                            pod = pod_candidate
                            found_fixture = fixture_name
                            logger.debug(f"Found pod from fixture: {fixture_name}")
                            break
                except (KeyError, AttributeError) as e:
                    logger.debug(f"Could not get pod from fixture {fixture_name}: {e}")
                    continue

            if pod is not None:
                try:
                    logger.info(
                        f"Printing pod logs for failed test {item.name} using fixture {found_fixture}"
                    )
                    print_pod_logs_on_failure(pod, item.name)
                except ImportError as e:
                    logger.error(f"Could not import log printing function: {e}")
                    print(f"⚠️ Could not import pod log printing function: {e}")
            else:
                logger.info(
                    f"No haproxy-template-ic pod found for test {item.name}. Available fixtures: {list(getattr(item, 'funcargs', {}).keys())}"
                )
                print("ℹ️ No haproxy-template-ic pod found for log retrieval")

        except Exception as e:
            logger.error(
                f"Unexpected error in pod log retrieval for test {item.name}: {e}"
            )
            print(f"⚠️ Failed to retrieve pod logs for debugging: {e}")
