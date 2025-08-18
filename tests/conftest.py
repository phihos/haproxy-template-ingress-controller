# =============================================================================
# IMPORTS
# =============================================================================

# Standard library imports
import pickle
import subprocess
import time
from pathlib import Path
from typing import Any, Dict

# Third-party imports
import kr8s
import pytest
import yaml
from pytest import CollectReport, StashKey
from python_on_whales import DockerClient

# Kubernetes objects
from kr8s.objects import (
    ClusterRoleBinding,
    ConfigMap,
    Namespace,
    Pod,
    Secret,
    Service,
    ServiceAccount,
)

# Pytest plugins
from pytest_kind.cluster import KindCluster
from pytest_shared_session_scope import (
    CleanupToken,
    SetupToken,
    StoreValueNotExists,
    shared_session_scope_fixture,
)
from pytest_shared_session_scope.store import LocalFileStoreMixin


# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

CONTAINER_IMAGE_NAME = "haproxy-template-ic-acceptance-test:test"
CONTAINER_IMAGE_NAME_COVERAGE = "haproxy-template-ic-acceptance-test:test-coverage"

phase_report_key = StashKey[Dict[str, CollectReport]]()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def wait_for_default_serviceaccount(k8s_client, k8s_namespace):
    """Wait for the default serviceaccount to be created in the given namespace."""
    max_attempts = 5
    attempt = 0
    while attempt < max_attempts:
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
        from tests.webhook_certs import (
            create_cert_secret_manifest,
            generate_webhook_certificates,
        )

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
# CUSTOM STORE CLASSES
# =============================================================================


class PickleStore(LocalFileStoreMixin):
    """Store that reads and writes pickle data using the pickle module."""

    def read(self, identifier: str, fixture_values: dict[str, Any]) -> str:
        """Read data from a file."""
        path = self._get_path(identifier, fixture_values["tmp_path_factory"])
        try:
            with open(path, "rb") as f:
                # Pickle the 'data' dictionary using the highest protocol available.
                return pickle.load(f)
        except FileNotFoundError:
            raise StoreValueNotExists()

    def write(self, identifier: str, data: str, fixture_values: dict[str, Any]):
        """Write data to a file."""
        path = self._get_path(identifier, fixture_values["tmp_path_factory"])
        with open(path, "wb") as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)


# =============================================================================
# INFRASTRUCTURE FIXTURES (cluster/docker setup)
# =============================================================================


@shared_session_scope_fixture(PickleStore())
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
                # Check if kubeconfig exists but is empty or missing clusters
                if cluster.kubeconfig_path.exists():
                    try:
                        with open(cluster.kubeconfig_path, "r") as f:
                            config_content = yaml.safe_load(f)

                        # If kubeconfig is empty or missing clusters, export from kind
                        if (
                            not config_content
                            or "clusters" not in config_content
                            or not config_content["clusters"]
                        ):
                            # Export kubeconfig from the existing cluster
                            kubeconfig_output = subprocess.check_output(
                                ["kind", "get", "kubeconfig", "--name", name],
                                encoding="utf-8",
                            )

                            with open(cluster.kubeconfig_path, "w") as f:
                                f.write(kubeconfig_output)

                    except (yaml.YAMLError, FileNotFoundError):
                        # If kubeconfig is malformed, regenerate it
                        kubeconfig_output = subprocess.check_output(
                            ["kind", "get", "kubeconfig", "--name", name],
                            encoding="utf-8",
                        )

                        with open(cluster.kubeconfig_path, "w") as f:
                            f.write(kubeconfig_output)

        except subprocess.CalledProcessError:
            # kind command failed, let create() handle cluster creation
            pass

        cluster.create()

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


@shared_session_scope_fixture(PickleStore())
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
    """
    # Generate a unique but short namespace name for each test (max 64 chars)
    import hashlib

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
            },
        }
    )
    ns.create()
    yield ns.name
    report = request.node.stash[phase_report_key]
    test_failed = ("setup" in report and report["setup"].failed) or (
        "call" in report and report["call"].failed
    )
    if not request.config.getoption("--keep-namespaces") and not (
        test_failed and request.config.getoption("--keep-namespace-on-failure")
    ):
        ns.delete()


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

frontend health
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }

backend servers
    balance roundrobin
    # Servers configured by controller
"""
        },
        "maps": {
            "/etc/haproxy/maps/host.map": {
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
    from tests.webhook_certs import generate_webhook_certificates

    return generate_webhook_certificates("haproxy-template-ic-webhook", k8s_namespace)


@pytest.fixture
def webhook_secret(webhook_certificates, k8s_client, k8s_namespace):
    """Create Kubernetes Secret with webhook certificates."""
    from tests.webhook_certs import create_cert_secret_manifest

    manifest = create_cert_secret_manifest(
        webhook_certificates, "haproxy-template-ic-webhook-certs", k8s_namespace
    )
    secret = Secret(manifest, namespace=k8s_namespace, api=k8s_client)
    secret.create()
    return secret


@pytest.fixture
def validating_webhook_config(webhook_certificates, k8s_namespace, k8s_client):
    """Create ValidatingAdmissionWebhook configuration."""
    from kr8s.objects import APIObject

    from tests.webhook_certs import create_validating_webhook_config

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
                            "image": "haproxytech/haproxy-debian:3.0",
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
                            "image": "haproxytech/haproxy-debian:3.0",
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
                                "controller",
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
    import httpx

    clients = []
    for pod in haproxy_production_pods:
        pod_ip = pod.status.podIP
        if not pod_ip:
            # Wait for pod IP assignment
            import time

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
    k8s_client, k8s_namespace, container_image, configmap, request
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

    ClusterRoleBinding(
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "ClusterRoleBinding",
            "metadata": {
                "name": f"ingress-controller-cluster-admin-{k8s_namespace}",
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
                    "ports": [
                        {"containerPort": 8080, "name": "healthz"},
                        {"containerPort": 9443, "name": "webhook"}
                        if needs_webhook
                        else {},
                        {"containerPort": 9090, "name": "metrics"},
                    ],
                    "env": [
                        {"name": "CONFIGMAP_NAME", "value": configmap.name},
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
                        "initialDelaySeconds": 10,
                        "periodSeconds": 30,
                    },
                    "readinessProbe": {
                        "httpGet": {
                            "path": "/healthz",
                            "port": 8080,
                        },
                        "initialDelaySeconds": 5,
                        "periodSeconds": 10,
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
                    "image": "haproxytech/haproxy-debian:3.0",
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
                    "image": "haproxytech/haproxy-debian:3.0",
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
                        "validation",
                    ],
                    "env": [
                        {"name": "DATAPLANE_API_USER", "value": "admin"},
                        {"name": "DATAPLANE_API_PASSWORD", "value": "validationpass"},
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
    pod.create()
    pod.wait("condition=Ready", timeout=120)

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
    import httpx
    import time

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
        auth=("admin", "validationpass"),
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
    
frontend health
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
    
backend servers
    balance roundrobin
    # Servers configured by controller
"""
        },
        "maps": {
            "/etc/haproxy/maps/host.map": {
                "template": "# Host mapping file\n# Generated by HAProxy Template IC"
            },
            "/etc/haproxy/maps/backends.map": {
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

    from .coverage_extraction import extract_coverage_from_pod

    coverage_file = extract_coverage_from_pod(
        controller_with_validation_sidecar, request.node.name, request.config.rootpath
    )

    if coverage_file:
        request.node.stash["coverage_file"] = coverage_file
