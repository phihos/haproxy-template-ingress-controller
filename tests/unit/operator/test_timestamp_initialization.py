"""
Tests for timestamp initialization when collecting resource indices.
"""

from unittest.mock import Mock, patch
from datetime import datetime, timezone

from haproxy_template_ic.operator.k8s_resources import _collect_resource_indices
from haproxy_template_ic.models.resource_metadata import ResourceTypeMetadata


class TestTimestampInitialization:
    """Tests for ensuring timestamps are initialized on first collection."""

    def test_new_resource_type_gets_timestamp(self):
        """Test that new resource types get an initial timestamp."""

        # Create mock memo
        class MockConfig:
            def __init__(self):
                self.watched_resources = {"ingresses": Mock(), "services": Mock()}

        class MockResources:
            def __init__(self):
                self.indices = {
                    "ingresses": {
                        ("default", "test-ingress"): {
                            "metadata": {"name": "test-ingress", "namespace": "default"}
                        }
                    },
                    "services": {
                        ("default", "test-service"): {
                            "metadata": {"name": "test-service", "namespace": "default"}
                        }
                    },
                }
                self.resource_metadata = {}

        class MockMemo:
            def __init__(self):
                self.config = MockConfig()
                self.resources = MockResources()
                # Add indices property for backward compatibility
                self.indices = self.resources.indices

        memo = MockMemo()
        metrics = Mock()

        with patch(
            "haproxy_template_ic.models.resource_metadata.datetime"
        ) as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            # Call _collect_resource_indices
            indices = _collect_resource_indices(memo, metrics)

        # Verify resource_metadata was created with timestamps
        assert hasattr(memo.resources, "resource_metadata")
        assert "ingresses" in memo.resources.resource_metadata
        assert "services" in memo.resources.resource_metadata

        # Check that timestamps were set
        ingress_metadata = memo.resources.resource_metadata["ingresses"]
        service_metadata = memo.resources.resource_metadata["services"]

        assert isinstance(ingress_metadata, ResourceTypeMetadata)
        assert isinstance(service_metadata, ResourceTypeMetadata)
        assert ingress_metadata.last_change == "2024-01-15T10:30:00+00:00"
        assert service_metadata.last_change == "2024-01-15T10:30:00+00:00"

        # Verify indices were still returned correctly
        assert "ingresses" in indices
        assert "services" in indices

    def test_existing_resource_metadata_preserves_timestamp(self):
        """Test that existing resource metadata preserves its timestamp."""

        # Create mock memo with existing metadata
        class MockConfig:
            def __init__(self):
                self.watched_resources = {"ingresses": Mock()}

        class MockResources:
            def __init__(self):
                self.indices = {
                    "ingresses": {
                        ("default", "test"): {
                            "metadata": {"name": "test", "namespace": "default"}
                        }
                    }
                }
                # Pre-existing metadata with earlier timestamp
                self.resource_metadata = {
                    "ingresses": ResourceTypeMetadata(
                        resource_type="ingresses",
                        last_change="2024-01-15T09:00:00+00:00",
                    )
                }

        class MockMemo:
            def __init__(self):
                self.config = MockConfig()
                self.resources = MockResources()
                # Add indices property for backward compatibility
                self.indices = self.resources.indices

        memo = MockMemo()
        metrics = Mock()

        with patch(
            "haproxy_template_ic.models.resource_metadata.datetime"
        ) as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            # Call _collect_resource_indices
            _collect_resource_indices(memo, metrics)

        # Verify timestamp was NOT overwritten
        ingress_metadata = memo.resources.resource_metadata["ingresses"]
        assert (
            ingress_metadata.last_change == "2024-01-15T09:00:00+00:00"
        )  # Original timestamp preserved

        # Statistics will be updated regardless (even if 0)

    def test_empty_indices_still_creates_metadata(self):
        """Test that empty indices still create metadata objects with timestamps."""

        class MockConfig:
            def __init__(self):
                self.watched_resources = {"ingresses": Mock()}

        class MockResources:
            def __init__(self):
                self.indices = {}  # Empty indices
                self.resource_metadata = {}

        class MockMemo:
            def __init__(self):
                self.config = MockConfig()
                self.resources = MockResources()
                # Add indices property for backward compatibility
                self.indices = self.resources.indices

        memo = MockMemo()
        metrics = Mock()

        with patch(
            "haproxy_template_ic.models.resource_metadata.datetime"
        ) as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            # Call _collect_resource_indices
            _collect_resource_indices(memo, metrics)

        # Verify metadata was created even with empty indices
        assert hasattr(memo.resources, "resource_metadata")
        assert "ingresses" in memo.resources.resource_metadata

        metadata = memo.resources.resource_metadata["ingresses"]
        assert isinstance(metadata, ResourceTypeMetadata)
        assert metadata.last_change == "2024-01-15T10:30:00+00:00"
        assert metadata.total_count == 0  # No resources, so count should be 0

    def test_error_case_still_creates_metadata_with_timestamp(self):
        """Test that error cases still create metadata objects with timestamps."""

        class MockConfig:
            def __init__(self):
                self.watched_resources = {"ingresses": Mock()}

        class MockResources:
            def __init__(self):
                # Set up indices to cause an error in IndexedResourceCollection.from_kopf_index
                self.indices = {
                    "ingresses": "invalid_data"
                }  # This will cause an exception
                self.resource_metadata = {}

        class MockMemo:
            def __init__(self):
                self.config = MockConfig()
                self.resources = MockResources()
                # Add indices property for backward compatibility
                self.indices = self.resources.indices

        memo = MockMemo()
        metrics = Mock()

        with patch(
            "haproxy_template_ic.models.resource_metadata.datetime"
        ) as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            # Call _collect_resource_indices - this should not raise an exception
            indices = _collect_resource_indices(memo, metrics)

        # Verify metadata was created even on error
        assert hasattr(memo.resources, "resource_metadata")
        assert "ingresses" in memo.resources.resource_metadata

        metadata = memo.resources.resource_metadata["ingresses"]
        assert isinstance(metadata, ResourceTypeMetadata)
        assert metadata.last_change == "2024-01-15T10:30:00+00:00"

        # Should have empty collection due to error
        assert "ingresses" in indices
        assert len(indices["ingresses"]) == 0
