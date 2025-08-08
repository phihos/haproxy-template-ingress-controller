def test_basic_init(ingress_controller, kind_cluster, k8s_client, k8s_namespace):
    """The ingress controller should be initialized successfully after a few seconds."""
    line = ""
    for line in ingress_controller.logs(follow=True, timeout=10):
        if "Activity 'init_config' succeeded." in line:
            break
    assert "Activity 'init_config' succeeded." in line
