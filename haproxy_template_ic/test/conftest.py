import time
from typing import Dict

import kr8s
import pytest
from kr8s.objects import ClusterRoleBinding, ConfigMap, Namespace, Pod
from pytest import CollectReport, StashKey
from python_on_whales import DockerClient

CONTAINER_IMAGE_NAME = "haproxy-template-ic-acceptance-test:test"


phase_report_key = StashKey[Dict[str, CollectReport]]()


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
def container_image(docker_client, project_root_path, kind_cluster):
    image = docker_client.build(
        context_path=str(project_root_path), tags=[CONTAINER_IMAGE_NAME]
    )
    kind_cluster.load_docker_image(CONTAINER_IMAGE_NAME)
    return image


@pytest.fixture(scope="session")
def k8s_client(kind_cluster):
    return kr8s.api(kubeconfig=kind_cluster.kubeconfig_path)


@pytest.fixture
def k8s_namespace(request, k8s_client):
    # generate a unique but human-recognizable namespace name for each test
    ns_name = f"{time.strftime('%Y-%m-%d-%H-%M-%S')}-{''.join(char for char in request.node.name if char.isalnum())}"
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
        "pod_selector": "foo=bar",
    }


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
            "data": config_dict,
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )
    cm.create()
    return cm


@pytest.fixture
def ingress_controller(k8s_client, k8s_namespace, container_image, configmap):
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
    pod = Pod(
        {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "haproxy-template-ic",
                "namespace": k8s_namespace,
            },
            "spec": {
                "containers": [
                    {
                        "name": "haproxy-template-ic",
                        "image": container_image.repo_tags[0],
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
                    }
                ]
            },
        },
        namespace=k8s_namespace,
        api=k8s_client,
    )
    pod.create()
    pod.wait("condition=Ready")
    return pod
