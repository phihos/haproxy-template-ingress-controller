"""Unit tests for sync optimization functionality."""

import pytest

from haproxy_template_ic.models import (
    HAProxyConfigContext,
    TriggerContext,
    Config,
    TemplateContext,
    TemplateConfig,
    PodSelector,
    RenderedConfig,
    RenderedContent,
    IndexedResourceCollection,
)


class TestSyncOptimization:
    """Test the sync optimization functionality."""

    @pytest.mark.asyncio
    async def test_content_hash_computation(self):
        """Test content hash computation and change detection."""
        config = Config(
            pod_selector=PodSelector(match_labels={"app": "haproxy"}),
            haproxy_config=TemplateConfig(template="# Test config"),
        )

        context = HAProxyConfigContext(
            config=config,
            template_context=TemplateContext(namespace="default"),
            rendered_config=RenderedConfig(content="test config content"),
        )

        # Add some rendered content
        context.rendered_content = [
            RenderedContent(
                filename="test.map", content="map content", content_type="map"
            ),
            RenderedContent(
                filename="cert.pem", content="cert content", content_type="certificate"
            ),
        ]

        # First hash computation - should detect change
        hash1 = context.compute_all_content_hash()
        changed1 = await context.has_content_changed()
        assert changed1 is True

        # Second hash computation - should not detect change
        hash2 = context.compute_all_content_hash()
        changed2 = await context.has_content_changed()
        assert hash1 == hash2
        assert changed2 is False

        # Modify content and check again
        context.rendered_config = RenderedConfig(content="modified config content")
        hash3 = context.compute_all_content_hash()
        changed3 = await context.has_content_changed()
        assert hash1 != hash3
        assert changed3 is True

    @pytest.mark.asyncio
    async def test_pod_hash_computation(self):
        """Test pod hash computation and change detection."""
        config = Config(
            pod_selector=PodSelector(match_labels={"app": "haproxy"}),
            haproxy_config=TemplateConfig(template="# Test config"),
        )

        context = HAProxyConfigContext(
            config=config,
            template_context=TemplateContext(namespace="default"),
        )

        # Create mock pod collection
        pod_data1 = {
            ("default", "pod1"): {
                "metadata": {"namespace": "default", "name": "pod1"},
                "status": {"podIP": "10.0.0.1"},
            },
            ("default", "pod2"): {
                "metadata": {"namespace": "default", "name": "pod2"},
                "status": {"podIP": "10.0.0.2"},
            },
        }
        pods_collection = IndexedResourceCollection()
        # IndexedResourceCollection uses _internal_dict with list values
        for key, resource in pod_data1.items():
            pods_collection._internal_dict[key] = [resource]

        # First hash computation
        hash1 = context.compute_haproxy_pods_hash(pods_collection)
        changed1 = await context.have_pods_changed(pods_collection)
        assert changed1 is True

        # Second hash computation - should not detect change
        hash2 = context.compute_haproxy_pods_hash(pods_collection)
        changed2 = await context.have_pods_changed(pods_collection)
        assert hash1 == hash2
        assert changed2 is False

        # Create collection with additional pod
        pod_data2 = pod_data1.copy()
        pod_data2[("default", "pod3")] = {
            "metadata": {"namespace": "default", "name": "pod3"},
            "status": {"podIP": "10.0.0.3"},
        }
        pods_collection2 = IndexedResourceCollection()
        for key, resource in pod_data2.items():
            pods_collection2._internal_dict[key] = [resource]

        hash3 = context.compute_haproxy_pods_hash(pods_collection2)
        changed3 = await context.have_pods_changed(pods_collection2)
        assert hash1 != hash3
        assert changed3 is True

    def test_empty_pod_collection_hash(self):
        """Test pod hash computation with empty collection."""
        config = Config(
            pod_selector=PodSelector(match_labels={"app": "haproxy"}),
            haproxy_config=TemplateConfig(template="# Test config"),
        )

        context = HAProxyConfigContext(
            config=config,
            template_context=TemplateContext(namespace="default"),
        )

        # Test with None collection
        hash1 = context.compute_haproxy_pods_hash(None)
        assert hash1 == "xxh64:empty"

        # Test with empty collection
        empty_collection = IndexedResourceCollection()
        hash2 = context.compute_haproxy_pods_hash(empty_collection)
        assert hash2 == "xxh64:empty"

    def test_trigger_context_force_sync(self):
        """Test TriggerContext force_sync property."""
        # Resource changes - should not force sync
        ctx1 = TriggerContext(trigger_type="resource_changes")
        assert ctx1.force_sync is False

        # Pod changes - should force sync
        ctx2 = TriggerContext(trigger_type="pod_changes")
        assert ctx2.force_sync is True

        # Periodic refresh - should force sync
        ctx3 = TriggerContext(trigger_type="periodic_refresh")
        assert ctx3.force_sync is True

        # Pod changed flag - should force sync
        ctx4 = TriggerContext(trigger_type="resource_changes", pod_changed=True)
        assert ctx4.force_sync is True

    def test_deterministic_content_hash(self):
        """Test that content hash is deterministic."""
        config = Config(
            pod_selector=PodSelector(match_labels={"app": "haproxy"}),
            haproxy_config=TemplateConfig(template="# Test config"),
        )

        context1 = HAProxyConfigContext(
            config=config,
            template_context=TemplateContext(namespace="default"),
            rendered_config=RenderedConfig(content="test config content"),
        )

        context2 = HAProxyConfigContext(
            config=config,
            template_context=TemplateContext(namespace="default"),
            rendered_config=RenderedConfig(content="test config content"),
        )

        # Same content should produce same hash
        hash1 = context1.compute_all_content_hash()
        hash2 = context2.compute_all_content_hash()
        assert hash1 == hash2

    def test_deterministic_pod_hash(self):
        """Test that pod hash is deterministic and order-independent."""
        config = Config(
            pod_selector=PodSelector(match_labels={"app": "haproxy"}),
            haproxy_config=TemplateConfig(template="# Test config"),
        )

        context = HAProxyConfigContext(
            config=config,
            template_context=TemplateContext(namespace="default"),
        )

        # Create two collections with same pods in different order
        pod_data1 = {
            ("default", "pod1"): {
                "metadata": {"namespace": "default", "name": "pod1"},
                "status": {"podIP": "10.0.0.1"},
            },
            ("default", "pod2"): {
                "metadata": {"namespace": "default", "name": "pod2"},
                "status": {"podIP": "10.0.0.2"},
            },
        }

        pod_data2 = {
            ("default", "pod2"): {
                "metadata": {"namespace": "default", "name": "pod2"},
                "status": {"podIP": "10.0.0.2"},
            },
            ("default", "pod1"): {
                "metadata": {"namespace": "default", "name": "pod1"},
                "status": {"podIP": "10.0.0.1"},
            },
        }

        pods_collection1 = IndexedResourceCollection()
        for key, resource in pod_data1.items():
            pods_collection1._internal_dict[key] = [resource]

        pods_collection2 = IndexedResourceCollection()
        for key, resource in pod_data2.items():
            pods_collection2._internal_dict[key] = [resource]

        # Same pods in different order should produce same hash
        hash1 = context.compute_haproxy_pods_hash(pods_collection1)
        hash2 = context.compute_haproxy_pods_hash(pods_collection2)
        assert hash1 == hash2

    def test_content_type_ordering_in_hash(self):
        """Test that content is properly ordered by type and filename for deterministic hashing."""
        config = Config(
            pod_selector=PodSelector(match_labels={"app": "haproxy"}),
            haproxy_config=TemplateConfig(template="# Test config"),
        )

        # Create two contexts with same content in different orders
        context1 = HAProxyConfigContext(
            config=config,
            template_context=TemplateContext(namespace="default"),
            rendered_config=RenderedConfig(content="test config content"),
        )
        context1.rendered_content = [
            RenderedContent(
                filename="z.map", content="map content", content_type="map"
            ),
            RenderedContent(
                filename="a.pem", content="cert content", content_type="certificate"
            ),
        ]

        context2 = HAProxyConfigContext(
            config=config,
            template_context=TemplateContext(namespace="default"),
            rendered_config=RenderedConfig(content="test config content"),
        )
        context2.rendered_content = [
            RenderedContent(
                filename="a.pem", content="cert content", content_type="certificate"
            ),
            RenderedContent(
                filename="z.map", content="map content", content_type="map"
            ),
        ]

        # Should produce same hash regardless of order in list
        hash1 = context1.compute_all_content_hash()
        hash2 = context2.compute_all_content_hash()
        assert hash1 == hash2
