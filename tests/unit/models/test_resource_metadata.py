"""
Tests for ResourceTypeMetadata dataclass.
"""

from datetime import datetime, timezone
from unittest.mock import patch

from haproxy_template_ic.models.resource_metadata import ResourceTypeMetadata


class TestResourceTypeMetadata:
    """Tests for ResourceTypeMetadata dataclass."""

    def test_initialization(self):
        """Test basic initialization of ResourceTypeMetadata."""
        metadata = ResourceTypeMetadata(resource_type="ingresses")

        assert metadata.resource_type == "ingresses"
        assert metadata.last_change is None
        assert metadata.total_count == 0
        assert metadata.namespace_count == 0
        assert metadata.memory_size == 0
        assert metadata.namespaces == {}

    def test_initialization_with_values(self):
        """Test initialization with custom values."""
        namespaces = {"default": 5, "test": 2}
        metadata = ResourceTypeMetadata(
            resource_type="services",
            last_change="2024-01-15T10:30:00Z",
            total_count=7,
            namespace_count=2,
            memory_size=1024,
            namespaces=namespaces,
        )

        assert metadata.resource_type == "services"
        assert metadata.last_change == "2024-01-15T10:30:00Z"
        assert metadata.total_count == 7
        assert metadata.namespace_count == 2
        assert metadata.memory_size == 1024
        assert metadata.namespaces == namespaces

    @patch("haproxy_template_ic.models.resource_metadata.datetime")
    def test_update_change_timestamp(self, mock_datetime):
        """Test updating change timestamp."""
        # Mock datetime.now to return a specific timestamp
        mock_now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone = timezone

        metadata = ResourceTypeMetadata(resource_type="secrets")
        metadata.update_change_timestamp()

        assert metadata.last_change == "2024-01-15T10:30:00+00:00"
        mock_datetime.now.assert_called_once_with(timezone.utc)

    def test_update_statistics(self):
        """Test updating resource statistics."""
        metadata = ResourceTypeMetadata(resource_type="configmaps")
        namespaces = {"default": 3, "kube-system": 2, "test": 1}

        metadata.update_statistics(
            total_count=6, namespace_count=3, memory_size=2048, namespaces=namespaces
        )

        assert metadata.total_count == 6
        assert metadata.namespace_count == 3
        assert metadata.memory_size == 2048
        assert metadata.namespaces == namespaces
        # Ensure it's a copy, not a reference
        namespaces["new"] = 1
        assert "new" not in metadata.namespaces

    def test_to_dict(self):
        """Test conversion to dictionary."""
        namespaces = {"default": 4, "test": 1}
        metadata = ResourceTypeMetadata(
            resource_type="pods",
            last_change="2024-01-15T10:30:00Z",
            total_count=5,
            namespace_count=2,
            memory_size=512,
            namespaces=namespaces,
        )

        result = metadata.to_dict()
        expected = {
            "total": 5,
            "namespace_count": 2,
            "memory_size": 512,
            "namespaces": namespaces,
            "last_change": "2024-01-15T10:30:00Z",
        }

        assert result == expected
        # Ensure resource_type is not included in the dict (as it's the key elsewhere)
        assert "resource_type" not in result

    def test_to_dict_with_none_timestamp(self):
        """Test to_dict with None timestamp."""
        metadata = ResourceTypeMetadata(resource_type="endpoints")

        result = metadata.to_dict()
        expected = {
            "total": 0,
            "namespace_count": 0,
            "memory_size": 0,
            "namespaces": {},
            "last_change": None,
        }

        assert result == expected

    def test_multiple_timestamp_updates(self):
        """Test multiple timestamp updates."""
        metadata = ResourceTypeMetadata(resource_type="ingresses")

        # First update
        with patch("haproxy_template_ic.models.resource_metadata.datetime") as mock_dt1:
            mock_dt1.now.return_value = datetime(
                2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc
            )
            mock_dt1.timezone = timezone
            metadata.update_change_timestamp()
            first_timestamp = metadata.last_change

        # Second update
        with patch("haproxy_template_ic.models.resource_metadata.datetime") as mock_dt2:
            mock_dt2.now.return_value = datetime(
                2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc
            )
            mock_dt2.timezone = timezone
            metadata.update_change_timestamp()
            second_timestamp = metadata.last_change

        assert first_timestamp == "2024-01-15T10:00:00+00:00"
        assert second_timestamp == "2024-01-15T11:00:00+00:00"
        assert first_timestamp != second_timestamp

    def test_empty_namespaces_handling(self):
        """Test handling of empty namespaces dict."""
        metadata = ResourceTypeMetadata(resource_type="services")
        metadata.update_statistics(
            total_count=0, namespace_count=0, memory_size=0, namespaces={}
        )

        result = metadata.to_dict()
        assert result["namespaces"] == {}
        assert result["namespace_count"] == 0
        assert result["total"] == 0
