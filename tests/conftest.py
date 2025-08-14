import time
from typing import Dict

import kr8s
import pytest
import yaml
from kr8s.objects import (
    ClusterRoleBinding,
    ConfigMap,
    Namespace,
    Pod,
    ServiceAccount,
    Service,
    Secret,
)
from pytest import CollectReport, StashKey
from python_on_whales import DockerClient

CONTAINER_IMAGE_NAME = "haproxy-template-ic-acceptance-test:test"
CONTAINER_IMAGE_NAME_COVERAGE = "haproxy-template-ic-acceptance-test:test-coverage"


phase_report_key = StashKey[Dict[str, CollectReport]]()


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


@pytest.fixture(scope="session")
def project_root_path(request):
    return request.config.rootpath


@pytest.fixture(scope="session")
def docker_client():
    return DockerClient()


@pytest.fixture(scope="session")
def container_image(docker_client, project_root_path, kind_cluster, request):
    use_coverage = request.config.getoption("--coverage")
    image_name = CONTAINER_IMAGE_NAME_COVERAGE if use_coverage else CONTAINER_IMAGE_NAME
    target = "coverage" if use_coverage else "production"

    image = docker_client.build(
        context_path=str(project_root_path),
        tags=[image_name],
        target=target,
        output={"type": "docker"},
    )
    kind_cluster.load_docker_image(image_name)
    return image


@pytest.fixture(scope="session")
def k8s_client(kind_cluster):
    """Get a Kubernetes client for the Kind cluster."""
    return kr8s.api(kubeconfig=kind_cluster.kubeconfig_path)


@pytest.fixture
def k8s_namespace(request, k8s_client):
    # Generate a unique but short namespace name for each test (max 64 chars)
    import hashlib

    test_name = request.node.name
    # Create a short hash of the test name for uniqueness
    test_hash = hashlib.sha256(test_name.encode()).hexdigest()[:8]
    timestamp = time.strftime("%m%d-%H%M%S")  # Short timestamp format
    ns_name = f"test-{timestamp}-{test_hash}"
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


@pytest.fixture
def config_dict():
    return {
        "pod_selector": {"match_labels": {"foo": "bar"}},
        "haproxy_config": {
            "template": """
global
    daemon
    user haproxy
    group haproxy

defaults
    mode http
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend main
    bind *:80
    default_backend servers

backend servers
    balance roundrobin
"""
        },
        "watch_resources": {
            "ingresses": {
                "group": "networking.k8s.io",
                "version": "v1",
                "kind": "Ingress",
                "enable_validation_webhook": False,
            },
            "secrets": {
                "group": "",
                "version": "v1",
                "kind": "Secret",
                "enable_validation_webhook": False,
            },
            "endpoints": {
                "group": "discovery.k8s.io",
                "version": "v1",
                "kind": "EndpointSlice",
                "enable_validation_webhook": False,
            },
        },
    }


@pytest.fixture
def webhook_config_dict():
    """Configuration with webhooks enabled for webhook functionality tests."""
    return {
        "pod_selector": {"match_labels": {"foo": "bar"}},
        "haproxy_config": {
            "template": """
global
    daemon
    user haproxy
    group haproxy

defaults
    mode http
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend main
    bind *:80
    default_backend servers

backend servers
    balance roundrobin
"""
        },
        "watch_resources": {
            "ingresses": {
                "group": "networking.k8s.io",
                "version": "v1",
                "kind": "Ingress",
                "enable_validation_webhook": True,
            },
            "secrets": {
                "group": "",
                "version": "v1",
                "kind": "Secret",
                "enable_validation_webhook": True,
            },
            "endpoints": {
                "group": "discovery.k8s.io",
                "version": "v1",
                "kind": "EndpointSlice",
                "enable_validation_webhook": False,
            },
        },
    }


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
    from tests.webhook_certs import create_validating_webhook_config
    from kr8s.objects import APIObject

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


@pytest.fixture
def ingress_controller(k8s_client, k8s_namespace, container_image, configmap, request):
    # Wait for the default serviceaccount before proceeding
    wait_for_default_serviceaccount(k8s_client, k8s_namespace)

    ClusterRoleBinding(
        {
            "apiVersion": "v1",
            "name": "ConfigMap",
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

    # Check if test needs webhook functionality
    needs_webhook = "webhook" in request.node.name

    # Conditionally create webhook secret if needed
    volume_mounts = []
    volumes = []

    if needs_webhook:
        try:
            # Try to create webhook secret
            from tests.webhook_certs import (
                generate_webhook_certificates,
                create_cert_secret_manifest,
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
        except Exception as e:
            # If webhook secret creation fails, continue without it
            print(f"Warning: Failed to create webhook certificates: {e}")
            needs_webhook = False

    pod = Pod(
        {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "haproxy-template-ic",
                "namespace": k8s_namespace,
                "labels": {
                    "app.kubernetes.io/name": "haproxy-template-ic",
                    "app.kubernetes.io/instance": "acceptance-test",
                },
            },
            "spec": {
                "containers": [
                    {
                        "name": "haproxy-template-ic",
                        "image": container_image.repo_tags[0],
                        "ports": [
                            {"containerPort": 8080, "name": "healthz"},
                            {"containerPort": 9443, "name": "webhook"},
                        ],
                        "env": [
                            {"name": "CONFIGMAP_NAME", "value": configmap.name},
                            {"name": "VERBOSE", "value": "2"},
                        ],
                        "livenessProbe": {
                            "httpGet": {
                                "path": "/healthz",
                                "port": 8080,
                            }
                        },
                        "volumeMounts": volume_mounts,
                    }
                ],
                "volumes": volumes,
            },
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )
    pod.create()
    pod.wait("condition=Ready")

    if needs_webhook:
        # Create webhook service
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

    # Note: ValidatingAdmissionWebhook is automatically managed by kopf
    # when settings.admission.managed is configured in the operator startup

    return pod


@pytest.fixture(scope="function")
def collect_coverage(request, ingress_controller):
    """Collect coverage data from the running container if coverage is enabled."""
    yield

    if not request.config.getoption("--coverage"):
        return

    from .coverage_extraction import extract_coverage_from_pod

    coverage_file = extract_coverage_from_pod(
        ingress_controller, request.node.name, request.config.rootpath
    )

    if coverage_file:
        request.node.stash["coverage_file"] = coverage_file
