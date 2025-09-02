"""Test resource models and IndexedResourceCollection functionality."""

from unittest.mock import MagicMock, patch

from haproxy_template_ic.models.resources import IndexedResourceCollection


class TestIndexedResourceCollection:
    """Test IndexedResourceCollection functionality."""

    def test_get_memory_size_empty_collection(self):
        """Test memory size calculation for empty collection."""
        collection = IndexedResourceCollection()

        size = collection.get_memory_size()

        # Should return some base size (at least size of empty dict)
        assert size >= 0
        assert isinstance(size, int)

    def test_get_memory_size_with_resources(self):
        """Test memory size calculation with resources."""
        collection = IndexedResourceCollection()

        # Manually add some test resources to the internal dict
        test_resources = [
            {
                "metadata": {"name": "test-resource-1", "namespace": "default"},
                "spec": {"data": "some content"},
                "status": {"phase": "Running"},
            },
            {
                "metadata": {"name": "test-resource-2", "namespace": "default"},
                "spec": {"data": "more content"},
                "status": {"phase": "Running"},
            },
        ]

        collection._internal_dict[("default", "test-app")] = test_resources

        size = collection.get_memory_size()

        # Should return a positive size
        assert size > 0
        assert isinstance(size, int)

    def test_get_memory_size_with_large_resources(self):
        """Test memory size calculation with larger resources."""
        collection = IndexedResourceCollection()

        # Create a resource with larger content
        large_resource = {
            "metadata": {"name": "large-resource", "namespace": "default"},
            "spec": {"data": "x" * 10000},  # 10KB of data
            "status": {"phase": "Running", "details": {"info": "y" * 5000}},  # 5KB more
        }

        collection._internal_dict[("default", "large-app")] = [large_resource]

        size = collection.get_memory_size()

        # Should return a larger size
        assert size > 15000  # At least the size of our test data
        assert isinstance(size, int)

    def test_get_memory_size_multiple_keys(self):
        """Test memory size calculation with multiple index keys."""
        collection = IndexedResourceCollection()

        # Add resources under different keys
        resources1 = [
            {"metadata": {"name": "res1", "namespace": "ns1"}, "data": "content1"}
        ]
        resources2 = [
            {"metadata": {"name": "res2", "namespace": "ns2"}, "data": "content2"}
        ]
        resources3 = [
            {"metadata": {"name": "res3a", "namespace": "ns3"}, "data": "content3a"},
            {"metadata": {"name": "res3b", "namespace": "ns3"}, "data": "content3b"},
        ]

        collection._internal_dict[("ns1", "app1")] = resources1
        collection._internal_dict[("ns2", "app2")] = resources2
        collection._internal_dict[("ns3", "app3")] = resources3

        size = collection.get_memory_size()

        # Should be larger than a single resource
        assert size > 0
        assert isinstance(size, int)

    def test_get_memory_size_error_handling(self):
        """Test memory size calculation handles errors gracefully."""
        collection = IndexedResourceCollection()

        # Create a problematic resource that might cause sys.getsizeof to fail
        # (this is hard to create in practice, but we test the error handling)
        collection._internal_dict[("test", "error")] = [{"normal": "resource"}]

        # Mock sys.getsizeof to raise an exception
        with patch(
            "haproxy_template_ic.models.resources.sys.getsizeof"
        ) as mock_getsizeof:
            mock_getsizeof.side_effect = Exception("Mocked error")

            size = collection.get_memory_size()

            # Should return 0 on error and not raise exception
            assert size == 0

    def test_memory_size_increases_with_content(self):
        """Test that memory size increases as more content is added."""
        collection = IndexedResourceCollection()

        # Start with empty collection
        empty_size = collection.get_memory_size()

        # Add one resource
        small_resource = {
            "metadata": {"name": "small", "namespace": "test"},
            "data": "small",
        }
        collection._internal_dict[("test", "app")] = [small_resource]
        small_size = collection.get_memory_size()

        # Add more content to the resource
        large_resource = {
            "metadata": {"name": "large", "namespace": "test"},
            "data": "x" * 1000,
        }
        collection._internal_dict[("test", "app")] = [small_resource, large_resource]
        large_size = collection.get_memory_size()

        # Memory size should increase with more content
        assert large_size > small_size > empty_size

    def test_calculate_dict_size_nested_structures(self):
        """Test the recursive dictionary size calculation."""
        collection = IndexedResourceCollection()

        # Test with nested dictionary structure
        nested_dict = {
            "level1": {"level2": {"level3": ["item1", "item2", {"nested": "value"}]}},
            "list": [1, 2, 3, {"key": "value"}],
            "simple": "string",
        }

        size = collection._calculate_dict_size(nested_dict)

        # Should return a positive size for nested structure
        assert size > 0
        assert isinstance(size, int)

    def test_calculate_dict_size_different_types(self):
        """Test size calculation for different data types."""
        collection = IndexedResourceCollection()

        # Test different types
        string_size = collection._calculate_dict_size("hello world")
        int_size = collection._calculate_dict_size(42)
        list_size = collection._calculate_dict_size([1, 2, 3, "four"])
        dict_size = collection._calculate_dict_size({"key": "value", "number": 123})

        # All should return positive sizes
        assert all(size > 0 for size in [string_size, int_size, list_size, dict_size])
        assert all(
            isinstance(size, int)
            for size in [string_size, int_size, list_size, dict_size]
        )

        # Dictionary should generally be larger than individual items
        assert dict_size > string_size
        assert list_size > int_size


class TestIndexedResourceCollectionIntegration:
    """Integration tests for IndexedResourceCollection memory functionality."""

    def test_from_kopf_index_preserves_memory_calculation(self):
        """Test that collections created from kopf index support memory size calculation."""
        # Mock a kopf index
        mock_index = MagicMock()
        mock_index.__getitem__ = MagicMock()
        mock_index.__iter__ = MagicMock(return_value=iter([("ns1", "app1")]))

        mock_resource = {
            "metadata": {"name": "test-resource", "namespace": "ns1"},
            "spec": {"replicas": 3},
            "status": {"ready": True},
        }

        mock_index.__getitem__.return_value = [mock_resource]

        # Mock the normalize function to return the resource as-is
        with patch("haproxy_template_ic.k8s.normalize_kopf_resource") as mock_normalize:
            mock_normalize.return_value = mock_resource

            collection = IndexedResourceCollection.from_kopf_index(mock_index)

            # Should be able to calculate memory size
            size = collection.get_memory_size()
            assert size > 0
            assert isinstance(size, int)
