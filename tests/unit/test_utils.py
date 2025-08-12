from unittest.mock import patch, mock_open


from haproxy_template_ic.utils import get_current_namespace


def test_namespace_from_service_account_file():
    """Test getting namespace from service account file."""
    mock_namespace = "test-namespace"
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_namespace)):
            result = get_current_namespace()
            assert result == mock_namespace


def test_namespace_from_service_account_file_with_whitespace():
    """Test getting namespace from service account file with whitespace."""
    mock_namespace = "  test-namespace  \n"
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_namespace)):
            result = get_current_namespace()
            assert result == "test-namespace"


def test_namespace_from_kubeconfig_active_context():
    """Test getting namespace from kubeconfig active context."""
    mock_contexts = [
        {"name": "context1", "context": {"namespace": "ns1"}},
        {"name": "context2", "context": {"namespace": "ns2"}},
    ]
    mock_active_context = {"context": {"namespace": "active-ns"}}

    with patch("os.path.exists", return_value=False):
        with patch("kubernetes.config.list_kube_config_contexts") as mock_list:
            mock_list.return_value = (mock_contexts, mock_active_context)

            result = get_current_namespace()
            assert result == "active-ns"


def test_namespace_from_kubeconfig_specific_context():
    """Test getting namespace from kubeconfig specific context."""
    mock_contexts = [
        {"name": "context1", "context": {"namespace": "ns1"}},
        {"name": "context2", "context": {"namespace": "ns2"}},
    ]
    mock_active_context = {"context": {"namespace": "active-ns"}}

    with patch("os.path.exists", return_value=False):
        with patch("kubernetes.config.list_kube_config_contexts") as mock_list:
            mock_list.return_value = (mock_contexts, mock_active_context)

            result = get_current_namespace("context2")
            assert result == "ns2"


def test_namespace_from_kubeconfig_context_not_found():
    """Test getting namespace when specified context doesn't exist."""
    mock_contexts = [
        {"name": "context1", "context": {"namespace": "ns1"}},
    ]
    mock_active_context = {"context": {"namespace": "active-ns"}}

    with patch("os.path.exists", return_value=False):
        with patch("kubernetes.config.list_kube_config_contexts") as mock_list:
            mock_list.return_value = (mock_contexts, mock_active_context)

            result = get_current_namespace("nonexistent-context")
            assert result == "default"


def test_namespace_from_kubeconfig_no_namespace_in_context():
    """Test getting namespace when context has no namespace field."""
    mock_contexts = [
        {"name": "context1", "context": {}},  # No namespace
    ]
    mock_active_context = {"context": {}}  # No namespace

    with patch("os.path.exists", return_value=False):
        with patch("kubernetes.config.list_kube_config_contexts") as mock_list:
            mock_list.return_value = (mock_contexts, mock_active_context)

            result = get_current_namespace()
            assert result == "default"


def test_namespace_from_kubeconfig_key_error():
    """Test getting namespace when kubeconfig raises KeyError."""
    with patch("os.path.exists", return_value=False):
        with patch("kubernetes.config.list_kube_config_contexts") as mock_list:
            mock_list.side_effect = KeyError("Missing key")

            result = get_current_namespace()
            assert result == "default"


def test_namespace_from_kubeconfig_stop_iteration():
    """Test getting namespace when context search raises StopIteration."""
    mock_contexts = []
    mock_active_context = {"context": {"namespace": "active-ns"}}

    with patch("os.path.exists", return_value=False):
        with patch("kubernetes.config.list_kube_config_contexts") as mock_list:
            mock_list.return_value = (mock_contexts, mock_active_context)

            result = get_current_namespace("nonexistent-context")
            assert result == "default"


def test_namespace_priority_service_account_over_kubeconfig():
    """Test that service account file takes priority over kubeconfig."""
    mock_contexts = [
        {"name": "context1", "context": {"namespace": "kubeconfig-ns"}},
    ]
    mock_active_context = {"context": {"namespace": "kubeconfig-ns"}}

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="service-account-ns")):
            with patch("kubernetes.config.list_kube_config_contexts") as mock_list:
                mock_list.return_value = (mock_contexts, mock_active_context)

                result = get_current_namespace()
                assert result == "service-account-ns"
                # Verify kubeconfig was not called
                mock_list.assert_not_called()


def test_namespace_with_empty_service_account_file():
    """Test handling empty service account file."""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="")):
            result = get_current_namespace()
            assert result == ""


def test_namespace_with_whitespace_only_service_account_file():
    """Test handling service account file with only whitespace."""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="   \n\t  ")):
            result = get_current_namespace()
            assert result == ""
