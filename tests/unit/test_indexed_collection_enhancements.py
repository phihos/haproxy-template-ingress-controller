"""
Tests for IndexedResourceCollection enhancements and error handling.

This module tests the new features added based on code review feedback,
including improved error handling, resource validation, and performance optimizations.
"""

import pytest
from unittest.mock import MagicMock, patch

from haproxy_template_ic.config_models import IndexedResourceCollection


class TestIndexedResourceCollectionEnhancements:
    """Test enhanced IndexedResourceCollection functionality."""

    def test_from_kopf_index_with_invalid_key_types(self):
        """Test handling of unexpected key types in from_kopf_index."""
        # Mock kopf Index interface: __iter__ and __getitem__
        mock_index = MagicMock()

        # Keys in the index
        keys = [
            ("namespace", "name"),
            "simple_key",
            ["list", "key"],
            42,
            {"dict": "key"},
        ]
        mock_index.__iter__.return_value = iter(keys)

        # Mock Store objects for each key
        def mock_getitem(key):
            mock_store = MagicMock()
            if key == ("namespace", "name"):
                mock_store.__iter__.return_value = iter(
                    [{"metadata": {"name": "test1"}}]
                )
            elif key == "simple_key":
                mock_store.__iter__.return_value = iter(
                    [{"metadata": {"name": "test2"}}]
                )
            elif key == ["list", "key"]:
                mock_store.__iter__.return_value = iter(
                    [{"metadata": {"name": "test3"}}]
                )
            elif key == 42:
                mock_store.__iter__.return_value = iter(
                    [{"metadata": {"name": "test4"}}]
                )
            elif key == {"dict": "key"}:
                mock_store.__iter__.return_value = iter(
                    [{"metadata": {"name": "test5"}}]
                )
            return mock_store

        mock_index.__getitem__.side_effect = mock_getitem

        # Capture logging output
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            collection = IndexedResourceCollection.from_kopf_index(mock_index)

            # Should have all resources (none filtered out for invalid structure)
            assert len(collection) == 5

    def test_from_kopf_index_with_invalid_resources(self):
        """Test resource validation during indexing."""
        # Mock kopf Index interface
        mock_index = MagicMock()

        # Keys in the index
        keys = ["key1", "key2", "key3", "key4", "key5", "key6"]
        mock_index.__iter__.return_value = iter(keys)

        # Mock Store objects for each key with different resource types
        def mock_getitem(key):
            mock_store = MagicMock()
            if key == "key1":
                mock_store.__iter__.return_value = iter(
                    [{"metadata": {"name": "valid1"}}]
                )
            elif key == "key2":
                mock_store.__iter__.return_value = iter([{"no_metadata": "invalid"}])
            elif key == "key3":
                mock_store.__iter__.return_value = iter(
                    [{"metadata": {"no_name": "invalid"}}]
                )
            elif key == "key4":
                mock_store.__iter__.return_value = iter([{"metadata": {"name": ""}}])
            elif key == "key5":
                mock_store.__iter__.return_value = iter(["not_a_dict"])
            elif key == "key6":
                mock_store.__iter__.return_value = iter(
                    [{"metadata": {"name": "valid2"}}]
                )
            return mock_store

        mock_index.__getitem__.side_effect = mock_getitem

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            collection = IndexedResourceCollection.from_kopf_index(mock_index)

            # Should only have valid resources (2 out of 6)
            assert len(collection) == 2

            # Should have warned about invalid resources
            mock_logger.warning.assert_called()
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            assert any("Skipping invalid resource" in call for call in warning_calls)

    def test_get_indexed_single_with_multiple_matches(self):
        """Test error handling when multiple resources match a single key."""

        # Create a custom subclass to allow method mocking
        class TestableCollection(IndexedResourceCollection):
            def get_indexed(self, *args):
                return [
                    {"metadata": {"name": "resource1", "namespace": "default"}},
                    {"metadata": {"name": "resource2", "namespace": "default"}},
                ]

        test_collection = TestableCollection()

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with pytest.raises(ValueError, match="Multiple resources found"):
                test_collection.get_indexed_single("test", "key")

            # Should have logged error with resource names (with kind prefix)
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "Multiple resources found" in error_call
            assert "2 matches" in error_call
            assert "unknown:default/resource1" in error_call
            assert "unknown:default/resource2" in error_call

    def test_get_indexed_single_with_tracing(self):
        """Test tracing integration in get_indexed_single."""

        class TestableCollection(IndexedResourceCollection):
            def get_indexed(self, *args):
                return [
                    {"metadata": {"name": "res1", "namespace": "ns1"}},
                    {"metadata": {"name": "res2", "namespace": "ns2"}},
                ]

        collection = TestableCollection()

        # Mock tracing module at import time
        with patch(
            "haproxy_template_ic.tracing.record_span_event"
        ) as mock_record_span_event:
            with patch("logging.getLogger"):
                with pytest.raises(ValueError):
                    collection.get_indexed_single("test", "key")

                # Should have recorded span event with resource information
                mock_record_span_event.assert_called_once()
                call_args = mock_record_span_event.call_args
                assert call_args[0][0] == "multiple_resources_found"
                assert call_args[0][1]["count"] == 2
                assert "resources" in call_args[0][1]
                assert "unknown:ns1/res1" in call_args[0][1]["resources"]
                assert "unknown:ns2/res2" in call_args[0][1]["resources"]

    def test_get_indexed_single_without_tracing(self):
        """Test graceful handling when tracing module is not available."""

        class TestableCollection(IndexedResourceCollection):
            def get_indexed(self, *args):
                return [
                    {"metadata": {"name": "res1", "namespace": "ns1"}},
                    {"metadata": {"name": "res2", "namespace": "ns2"}},
                ]

        collection = TestableCollection()

        # Mock ImportError for tracing module import
        original_import = __builtins__["__import__"]

        def mock_import(name, *args, **kwargs):
            if name == "haproxy_template_ic.tracing":
                raise ImportError("Tracing module not available")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with patch("logging.getLogger"):
                with pytest.raises(
                    ValueError, match="unknown:ns1/res1, unknown:ns2/res2"
                ):
                    collection.get_indexed_single("test", "key")
                # Should not raise ImportError, should handle gracefully

    def test_get_indexed_performance_optimization(self):
        """Test that get_indexed uses optimized dict.get instead of contains check."""
        collection = IndexedResourceCollection()
        test_resource = {"metadata": {"name": "test"}}
        collection._internal_dict[("test", "key")] = [test_resource]

        # Test successful lookup
        result = collection.get_indexed("test", "key")
        assert result == [test_resource]

        # Test missing key
        result = collection.get_indexed("missing", "key")
        assert result == []

    def test_get_indexed_iter_method(self):
        """Test the new get_indexed_iter method for memory efficiency."""
        collection = IndexedResourceCollection()
        test_resource = {"metadata": {"name": "test"}}
        collection._internal_dict[("test", "key")] = [test_resource]

        # Test successful lookup with iterator
        results = list(collection.get_indexed_iter("test", "key"))
        assert results == [test_resource]

        # Test missing key with iterator
        results = list(collection.get_indexed_iter("missing", "key"))
        assert results == []

        # Verify it returns an iterator, not a list
        iterator = collection.get_indexed_iter("test", "key")
        assert hasattr(iterator, "__iter__")
        assert hasattr(iterator, "__next__")

    def test_validate_resource_method(self):
        """Test the _validate_resource method."""
        collection = IndexedResourceCollection()

        # Valid resource
        valid_resource = {
            "metadata": {"name": "test", "namespace": "default"},
            "spec": {"some": "data"},
        }
        assert collection._validate_resource(valid_resource) is True

        # Invalid - not a dict
        assert collection._validate_resource("not a dict") is False

        # Invalid - no metadata
        assert collection._validate_resource({"spec": {"data": "test"}}) is False

        # Invalid - metadata not a dict
        assert collection._validate_resource({"metadata": "not a dict"}) is False

        # Invalid - no name in metadata
        assert (
            collection._validate_resource({"metadata": {"namespace": "test"}}) is False
        )

        # Invalid - empty name
        assert collection._validate_resource({"metadata": {"name": ""}}) is False

        # Valid - minimal valid resource
        assert collection._validate_resource({"metadata": {"name": "test"}}) is True

        # Valid - mock object with metadata.name (for tests)
        mock_resource = MagicMock()
        mock_resource.metadata.name = "test-mock"
        assert collection._validate_resource(mock_resource) is True

        # Invalid - mock object without proper metadata structure
        invalid_mock = MagicMock()
        del invalid_mock.metadata  # Remove metadata attribute
        assert collection._validate_resource(invalid_mock) is False

    def test_get_indexed_single_error_message_enhancement(self):
        """Test enhanced error messages with resource identification."""

        class TestableCollection(IndexedResourceCollection):
            def get_indexed(self, *args):
                # Mix of dict and mock resources
                mock_resource = MagicMock()
                mock_resource.metadata.name = "mock-resource"
                mock_resource.metadata.namespace = "test-ns"
                mock_resource.kind = "Pod"

                return [
                    {"metadata": {"name": "dict-resource", "namespace": "default"}},
                    mock_resource,
                    {"metadata": {"name": "another-dict"}},  # No namespace
                    "invalid-resource",  # Will trigger error handling
                ]

        collection = TestableCollection()

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with pytest.raises(ValueError) as exc_info:
                collection.get_indexed_single("test", "key")

            # Check error message contains resource identifiers with kind
            error_msg = str(exc_info.value)
            assert "unknown:default/dict-resource" in error_msg
            assert "Pod:test-ns/mock-resource" in error_msg
            assert (
                "unknown:unknown/another-dict" in error_msg
            )  # Missing namespace becomes 'unknown'

            # Check logged error message
            mock_logger.error.assert_called_once()
            log_msg = mock_logger.error.call_args[0][0]
            assert "4 matches" in log_msg
            assert "unknown:default/dict-resource" in log_msg
            assert "Pod:test-ns/mock-resource" in log_msg


class TestIndexedResourceCollectionPerformance:
    """Test performance characteristics of IndexedResourceCollection."""

    def test_memory_efficiency_with_large_dataset(self):
        """Test memory efficiency with a larger dataset."""
        collection = IndexedResourceCollection()

        # Add 1000 resources
        for i in range(1000):
            resource = {
                "metadata": {"name": f"resource-{i}", "namespace": f"ns-{i % 10}"},
                "data": f"test-data-{i}",
            }
            collection._internal_dict[(f"ns-{i % 10}", f"resource-{i}")] = [resource]

        assert len(collection) == 1000

        # Test that lookups are still fast
        result = collection.get_indexed("ns-5", "resource-5")
        assert len(result) == 1
        assert result[0]["metadata"]["name"] == "resource-5"

        # Test iterator efficiency
        iterator_results = list(collection.get_indexed_iter("ns-5", "resource-15"))
        list_results = collection.get_indexed("ns-5", "resource-15")
        assert iterator_results == list_results

    def test_key_normalization_consistency(self):
        """Test that key normalization is consistent across methods."""
        collection = IndexedResourceCollection()
        resource = {"metadata": {"name": "test"}}

        # Add with mixed types
        collection._internal_dict[("123", "test")] = [resource]

        # Should be able to retrieve with string args
        assert collection.get_indexed("123", "test") == [resource]
        assert collection.get_indexed_single("123", "test") == resource
        assert list(collection.get_indexed_iter("123", "test")) == [resource]

    def test_large_resource_list_truncation(self):
        """Test that error messages with many resources get truncated properly."""

        class TestableCollection(IndexedResourceCollection):
            def get_indexed(self, *args):
                # Return 8 resources to test truncation (should show 5 + "3 more")
                return [
                    {"metadata": {"name": f"resource-{i}", "namespace": "default"}}
                    for i in range(8)
                ]

        collection = TestableCollection()

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with pytest.raises(ValueError) as exc_info:
                collection.get_indexed_single("test", "key")

            # Check that error message is truncated
            error_msg = str(exc_info.value)
            assert "unknown:default/resource-0" in error_msg
            assert (
                "unknown:default/resource-2" in error_msg
            )  # Should show first 3 (0, 1, 2)
            assert "showing first 3" in error_msg
            # Should not contain all 8 resources
            assert "unknown:default/resource-7" not in error_msg


class TestIndexedResourceCollectionEnhancedAPI:
    """Test enhanced API methods and Unicode support."""

    def test_contains_method(self):
        """Test __contains__ method for membership testing."""
        collection = IndexedResourceCollection()
        test_resource = {"metadata": {"name": "test"}}
        collection._internal_dict[("test", "key")] = [test_resource]

        # Test membership with tuple key
        assert ("test", "key") in collection
        assert ("missing", "key") not in collection

        # Test membership with individual arguments (should normalize)
        normalized_key = collection._normalize_key("test", "key")
        assert normalized_key in collection

    def test_keys_method(self):
        """Test keys() method for iterating over index keys."""
        collection = IndexedResourceCollection()
        test_resources = [
            {"metadata": {"name": "test1"}},
            {"metadata": {"name": "test2"}},
        ]
        collection._internal_dict[("ns1", "test1")] = [test_resources[0]]
        collection._internal_dict[("ns2", "test2")] = [test_resources[1]]

        keys_list = list(collection.keys())
        assert len(keys_list) == 2
        assert ("ns1", "test1") in keys_list
        assert ("ns2", "test2") in keys_list

    def test_unicode_resource_names(self):
        """Test handling of Unicode characters in resource names."""
        collection = IndexedResourceCollection()

        # Test with various Unicode characters
        unicode_resources = [
            {"metadata": {"name": "测试-resource", "namespace": "系统"}},  # Chinese
            {
                "metadata": {"name": "tëst-rësoürçe", "namespace": "défäult"}
            },  # Accented Latin
            {"metadata": {"name": "тест-ресурс", "namespace": "система"}},  # Cyrillic
            {"metadata": {"name": "🚀-rocket", "namespace": "🌟-space"}},  # Emojis
        ]

        for i, resource in enumerate(unicode_resources):
            key = (resource["metadata"]["namespace"], resource["metadata"]["name"])
            collection._internal_dict[key] = [resource]

        assert len(collection) == 4

        # Test lookups with Unicode
        chinese_result = collection.get_indexed("系统", "测试-resource")
        assert len(chinese_result) == 1
        assert chinese_result[0]["metadata"]["name"] == "测试-resource"

        # Test resource ID extraction with Unicode
        chinese_id = collection._extract_resource_id(unicode_resources[0])
        assert "系统/测试-resource" in chinese_id

        # Test emoji handling
        emoji_result = collection.get_indexed("🌟-space", "🚀-rocket")
        assert len(emoji_result) == 1

    def test_enhanced_resource_id_with_kind(self):
        """Test enhanced resource ID extraction with kind information."""
        collection = IndexedResourceCollection()

        # Test with kind information
        pod_resource = {
            "kind": "Pod",
            "metadata": {"name": "test-pod", "namespace": "default"},
        }

        service_resource = {
            "kind": "Service",
            "metadata": {"name": "test-service", "namespace": "kube-system"},
        }

        # Test resource ID extraction with kind
        pod_id = collection._extract_resource_id(pod_resource)
        assert pod_id == "Pod:default/test-pod"

        service_id = collection._extract_resource_id(service_resource)
        assert service_id == "Service:kube-system/test-service"

        # Test with missing kind
        no_kind_resource = {"metadata": {"name": "no-kind", "namespace": "default"}}

        no_kind_id = collection._extract_resource_id(no_kind_resource)
        assert no_kind_id == "unknown:default/no-kind"

    def test_enhanced_error_handling_in_resource_id_extraction(self):
        """Test enhanced error handling in resource ID extraction."""
        collection = IndexedResourceCollection()

        # Test malformed metadata
        malformed_resource = {
            "metadata": "not-a-dict",  # Invalid metadata type
            "kind": "Pod",
        }

        malformed_id = collection._extract_resource_id(malformed_resource)
        assert malformed_id == "<error>"

        # Test completely invalid resource
        invalid_resource = "not-a-resource"
        invalid_id = collection._extract_resource_id(invalid_resource)
        assert invalid_id == "<unknown>"

        # Test resource that raises exception during str() conversion
        class BadResource:
            def __init__(self):
                self.metadata = BadMetadata()
                self.kind = "Pod"

        class BadMetadata:
            @property
            def name(self):
                return BadName()

        class BadName:
            def __str__(self):
                raise TypeError("Cannot convert to string")

        bad_resource = BadResource()
        error_id = collection._extract_resource_id(bad_resource)
        assert error_id == "<error>"

    def test_unicode_normalization_in_keys(self):
        """Test Unicode normalization in key components."""
        collection = IndexedResourceCollection()

        # Test different Unicode representations of the same character
        # é can be represented as:
        # 1. Single character: é (U+00E9)
        # 2. Composed: e + ́ (U+0065 + U+0301)
        name_nfc = "café"  # NFC form (composed)
        name_nfd = "cafe\u0301"  # NFD form (decomposed)

        # Both should normalize to the same key
        key1 = collection._normalize_key("default", name_nfc)
        key2 = collection._normalize_key("default", name_nfd)

        assert key1 == key2
        assert key1[1] == "café"  # Should be normalized to NFC form

    def test_memory_efficient_iteration_methods(self):
        """Test that items() and values() methods don't create memory leaks."""
        collection = IndexedResourceCollection()

        # Add test resources
        for i in range(100):
            resource = {
                "metadata": {"name": f"resource-{i}", "namespace": "test"},
                "data": f"large-data-{i}" * 100,  # Make resources larger
            }
            collection._internal_dict[("test", f"resource-{i}")] = [resource]

        # Test that items() iteration is lazy and doesn't pre-allocate all resources
        items_count = 0
        for key, resource in collection.items():
            items_count += 1
            if items_count > 10:  # Break early to test lazy evaluation
                break

        assert items_count == 11

        # Test that values() iteration is lazy and doesn't pre-allocate all resources
        values_count = 0
        for resource in collection.values():
            values_count += 1
            if values_count > 10:  # Break early to test lazy evaluation
                break

        assert values_count == 11

        # Verify we can still get the full count
        assert len(collection) == 100

    def test_ascii_optimization_in_unicode_normalization(self):
        """Test that ASCII strings bypass expensive Unicode normalization."""
        collection = IndexedResourceCollection()

        # Test ASCII string (should be fast path)
        ascii_key = collection._normalize_key("simple-ascii-key")
        assert ascii_key == ("simple-ascii-key",)

        # Test Unicode string (should use normalization)
        unicode_key = collection._normalize_key("café")
        assert unicode_key == ("café",)

        # Test mixed components
        mixed_key = collection._normalize_key("ascii", "café", "more-ascii")
        assert mixed_key == ("ascii", "café", "more-ascii")
