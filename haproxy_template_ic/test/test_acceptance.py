import time

import pytest
import yaml


def assert_log_line(pod, log_line, timeout=10):
    full_log = ""
    start = time.time()
    for line in pod.logs(follow=True, timeout=timeout):
        full_log += f"{line}\n"
        if log_line in line:
            return full_log
        if time.time() - start > timeout:
            pytest.fail(f'Log line "{log_line}" not found in pod log:\n\n{full_log}')
    return None


@pytest.mark.slow
def test_basic_init(ingress_controller, collect_coverage):
    """The ingress controller should be initialized successfully after a few seconds."""
    assert_log_line(ingress_controller, "Activity 'init_config' succeeded.")


@pytest.mark.slow
def test_config_reload(ingress_controller, configmap, config_dict, collect_coverage):
    """Test that the ingress controller properly reloads configuration when the ConfigMap is updated.

    This test verifies that:
    1. The controller starts watching for configmap changes
    2. When the config is modified, it detects the change
    3. The controller stops and reinitializes with the new configuration
    4. The new configuration is successfully applied
    """
    assert_log_line(
        ingress_controller,
        "Starting the watch-stream for configmaps.v1 cluster-wide.",
    )
    config_dict["pod_selector"] = "baz=bar"
    configmap.patch({"data": {"config": yaml.dump(config_dict, Dumper=yaml.CDumper)}})
    assert_log_line(ingress_controller, "Config has changed:")
    assert_log_line(ingress_controller, "Stop-flag is raised. Operator is stopping.")
    assert_log_line(ingress_controller, "Config change detected. Reinitializing...")
    assert_log_line(ingress_controller, "Config initialization complete.")
