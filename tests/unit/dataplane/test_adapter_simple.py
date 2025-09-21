"""
Simple unit tests for Dataplane Adapter core functionality.

Tests basic adapter functionality without complex mocking.
"""

from haproxy_template_ic.dataplane.adapter import ReloadInfo


def test_reload_info_creation():
    """Test ReloadInfo creation with no reload."""
    reload_info = ReloadInfo()
    assert reload_info.reload_id is None
    assert not reload_info.reload_triggered


def test_reload_info_with_reload():
    """Test ReloadInfo creation with reload."""
    reload_info = ReloadInfo(reload_id="test-reload-123")
    assert reload_info.reload_id == "test-reload-123"
    assert reload_info.reload_triggered


def test_reload_info_combine_no_reloads():
    """Test combining ReloadInfo instances with no reloads."""
    r1 = ReloadInfo()
    r2 = ReloadInfo()

    combined = ReloadInfo.combine(r1, r2)

    assert not combined.reload_triggered
    assert combined.reload_id is None


def test_reload_info_combine_with_reload():
    """Test combining ReloadInfo instances with one reload."""
    r1 = ReloadInfo()
    r2 = ReloadInfo(reload_id="test-reload-456")

    combined = ReloadInfo.combine(r1, r2)

    assert combined.reload_triggered
    assert combined.reload_id == "test-reload-456"


def test_reload_info_combine_multiple_reloads():
    """Test combining ReloadInfo instances with multiple reloads."""
    r1 = ReloadInfo(reload_id="first-reload")
    r2 = ReloadInfo(reload_id="second-reload")

    combined = ReloadInfo.combine(r1, r2)

    assert combined.reload_triggered
    # Should use the first reload_id found
    assert combined.reload_id == "first-reload"
