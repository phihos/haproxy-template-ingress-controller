"""Test UI panel components."""

import pytest

from haproxy_template_ic.dashboard.ui_panels import (
    HeaderPanel,
    PodsPanel,
    TemplatesPanel,
    ResourcesPanel,
    PerformancePanel,
    ActivityPanel,
)
from haproxy_template_ic.dashboard.compatibility import CompatibilityLevel


class TestHeaderPanel:
    """Test HeaderPanel functionality."""

    @pytest.fixture
    def header_panel(self):
        """Create HeaderPanel instance."""
        return HeaderPanel()

    def test_render_basic_header(self, header_panel):
        """Test basic header rendering."""
        data = {"config": {"operator_version": "1.0.0", "namespace": "test-namespace"}}

        panel = header_panel.render(data, CompatibilityLevel.BASIC)

        assert panel is not None
        # Panel should be renderable by Rich
        assert hasattr(panel, "renderable") or hasattr(panel, "__rich__")

    def test_render_with_compatibility_info(self, header_panel):
        """Test header with compatibility information."""
        data = {"config": {"operator_version": "1.2.0", "namespace": "production"}}

        panel = header_panel.render(data, CompatibilityLevel.FULL)

        assert panel is not None

    def test_render_with_missing_data(self, header_panel):
        """Test header with missing data."""
        data = {}

        panel = header_panel.render(data, CompatibilityLevel.BASIC)

        # Should handle missing data gracefully
        assert panel is not None


class TestPodsPanel:
    """Test PodsPanel functionality."""

    @pytest.fixture
    def pods_panel(self):
        """Create PodsPanel instance."""
        return PodsPanel()

    def test_render_with_pods(self, pods_panel):
        """Test rendering with pod data."""
        data = {
            "pods": {
                "discovered": [
                    {
                        "name": "haproxy-1",
                        "ip": "10.0.1.1",
                        "status": "Running",
                        "ready": True,
                    },
                    {
                        "name": "haproxy-2",
                        "ip": "10.0.1.2",
                        "status": "Pending",
                        "ready": False,
                    },
                ]
            }
        }

        panel = pods_panel.render(data)

        assert panel is not None

    def test_render_with_empty_pods(self, pods_panel):
        """Test rendering with no pods."""
        data = {"pods": {"discovered": []}}

        panel = pods_panel.render(data)

        assert panel is not None

    def test_render_with_missing_pods_data(self, pods_panel):
        """Test rendering with missing pods data."""
        data = {}

        panel = pods_panel.render(data)

        assert panel is not None


class TestTemplatesPanel:
    """Test TemplatesPanel functionality."""

    @pytest.fixture
    def templates_panel(self):
        """Create TemplatesPanel instance."""
        return TemplatesPanel()

    def test_render_with_templates(self, templates_panel):
        """Test rendering with template data."""
        data = {
            "config": {
                "templates": {
                    "haproxy.cfg": {
                        "status": "rendered",
                        "last_updated": "2023-01-01T12:00:00Z",
                    },
                    "host.map": {"status": "error", "error": "Template syntax error"},
                }
            }
        }

        panel = templates_panel.render(data)

        assert panel is not None

    def test_render_with_no_templates(self, templates_panel):
        """Test rendering with no templates."""
        data = {"config": {"templates": {}}}

        panel = templates_panel.render(data)

        assert panel is not None

    def test_render_with_missing_config(self, templates_panel):
        """Test rendering with missing config data."""
        data = {}

        panel = templates_panel.render(data)

        assert panel is not None


class TestResourcesPanel:
    """Test ResourcesPanel functionality."""

    @pytest.fixture
    def resources_panel(self):
        """Create ResourcesPanel instance."""
        return ResourcesPanel()

    def test_render_with_resources(self, resources_panel):
        """Test rendering with resource data."""
        data = {
            "resources": {
                "ingresses": {
                    "total": 5,
                    "namespace_count": 2,
                    "namespaces": {"default": 3, "production": 2},
                    "memory_size": 12345,
                },
                "services": {
                    "total": 12,
                    "namespace_count": 3,
                    "namespaces": {"default": 5, "production": 4, "staging": 3},
                    "memory_size": 67890,
                },
            }
        }

        panel = resources_panel.render(data)

        assert panel is not None

    def test_render_with_many_namespaces(self, resources_panel):
        """Test rendering with many namespaces."""
        # Create data with many namespaces
        many_namespaces = {f"namespace-{i}": i + 1 for i in range(50)}
        data = {
            "resources": {
                "ingresses": {
                    "total": 100,
                    "namespace_count": 50,
                    "namespaces": many_namespaces,
                    "memory_size": 1024000,
                }
            }
        }

        panel = resources_panel.render(data)

        # Should handle many namespaces gracefully
        assert panel is not None

    def test_render_with_memory_sizes(self, resources_panel):
        """Test rendering with memory size information."""
        data = {
            "resources": {
                "ingresses": {
                    "total": 10,
                    "namespace_count": 2,
                    "namespaces": {"default": 6, "production": 4},
                    "memory_size": 1024,  # 1KB
                },
                "secrets": {
                    "total": 5,
                    "namespace_count": 1,
                    "namespaces": {"default": 5},
                    "memory_size": 5242880,  # 5MB
                },
                "services": {
                    "total": 3,
                    "namespace_count": 1,
                    "namespaces": {"default": 3},
                    "memory_size": 0,  # No memory size available
                },
            }
        }

        panel = resources_panel.render(data)

        assert panel is not None
        # The panel should handle various memory sizes gracefully

    def test_render_with_missing_indices(self, resources_panel):
        """Test rendering with missing indices."""
        data = {}

        panel = resources_panel.render(data)

        assert panel is not None


class TestPerformancePanel:
    """Test PerformancePanel functionality."""

    @pytest.fixture
    def performance_panel(self):
        """Create PerformancePanel instance."""
        return PerformancePanel()

    def test_render_with_full_compatibility(self, performance_panel):
        """Test rendering with full compatibility and performance data."""
        data = {
            "stats": {
                "template_renders": 150,
                "api_calls": 1200,
                "response_times": [10, 15, 12, 18, 20],
                "success_rate": 0.98,
            }
        }

        panel = performance_panel.render(data, CompatibilityLevel.FULL)

        assert panel is not None

    def test_render_with_enhanced_compatibility(self, performance_panel):
        """Test rendering with enhanced compatibility."""
        data = {"stats": {"template_renders": 75, "api_calls": 600}}

        panel = performance_panel.render(data, CompatibilityLevel.ENHANCED)

        assert panel is not None

    def test_render_with_basic_compatibility(self, performance_panel):
        """Test rendering with basic compatibility (limited features)."""
        data = {}

        panel = performance_panel.render(data, CompatibilityLevel.BASIC)

        # Should show "not available" message for basic compatibility
        assert panel is not None

    def test_render_with_missing_stats(self, performance_panel):
        """Test rendering with missing performance stats."""
        data = {}

        panel = performance_panel.render(data, CompatibilityLevel.FULL)

        assert panel is not None


class TestActivityPanel:
    """Test ActivityPanel functionality."""

    @pytest.fixture
    def activity_panel(self):
        """Create ActivityPanel instance."""
        return ActivityPanel()

    def test_render_with_full_compatibility(self, activity_panel):
        """Test rendering with full compatibility and activity data."""
        data = {
            "activity": {
                "recent_events": [
                    {
                        "timestamp": "2023-01-01T12:00:00Z",
                        "type": "config_update",
                        "message": "Updated haproxy.cfg template",
                    },
                    {
                        "timestamp": "2023-01-01T11:55:00Z",
                        "type": "pod_discovered",
                        "message": "Discovered new pod: haproxy-3",
                    },
                ]
            }
        }

        panel = activity_panel.render(data, CompatibilityLevel.FULL)

        assert panel is not None

    def test_render_with_basic_compatibility(self, activity_panel):
        """Test rendering with basic compatibility (no activity feed)."""
        data = {}

        panel = activity_panel.render(data, CompatibilityLevel.BASIC)

        # Should show "not available" message for basic compatibility
        assert panel is not None

    def test_render_with_empty_activity(self, activity_panel):
        """Test rendering with empty activity data."""
        data = {"activity": {"recent_events": []}}

        panel = activity_panel.render(data, CompatibilityLevel.FULL)

        assert panel is not None

    def test_render_with_missing_activity(self, activity_panel):
        """Test rendering with missing activity data."""
        data = {}

        panel = activity_panel.render(data, CompatibilityLevel.FULL)

        assert panel is not None


class TestPanelIntegration:
    """Test panel integration and consistency."""

    def test_all_panels_handle_empty_data(self):
        """Test that all panels handle empty data gracefully."""
        panels = [
            HeaderPanel(),
            PodsPanel(),
            TemplatesPanel(),
            ResourcesPanel(),
            PerformancePanel(),
            ActivityPanel(),
        ]

        empty_data = {}

        for panel in panels:
            if hasattr(panel, "render"):
                if panel.__class__.__name__ in [
                    "PerformancePanel",
                    "ActivityPanel",
                    "HeaderPanel",
                ]:
                    # These panels need compatibility level
                    result = panel.render(empty_data, CompatibilityLevel.BASIC)
                else:
                    result = panel.render(empty_data)

                assert result is not None, (
                    f"{panel.__class__.__name__} failed with empty data"
                )

    def test_panel_rich_compatibility(self):
        """Test that all panels produce Rich-compatible output."""
        panels = [
            HeaderPanel(),
            PodsPanel(),
            TemplatesPanel(),
            ResourcesPanel(),
            PerformancePanel(),
            ActivityPanel(),
        ]

        sample_data = {
            "config": {"operator_version": "1.0.0", "namespace": "test"},
            "pods": {"discovered": []},
            "indices": {"resources": {}},
            "stats": {},
            "activity": {"recent_events": []},
        }

        for panel in panels:
            if hasattr(panel, "render"):
                if panel.__class__.__name__ in [
                    "PerformancePanel",
                    "ActivityPanel",
                    "HeaderPanel",
                ]:
                    result = panel.render(sample_data, CompatibilityLevel.FULL)
                else:
                    result = panel.render(sample_data)

                # Should be Rich-compatible
                assert result is not None
                # Rich objects typically have these methods/attributes
                assert (
                    hasattr(result, "renderable")
                    or hasattr(result, "__rich__")
                    or hasattr(result, "__rich_console__")
                ), f"{panel.__class__.__name__} doesn't produce Rich-compatible output"
