"""
Tests for resource timestamp tracking in the operator.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from haproxy_template_ic.operator.k8s_resources import update_resource_index
from haproxy_template_ic.models.resource_metadata import ResourceTypeMetadata


class TestResourceTimestampTracking:
    """Tests for resource timestamp tracking functionality."""

    @pytest.fixture
    def mock_memo(self):
        """Create a mock memo object with necessary attributes."""

        class MockConfig:
            def __init__(self):
                self.watched_resources = {
                    "ingresses": Mock(
                        api_version="networking.k8s.io/v1",
                        kind="Ingress",
                        index_by=["metadata.namespace", "metadata.name"],
                    )
                }

        class MockResources:
            def __init__(self):
                self.indices = {}
                self.resource_metadata = {}

        class MockMemo:
            def __init__(self):
                self.config = MockConfig()
                self.resources = MockResources()
                self.debouncer = Mock()
                self.debouncer.trigger = AsyncMock()
                self.activity_buffer = Mock()

        return MockMemo()

    @pytest.fixture
    def sample_resource_body(self):
        """Sample Kubernetes resource body."""
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "test-ingress",
                "namespace": "default",
                "uid": "abc-123",
            },
            "spec": {"rules": [{"host": "example.com"}]},
        }

    @pytest.mark.asyncio
    async def test_timestamp_tracking_on_resource_update(
        self, mock_memo, sample_resource_body
    ):
        """Test that timestamps are tracked when resources are updated."""
        with patch(
            "haproxy_template_ic.models.resource_metadata.datetime"
        ) as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            # Call update_resource_index
            result = await update_resource_index(
                param="ingresses",
                namespace="default",
                name="test-ingress",
                body=sample_resource_body,
                logger=Mock(),
                memo=mock_memo,
            )

            # Check that resource_metadata was created and timestamp updated
            assert hasattr(mock_memo.resources, "resource_metadata")
            assert "ingresses" in mock_memo.resources.resource_metadata

            metadata = mock_memo.resources.resource_metadata["ingresses"]
            assert isinstance(metadata, ResourceTypeMetadata)
            assert metadata.resource_type == "ingresses"
            assert metadata.last_change == "2024-01-15T10:30:00+00:00"

            # Check that the debouncer was triggered
            mock_memo.debouncer.trigger.assert_called_once_with("resource_changes")

            # Check that the result contains the indexed resource
            assert len(result) == 1
            assert ("default", "test-ingress") in result

    @pytest.mark.asyncio
    async def test_multiple_resource_updates_same_type(
        self, mock_memo, sample_resource_body
    ):
        """Test multiple updates to the same resource type update the timestamp."""
        # First update
        with patch("haproxy_template_ic.models.resource_metadata.datetime") as mock_dt1:
            mock_dt1.now.return_value = datetime(
                2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc
            )
            mock_dt1.timezone = timezone

            await update_resource_index(
                param="ingresses",
                namespace="default",
                name="ingress-1",
                body=sample_resource_body,
                logger=Mock(),
                memo=mock_memo,
            )

            first_timestamp = mock_memo.resources.resource_metadata[
                "ingresses"
            ].last_change

        # Second update (different resource, same type)
        sample_resource_body["metadata"]["name"] = "ingress-2"
        with patch("haproxy_template_ic.models.resource_metadata.datetime") as mock_dt2:
            mock_dt2.now.return_value = datetime(
                2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc
            )
            mock_dt2.timezone = timezone

            await update_resource_index(
                param="ingresses",
                namespace="default",
                name="ingress-2",
                body=sample_resource_body,
                logger=Mock(),
                memo=mock_memo,
            )

            second_timestamp = mock_memo.resources.resource_metadata[
                "ingresses"
            ].last_change

        # Check that timestamp was updated
        assert first_timestamp == "2024-01-15T10:00:00+00:00"
        assert second_timestamp == "2024-01-15T11:00:00+00:00"
        assert first_timestamp != second_timestamp

        # Check that debouncer was called twice
        assert mock_memo.debouncer.trigger.call_count == 2

    @pytest.mark.asyncio
    async def test_different_resource_types_separate_timestamps(
        self, mock_memo, sample_resource_body
    ):
        """Test that different resource types have separate timestamps."""
        # Add another resource type to config
        mock_memo.config.watched_resources["services"] = Mock(
            api_version="v1",
            kind="Service",
            index_by=["metadata.namespace", "metadata.name"],
        )

        service_body = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "test-service", "namespace": "default"},
        }

        # Update ingress
        with patch("haproxy_template_ic.models.resource_metadata.datetime") as mock_dt1:
            mock_dt1.now.return_value = datetime(
                2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc
            )
            mock_dt1.timezone = timezone

            await update_resource_index(
                param="ingresses",
                namespace="default",
                name="test-ingress",
                body=sample_resource_body,
                logger=Mock(),
                memo=mock_memo,
            )

        # Update service
        with patch("haproxy_template_ic.models.resource_metadata.datetime") as mock_dt2:
            mock_dt2.now.return_value = datetime(
                2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc
            )
            mock_dt2.timezone = timezone

            await update_resource_index(
                param="services",
                namespace="default",
                name="test-service",
                body=service_body,
                logger=Mock(),
                memo=mock_memo,
            )

        # Check that both resource types have separate metadata
        assert "ingresses" in mock_memo.resources.resource_metadata
        assert "services" in mock_memo.resources.resource_metadata

        ingress_metadata = mock_memo.resources.resource_metadata["ingresses"]
        service_metadata = mock_memo.resources.resource_metadata["services"]

        assert ingress_metadata.last_change == "2024-01-15T10:00:00+00:00"
        assert service_metadata.last_change == "2024-01-15T11:00:00+00:00"
        assert ingress_metadata.resource_type == "ingresses"
        assert service_metadata.resource_type == "services"

    @pytest.mark.asyncio
    async def test_no_memo_no_crash(self, sample_resource_body):
        """Test that missing memo doesn't cause crashes."""
        # Should not crash when memo is None
        result = await update_resource_index(
            param="ingresses",
            namespace="default",
            name="test-ingress",
            body=sample_resource_body,
            logger=Mock(),
            memo=None,
        )

        # Should still return the indexed result
        assert len(result) == 1
        assert ("default", "test-ingress") in result

    @pytest.mark.asyncio
    async def test_initialization_on_first_use(self, sample_resource_body):
        """Test that resource_metadata entries are created on first use of a resource type."""

        class MockConfig:
            def __init__(self):
                self.watched_resources = {
                    "ingresses": Mock(
                        api_version="networking.k8s.io/v1",
                        kind="Ingress",
                        index_by=["metadata.namespace", "metadata.name"],
                    )
                }

        class MockResources:
            def __init__(self):
                self.indices = {}
                self.resource_metadata = {}  # Always initialized, matching ResourceState

        class MockMemo:
            def __init__(self):
                self.config = MockConfig()
                self.resources = MockResources()
                self.debouncer = Mock()
                self.debouncer.trigger = AsyncMock()
                self.activity_buffer = Mock()

        memo = MockMemo()

        # Resources has resource_metadata but it's empty initially
        assert hasattr(memo.resources, "resource_metadata")
        assert memo.resources.resource_metadata == {}

        with patch(
            "haproxy_template_ic.models.resource_metadata.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc
            )
            mock_datetime.timezone = timezone

            await update_resource_index(
                param="ingresses",
                namespace="default",
                name="test-ingress",
                body=sample_resource_body,
                logger=Mock(),
                memo=memo,
            )

        # Check that resource_metadata entry was created for this resource type
        assert hasattr(memo.resources, "resource_metadata")
        assert isinstance(memo.resources.resource_metadata, dict)
        assert "ingresses" in memo.resources.resource_metadata
