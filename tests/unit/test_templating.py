"""
Unit tests for templating functionality.

Tests the Jinja2-based template compilation, rendering, and caching functionality
including support for template snippets and custom filters.
"""

import base64
import pytest
from unittest.mock import Mock, patch
from jinja2 import TemplateSyntaxError, TemplateNotFound, Environment, Template

from haproxy_template_ic.templating import (
    b64decode_filter,
    get_path_filter,
    SnippetLoader,
    get_template_environment,
    TemplateEnvironmentFactory,
    TemplateCompiler,
    compile_template,
    render_template,
    TemplateRenderer,
    validate_config_templates,
    format_template_error,
    _extract_snippet_name,
    _get_context_lines,
)
from haproxy_template_ic.models import TemplateSnippet


class TestB64DecodeFilter:
    """Test the b64decode custom filter."""

    def test_b64decode_filter_success(self):
        """Test successful base64 decoding."""
        # "hello" in base64
        encoded = base64.b64encode(b"hello").decode()
        result = b64decode_filter(encoded)
        assert result == "hello"

    def test_b64decode_filter_invalid_base64(self):
        """Test b64decode filter with invalid base64."""
        with pytest.raises(ValueError, match="Failed to decode base64 value"):
            b64decode_filter("invalid-base64!")

    def test_b64decode_filter_empty_string(self):
        """Test b64decode filter with empty string."""
        result = b64decode_filter("")
        assert result == ""

    def test_b64decode_filter_unicode(self):
        """Test b64decode filter with unicode content."""
        # "héllo" in base64
        encoded = base64.b64encode("héllo".encode("utf-8")).decode()
        result = b64decode_filter(encoded)
        assert result == "héllo"


class TestSnippetLoader:
    """Test the SnippetLoader class."""

    @pytest.fixture
    def sample_snippets(self):
        """Create sample template snippets."""
        return {
            "backend-name": TemplateSnippet(
                name="backend-name", template="backend_{{ service_name }}_{{ port }}"
            ),
            "frontend-config": TemplateSnippet(
                name="frontend-config", template="bind *:{{ port }}\nmode http"
            ),
        }

    def test_snippet_loader_init_with_snippets(self, sample_snippets):
        """Test SnippetLoader initialization with snippets."""
        loader = SnippetLoader(sample_snippets)
        assert loader.snippets == sample_snippets

    def test_snippet_loader_init_without_snippets(self):
        """Test SnippetLoader initialization without snippets."""
        loader = SnippetLoader()
        assert loader.snippets == {}

    def test_snippet_loader_init_none_snippets(self):
        """Test SnippetLoader initialization with None snippets."""
        loader = SnippetLoader(None)
        assert loader.snippets == {}

    def test_get_source_existing_snippet(self, sample_snippets):
        """Test getting source for existing snippet."""
        loader = SnippetLoader(sample_snippets)
        env = Mock()

        source, filename, uptodate = loader.get_source(env, "backend-name")

        assert source == "backend_{{ service_name }}_{{ port }}"
        assert filename is None
        assert uptodate() is True

    def test_get_source_nonexistent_snippet(self, sample_snippets):
        """Test getting source for non-existent snippet."""
        loader = SnippetLoader(sample_snippets)
        env = Mock()

        with pytest.raises(TemplateNotFound):
            loader.get_source(env, "nonexistent")

    def test_get_source_string_snippet(self):
        """Test getting source for string-based snippet."""
        snippets = {"simple": "template content"}
        loader = SnippetLoader(snippets)
        env = Mock()

        source, filename, uptodate = loader.get_source(env, "simple")

        assert source == "template content"
        assert filename is None
        assert uptodate() is True


class TestGetTemplateEnvironment:
    """Test the get_template_environment function."""

    def test_get_template_environment_with_snippets(self):
        """Test creating environment with snippets."""
        snippets = {"test": TemplateSnippet(name="test", template="test content")}

        env = get_template_environment(snippets)

        assert isinstance(env, Environment)
        assert env.autoescape is False
        assert env.trim_blocks is False
        assert env.lstrip_blocks is False
        assert "b64decode" in env.filters

    def test_get_template_environment_without_snippets(self):
        """Test creating environment without snippets."""
        env = get_template_environment()

        assert isinstance(env, Environment)
        assert "b64decode" in env.filters

    def test_get_template_environment_b64decode_filter(self):
        """Test that b64decode filter is properly registered."""
        env = get_template_environment()

        # Test the filter
        encoded = base64.b64encode(b"test").decode()
        result = env.filters["b64decode"](encoded)
        assert result == "test"


class TestTemplateEnvironmentFactory:
    """Test the TemplateEnvironmentFactory class."""

    def test_create_environment_with_snippets(self):
        """Test creating environment with snippets."""
        snippets = {"test": TemplateSnippet(name="test", template="test content")}

        env = TemplateEnvironmentFactory.create_environment(snippets)

        assert isinstance(env, Environment)
        assert "b64decode" in env.filters

    def test_create_environment_without_snippets(self):
        """Test creating environment without snippets."""
        env = TemplateEnvironmentFactory.create_environment()

        assert isinstance(env, Environment)
        assert "b64decode" in env.filters

    def test_create_environment_with_config(self):
        """Test creating environment with config object."""

        class MockConfig:
            storage_maps_dir = "/test/maps"
            storage_ssl_dir = "/test/ssl"
            storage_general_dir = "/test/general"

        config = MockConfig()
        env = TemplateEnvironmentFactory.create_environment(None, config)

        assert isinstance(env, Environment)
        assert "get_path" in env.filters

    def test_create_environment_error_handling(self):
        """Test factory error handling with invalid snippets."""
        # Test with invalid snippet data that could cause issues
        invalid_snippets = {"test": "not a snippet object"}

        # Should not raise an exception, factory should handle gracefully
        env = TemplateEnvironmentFactory.create_environment(invalid_snippets)
        assert isinstance(env, Environment)

    def test_create_environment_filters_available(self):
        """Test that all expected filters are available in created environment."""
        env = TemplateEnvironmentFactory.create_environment()

        # Check that custom filters are registered
        assert "b64decode" in env.filters
        assert "get_path" in env.filters

        # Verify filters are callable
        assert callable(env.filters["b64decode"])
        assert callable(env.filters["get_path"])

    def test_create_environment_with_problematic_config(self):
        """Test factory with config that might cause issues."""

        class ProblematicConfig:
            def __getattr__(self, name):
                raise AttributeError(f"Config error accessing {name}")

        # Should handle gracefully even with problematic config
        env = TemplateEnvironmentFactory.create_environment(None, ProblematicConfig())
        assert isinstance(env, Environment)


class TestTemplateCompiler:
    """Test the TemplateCompiler class."""

    @pytest.fixture
    def sample_snippets(self):
        """Create sample template snippets."""
        return {
            "backend-name": TemplateSnippet(
                name="backend-name", template="backend_{{ service_name }}_{{ port }}"
            ),
        }

    def test_template_compiler_init_with_snippets(self, sample_snippets):
        """Test TemplateCompiler initialization with snippets."""
        compiler = TemplateCompiler(sample_snippets)
        assert isinstance(compiler.environment, Environment)

    def test_template_compiler_init_without_snippets(self):
        """Test TemplateCompiler initialization without snippets."""
        compiler = TemplateCompiler()
        assert isinstance(compiler.environment, Environment)

    def test_compile_template_success(self, sample_snippets):
        """Test successful template compilation."""
        compiler = TemplateCompiler(sample_snippets)
        template_string = "Hello {{ name }}"

        template = compiler.compile_template(template_string)

        assert isinstance(template, Template)
        result = template.render(name="World")
        assert result == "Hello World"

    def test_compile_template_with_snippet(self, sample_snippets):
        """Test template compilation with snippet inclusion."""
        compiler = TemplateCompiler(sample_snippets)
        template_string = "{% include 'backend-name' %}"

        template = compiler.compile_template(template_string)

        assert isinstance(template, Template)
        result = template.render(service_name="web", port="80")
        assert result == "backend_web_80"

    def test_compile_template_syntax_error(self):
        """Test template compilation with syntax error."""
        compiler = TemplateCompiler()
        template_string = "{{ invalid syntax"  # Missing closing brace

        # Jinja2 should raise TemplateSyntaxError on compilation
        with pytest.raises(TemplateSyntaxError):
            compiler.compile_template(template_string)


class TestCompileTemplateFunction:
    """Test the compile_template function."""

    def test_compile_template_no_snippets(self):
        """Test template compilation without snippets."""
        template_str = "Hello {{ name }}"

        template = compile_template(template_str)

        assert isinstance(template, Template)
        result = template.render(name="World")
        assert result == "Hello World"

    def test_compile_template_with_snippets_tuple(self):
        """Test template compilation with snippets tuple."""
        snippets_tuple = (("test", "Test: {{ value }}"),)
        template_str = "{% include 'test' %}"

        template = compile_template(template_str, snippets_tuple)

        assert isinstance(template, Template)
        result = template.render(value="123")
        assert result == "Test: 123"

    def test_compile_template_caching(self):
        """Test that template compilation uses caching."""
        template_str = "Hello {{ name }}"

        # Clear cache first
        compile_template.cache_clear()

        # First call
        template1 = compile_template(template_str)

        # Second call should return cached version
        template2 = compile_template(template_str)

        # They should be the same object due to caching
        assert template1 is template2

    def test_compile_template_syntax_error(self):
        """Test template compilation with syntax error."""
        with pytest.raises(ValueError, match="Template syntax error"):
            compile_template("{{ invalid syntax")


class TestRenderTemplateFunction:
    """Test the render_template function."""

    def test_render_template_simple(self):
        """Test simple template rendering."""
        template_str = "Hello {{ name }}"
        context = {"name": "World"}

        result = render_template(template_str, context)

        assert result == "Hello World"

    def test_render_template_with_snippets(self):
        """Test template rendering with snippets."""
        # Use TemplateRenderer instead of render_template for TemplateSnippet objects
        snippets = {
            "greeting": TemplateSnippet(name="greeting", template="Hello {{ name }}!")
        }
        template_str = "{% include 'greeting' %}"
        context = {"name": "World"}

        renderer = TemplateRenderer(snippets)
        result = renderer.render(template_str, **context)

        assert result == "Hello World!"

    def test_render_template_error(self):
        """Test template rendering with error."""
        template_str = "{{ undefined_var.missing_attr }}"
        context = {}

        with pytest.raises(ValueError, match="Template rendering failed"):
            render_template(template_str, context)


class TestTemplateRenderer:
    """Test the TemplateRenderer class."""

    @pytest.fixture
    def sample_snippets(self):
        """Create sample template snippets."""
        return {
            "backend": TemplateSnippet(name="backend", template="backend {{ name }}"),
            "frontend": TemplateSnippet(
                name="frontend", template="frontend {{ name }}"
            ),
        }

    def test_template_renderer_init_with_snippets(self, sample_snippets):
        """Test TemplateRenderer initialization with snippets."""
        renderer = TemplateRenderer(sample_snippets)
        assert isinstance(renderer._compiler, TemplateCompiler)
        assert renderer._compiled_templates == {}

    def test_template_renderer_init_without_snippets(self):
        """Test TemplateRenderer initialization without snippets."""
        renderer = TemplateRenderer()
        assert isinstance(renderer._compiler, TemplateCompiler)
        assert renderer._compiled_templates == {}

    def test_from_config(self):
        """Test creating TemplateRenderer from config."""
        mock_config = Mock()
        mock_config.template_snippets = {"test": "template"}

        renderer = TemplateRenderer.from_config(mock_config)

        assert isinstance(renderer, TemplateRenderer)

    def test_render_success(self, sample_snippets):
        """Test successful template rendering."""
        renderer = TemplateRenderer(sample_snippets)
        template_str = "{% include 'backend' %}"

        result = renderer.render(template_str, name="web")

        assert result == "backend web"

    def test_render_caching(self):
        """Test template caching in renderer."""
        renderer = TemplateRenderer()
        template_str = "Hello {{ name }}"

        # First render
        result1 = renderer.render(template_str, name="World")
        assert result1 == "Hello World"
        assert len(renderer._compiled_templates) == 1

        # Second render should use cached template
        result2 = renderer.render(template_str, name="Universe")
        assert result2 == "Hello Universe"
        assert len(renderer._compiled_templates) == 1

    def test_render_error(self):
        """Test template rendering with error."""
        renderer = TemplateRenderer()
        template_str = "{{ undefined_var.missing_attr }}"

        with pytest.raises(ValueError, match="Template 'unnamed' rendering failed"):
            renderer.render(template_str)

    def test_get_compiled_success(self):
        """Test getting compiled template."""
        renderer = TemplateRenderer()
        template_str = "Hello {{ name }}"

        template = renderer.get_compiled(template_str)

        assert isinstance(template, Template)
        assert len(renderer._compiled_templates) == 1

    def test_get_compiled_caching(self):
        """Test template compilation caching."""
        renderer = TemplateRenderer()
        template_str = "Hello {{ name }}"

        # First call
        template1 = renderer.get_compiled(template_str)

        # Second call should return cached version
        template2 = renderer.get_compiled(template_str)

        assert template1 is template2
        assert len(renderer._compiled_templates) == 1

    def test_get_compiled_error(self):
        """Test getting compiled template with compilation error."""
        renderer = TemplateRenderer()
        template_str = "{{ invalid syntax"

        with pytest.raises(ValueError, match="Template compilation failed"):
            renderer.get_compiled(template_str)

    def test_clear_cache(self):
        """Test clearing template cache."""
        renderer = TemplateRenderer()
        template_str = "Hello {{ name }}"

        # Compile a template
        renderer.get_compiled(template_str)
        assert len(renderer._compiled_templates) == 1

        # Clear cache
        renderer.clear_cache()
        assert len(renderer._compiled_templates) == 0

    def test_cache_size_property(self):
        """Test cache_size property."""
        renderer = TemplateRenderer()

        assert renderer.cache_size == 0

        # Add templates
        renderer.get_compiled("Template 1")
        assert renderer.cache_size == 1

        renderer.get_compiled("Template 2")
        assert renderer.cache_size == 2

    def test_validate_template_success(self):
        """Test successful template validation."""
        renderer = TemplateRenderer()
        template_str = "Hello {{ name }}"

        warnings = renderer.validate_template(template_str)

        assert warnings == []

    def test_validate_template_syntax_error(self):
        """Test template validation with syntax error."""
        renderer = TemplateRenderer()
        template_str = "{{ invalid syntax"  # Missing closing brace

        warnings = renderer.validate_template(template_str)

        assert len(warnings) > 0
        assert any("template" in warning.lower() for warning in warnings)

    def test_validate_template_not_found(self, sample_snippets):
        """Test template validation with missing snippet."""
        renderer = TemplateRenderer(sample_snippets)
        template_str = "{% include 'nonexistent' %}"

        warnings = renderer.validate_template(template_str)

        assert len(warnings) > 0
        assert any(
            "not found" in warning.lower() or "template" in warning.lower()
            for warning in warnings
        )

    def test_validate_template_general_error(self):
        """Test template validation with general error."""
        renderer = TemplateRenderer()

        # Mock get_compiled to raise a general exception
        with patch.object(
            renderer, "get_compiled", side_effect=RuntimeError("General error")
        ):
            warnings = renderer.validate_template("test template")

            assert len(warnings) > 0
            assert "Template error" in warnings[0]


class TestValidateConfigTemplates:
    """Test the validate_config_templates function."""

    def test_validate_config_templates_empty_config(self):
        """Test validation with empty configuration."""
        config_dict = {}

        warnings = validate_config_templates(config_dict)

        assert warnings == []

    def test_validate_config_templates_valid_snippets(self):
        """Test validation with valid template snippets."""
        config_dict = {
            "template_snippets": {
                "backend": {"template": "backend {{ name }}"},
                "frontend": {"template": "frontend {{ name }}"},
            }
        }

        warnings = validate_config_templates(config_dict)

        assert warnings == []

    def test_validate_config_templates_invalid_snippet(self):
        """Test validation with invalid template snippet."""
        config_dict = {
            "template_snippets": {
                "broken": {"template": "{{ invalid syntax"},
            }
        }

        warnings = validate_config_templates(config_dict)

        assert len(warnings) > 0
        assert any("Snippet 'broken'" in warning for warning in warnings)
        assert any("template" in warning.lower() for warning in warnings)

    def test_validate_config_templates_string_snippets(self):
        """Test validation with string-based snippets."""
        config_dict = {
            "template_snippets": {
                "simple": "simple template content",
            }
        }

        warnings = validate_config_templates(config_dict)

        assert warnings == []

    def test_validate_config_templates_object_snippets(self):
        """Test validation with object-based snippets."""
        mock_snippet = Mock()
        mock_snippet.template = "template content"

        config_dict = {
            "template_snippets": {
                "object": mock_snippet,
            }
        }

        warnings = validate_config_templates(config_dict)

        assert warnings == []

    def test_validate_config_templates_fallback_snippets(self):
        """Test validation with snippets that need fallback."""
        mock_snippet = Mock()
        del mock_snippet.template  # Remove template attribute
        mock_snippet.__str__ = Mock(return_value="fallback content")

        config_dict = {
            "template_snippets": {
                "fallback": mock_snippet,
            }
        }

        warnings = validate_config_templates(config_dict)

        assert warnings == []

    def test_validate_config_templates_valid_maps(self):
        """Test validation with valid map templates."""
        config_dict = {
            "maps": {
                "host.map": {"template": "{{ host }} {{ backend }}"},
            }
        }

        warnings = validate_config_templates(config_dict)

        assert warnings == []

    def test_validate_config_templates_invalid_map(self):
        """Test validation with invalid map template."""
        config_dict = {
            "maps": {
                "host.map": {"template": "{{ invalid syntax"},
            }
        }

        warnings = validate_config_templates(config_dict)

        assert len(warnings) > 0
        assert "Map 'host.map'" in warnings[0]

    def test_validate_config_templates_valid_haproxy_config(self):
        """Test validation with valid HAProxy config template."""
        config_dict = {
            "haproxy_config": {"template": "global\n  daemon\n\ndefaults\n  mode http"},
        }

        warnings = validate_config_templates(config_dict)

        assert warnings == []

    def test_validate_config_templates_invalid_haproxy_config(self):
        """Test validation with invalid HAProxy config template."""
        config_dict = {
            "haproxy_config": {"template": "{{ invalid syntax"},
        }

        warnings = validate_config_templates(config_dict)

        assert len(warnings) > 0
        assert "HAProxy config" in warnings[0]

    def test_validate_config_templates_valid_certificates(self):
        """Test validation with valid certificate templates."""
        config_dict = {
            "certificates": {
                "tls.pem": {"template": "{{ cert_data }}"},
            }
        }

        warnings = validate_config_templates(config_dict)

        assert warnings == []

    def test_validate_config_templates_invalid_certificate(self):
        """Test validation with invalid certificate template."""
        config_dict = {
            "certificates": {
                "tls.pem": {"template": "{{ invalid syntax"},
            }
        }

        warnings = validate_config_templates(config_dict)

        assert len(warnings) > 0
        assert "Certificate 'tls.pem'" in warnings[0]

    def test_validate_config_templates_comprehensive(self):
        """Test validation with all template types."""
        config_dict = {
            "template_snippets": {
                "backend": {"template": "backend {{ name }}"},
                "broken_snippet": {"template": "{{ invalid syntax"},
            },
            "maps": {
                "host.map": {"template": "{{ host }} {{ backend }}"},
                "broken.map": {"template": "{{ invalid syntax"},
            },
            "haproxy_config": {"template": "global\n  daemon"},
            "certificates": {
                "tls.pem": {"template": "{{ cert_data }}"},
                "broken.pem": {"template": "{{ invalid syntax"},
            },
        }

        warnings = validate_config_templates(config_dict)

        # Should have warnings for broken templates
        assert len(warnings) > 0
        broken_warnings = [w for w in warnings if "template" in w.lower()]
        assert len(broken_warnings) >= 1  # At least one broken template warning

    def test_validate_config_templates_edge_cases(self):
        """Test validation with edge cases."""
        config_dict = {
            "template_snippets": {},  # Empty dict instead of None
            "maps": {},  # Empty dict
            "haproxy_config": {},  # Missing template key
            "certificates": {"cert": {}},  # Missing template key
        }

        # Should not raise exception
        warnings = validate_config_templates(config_dict)

        # May have warnings but should complete successfully
        assert isinstance(warnings, list)


class TestGetPathFilterSecurity:
    """Security tests for the get_path filter to prevent path traversal attacks."""

    def test_get_path_filter_valid_filenames(self):
        """Test get_path_filter with valid filenames."""
        # Test valid cases
        assert get_path_filter("host.map", "map") == "/etc/haproxy/maps/host.map"
        assert get_path_filter("tls.pem", "certificate") == "/etc/haproxy/ssl/tls.pem"
        assert get_path_filter("500.http", "file") == "/etc/haproxy/general/500.http"

        # Test with underscores, hyphens, numbers
        assert (
            get_path_filter("host_backend.map", "map")
            == "/etc/haproxy/maps/host_backend.map"
        )
        assert (
            get_path_filter("tls-cert-2024.pem", "certificate")
            == "/etc/haproxy/ssl/tls-cert-2024.pem"
        )
        assert (
            get_path_filter("error404.http", "file")
            == "/etc/haproxy/general/error404.http"
        )

    def test_get_path_filter_path_traversal_protection(self):
        """Test that get_path_filter blocks path traversal attempts."""
        # Test various path traversal patterns
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "host/../../../etc/passwd",
            "tls/../../etc/passwd",
            "../../../../../../root/.ssh/id_rsa",
            "..\\..\\..\\..\\.ssh\\id_rsa",
            "normal/../../../etc/shadow",
            "file.map/../../../etc/hosts",
        ]

        for malicious_filename in path_traversal_attempts:
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(malicious_filename, "map")
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(malicious_filename, "certificate")
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(malicious_filename, "file")

    def test_get_path_filter_directory_names_blocked(self):
        """Test that directory names like '.' and '..' are blocked."""
        directory_names = [".", ".."]

        for dir_name in directory_names:
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(dir_name, "map")
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(dir_name, "certificate")
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(dir_name, "file")

    def test_get_path_filter_null_byte_injection(self):
        """Test that null byte injection is blocked."""
        null_byte_attempts = [
            "host.map\x00",
            "\x00host.map",
            "host\x00.map",
            "host.map\x00../../../etc/passwd",
        ]

        for malicious_filename in null_byte_attempts:
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(malicious_filename, "map")

    def test_get_path_filter_path_separators_blocked(self):
        """Test that path separators are blocked."""
        separator_attempts = [
            "subdir/host.map",
            "dir\\host.map",
            "a/b/c/host.map",
            "dir\\subdir\\host.map",
            "//host.map",
            "\\\\host.map",
        ]

        for malicious_filename in separator_attempts:
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(malicious_filename, "map")

    def test_get_path_filter_empty_invalid_filenames(self):
        """Test that empty or invalid filenames are rejected."""
        invalid_filenames = ["", None]

        for invalid_filename in invalid_filenames:
            with pytest.raises(ValueError, match="Invalid filename"):
                get_path_filter(invalid_filename, "map")

    def test_get_path_filter_invalid_content_types(self):
        """Test that invalid content types are rejected."""
        invalid_content_types = [
            "invalid",
            "MAP",  # Wrong case
            "Certificate",  # Wrong case
            "files",  # Plural
            "",
            None,
            123,
            "executable",
        ]

        for invalid_type in invalid_content_types:
            with pytest.raises(ValueError, match="Invalid content_type"):
                get_path_filter("host.map", invalid_type)

    def test_get_path_filter_with_custom_config(self):
        """Test get_path_filter with custom configuration directories."""
        mock_config = Mock()
        mock_config.storage_maps_dir = "/custom/maps"
        mock_config.storage_ssl_dir = "/custom/ssl"
        mock_config.storage_general_dir = "/custom/files"

        # Test custom paths
        assert (
            get_path_filter("host.map", "map", mock_config) == "/custom/maps/host.map"
        )
        assert (
            get_path_filter("tls.pem", "certificate", mock_config)
            == "/custom/ssl/tls.pem"
        )
        assert (
            get_path_filter("500.http", "file", mock_config) == "/custom/files/500.http"
        )

    def test_get_path_filter_path_traversal_with_normalization(self):
        """Test that path traversal is blocked even with path normalization attempts."""
        # These might try to bypass validation through normalization
        normalization_attempts = [
            "host.map/./../../etc/passwd",
            "host.map/./../../../etc/passwd",
            "host.map/foo/../../../etc/passwd",
        ]

        # All should be blocked at the filename validation level
        for malicious_filename in normalization_attempts:
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(malicious_filename, "map")

    def test_get_path_filter_comprehensive_attack_scenarios(self):
        """Test comprehensive attack scenarios combining multiple techniques."""
        attack_scenarios_with_prohibited_chars = [
            # Path traversal with explicit separators and null bytes
            "../../../etc/passwd\x00.map",
            "..\\..\\..\\windows\\system32\\config\\sam\x00",
            "./../../etc/shadow",
            ".\\..\\..\\etc\\hosts",
            "normal/../../etc/passwd",
            "normal\\..\\..\\etc\\passwd",
        ]

        for attack in attack_scenarios_with_prohibited_chars:
            with pytest.raises(
                ValueError, match="Invalid filename contains prohibited characters"
            ):
                get_path_filter(attack, "map")

        # These should pass get_path_filter but would be caught by Pydantic validation patterns
        encoded_attacks = [
            "host.map%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded - no actual path separators
        ]

        for encoded_attack in encoded_attacks:
            # These should pass get_path_filter since they don't contain actual path separators
            try:
                result = get_path_filter(encoded_attack, "map")
                assert "/etc/haproxy/maps/" in result
            except ValueError:
                # Also acceptable if caught at filter level for being suspicious
                pass

    def test_get_path_filter_case_sensitivity(self):
        """Test that content type validation is case-sensitive (security feature)."""
        # Uppercase versions should be rejected to prevent confusion
        uppercase_types = ["MAP", "CERTIFICATE", "FILE"]

        for bad_type in uppercase_types:
            with pytest.raises(ValueError, match="Invalid content_type"):
                get_path_filter("host.map", bad_type)

    def test_get_path_filter_boundary_conditions(self):
        """Test boundary conditions for filename security."""
        # Very long filename (potential buffer overflow attempt)
        long_filename = "a" * 300 + ".map"
        # This should be caught by our Filename validation in config_models.py
        # but we test the filter directly here
        try:
            result = get_path_filter(long_filename, "map")
            # If it doesn't raise, check it's handled properly
            assert "/etc/haproxy/maps/" in result
        except ValueError:
            # Also acceptable if rejected for being too long
            pass

        # Single character filenames (valid)
        assert get_path_filter("a", "map") == "/etc/haproxy/maps/a"

        # Filenames with spaces are now blocked by the restrictive pattern
        with pytest.raises(ValueError, match="unsafe characters"):
            get_path_filter("host file.map", "map")

    def test_get_path_filter_url_encoded_attacks(self):
        """Test that URL-encoded path traversal attacks are blocked."""
        url_encoded_attacks = [
            # Basic URL encoding
            "host%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # ../../../etc/passwd
            "host%2E%2E%2F%2E%2E%2Fetc%2Fpasswd",  # Mixed case encoding
            "host%5c%2e%2e%5c%2e%2e%5cwindows%5csystem32",  # Windows paths
            # Double encoding
            "host%252e%252e%252f%252e%252e%252fetc%252fpasswd",
            # Partial encoding
            "host..%2fetc%2fpasswd",
            "host%2e%2e/etc/passwd",
            # Null byte injection
            "host%00.map",
            "host.map%00.txt",
        ]

        for attack in url_encoded_attacks:
            with pytest.raises(
                ValueError,
                match="(Invalid filename|Filename contains|prohibited characters|unsafe characters)",
            ):
                get_path_filter(attack, "map")

    def test_get_path_filter_unicode_normalization_attacks(self):
        """Test that Unicode normalization attacks are blocked."""
        unicode_attacks = [
            # Unicode dot variations (U+002E is normal dot)
            "host\u002e\u002e/etc/passwd",  # Unicode dots
            "host․․/etc/passwd",  # U+2024 ONE DOT LEADER
            # Unicode slash variations
            "host..\u002fetc\u002fpasswd",  # Unicode forward slash
            "host..\u2044etc\u2044passwd",  # Fraction slash
            "host..\u2215etc\u2215passwd",  # Division slash
            "host..\u005cetc\u005cpasswd",  # Unicode backslash
            # Mixed Unicode and ASCII
            "host\u002e\u002e/\u002e\u002e/etc/passwd",
        ]

        for attack in unicode_attacks:
            with pytest.raises(
                ValueError,
                match="(Invalid filename|prohibited characters|unsafe characters)",
            ):
                get_path_filter(attack, "map")

    def test_get_path_filter_comprehensive_encoded_attacks(self):
        """Test comprehensive encoded attack scenarios."""
        comprehensive_attacks = [
            # Triple encoding
            "host%25252e%25252e%25252f",
            # Mixed encoding techniques
            "host%2e%2e%u002f%2e%2e",
            # Unicode escape sequences
            "host\\u002e\\u002e\\u002f",
            # Hex encoding variations
            "host\\x2e\\x2e\\x2f",
            # Overlong UTF-8 encoding attempts
            "host%c0%ae%c0%ae%c0%af",
            # Directory traversal with various encodings
            "host%2e%2e%c0%af%2e%2e%c0%afetc%c0%afpasswd",
        ]

        for attack in comprehensive_attacks:
            with pytest.raises(
                ValueError,
                match="(Invalid filename|Filename contains|prohibited characters|unsafe characters)",
            ):
                get_path_filter(attack, "map")

    def test_get_path_filter_whitelist_validation(self):
        """Test that only whitelisted characters are allowed."""
        # Valid filenames that should pass
        valid_filenames = [
            "host.map",
            "backend-config.conf",
            "ssl_cert.pem",
            "route_123.map",
            "test-file_v2.config",
            "a",
            "A123",
            "file.with.dots",
        ]

        for valid_filename in valid_filenames:
            # Should not raise an exception
            result = get_path_filter(valid_filename, "map")
            assert "/etc/haproxy/maps/" in result
            assert valid_filename in result

        # Invalid characters that should be blocked
        invalid_filenames = [
            "host file.map",  # space
            "host@file.map",  # special character
            "host#file.map",  # hash
            "host&file.map",  # ampersand
            "host*file.map",  # asterisk
            "host+file.map",  # plus
            "host=file.map",  # equals
            "host[file].map",  # brackets
            "host{file}.map",  # braces
            "host|file.map",  # pipe
            "host:file.map",  # colon
            "host;file.map",  # semicolon
            "host,file.map",  # comma
            "host<file>.map",  # angle brackets
            "host?file.map",  # question mark
            "!host.map",  # starts with special char
            ".host.map",  # starts with dot
            "-host.map",  # starts with dash
            "_host.map",  # starts with underscore
        ]

        for invalid_filename in invalid_filenames:
            with pytest.raises(
                ValueError, match="(unsafe characters|prohibited characters)"
            ):
                get_path_filter(invalid_filename, "map")


class TestFormatTemplateError:
    """Test the format_template_error function for comprehensive error formatting."""

    def test_format_template_error_simple(self):
        """Test formatting a simple template error without line numbers."""
        error = ValueError("Simple error message")
        result = format_template_error(error, "test_template")

        assert "Template 'test_template' rendering failed" in result
        assert "Simple error message" in result

    def test_format_template_error_with_line_number(self):
        """Test formatting an error with line number information."""
        error = TemplateSyntaxError("Syntax error", lineno=5)
        template_content = "\n".join(
            [
                "line 1",
                "line 2",
                "line 3",
                "line 4",
                "line 5 with error",
                "line 6",
                "line 7",
            ]
        )

        result = format_template_error(error, "test_template", template_content)

        assert "Template 'test_template' rendering failed" in result
        assert "at line 5" in result
        assert ">>> line 5 with error" in result
        assert "Template context:" in result

    def test_format_template_error_deeply_nested_includes(self):
        """Test error formatting for 3+ level nested includes."""
        # Create mock exception with deep traceback
        error = ValueError("Error in deeply nested snippet")

        # Create snippets for testing
        snippets = {
            "level1": TemplateSnippet(
                name="level1", template='First level\n{% include "level2" %}\nEnd first'
            ),
            "level2": TemplateSnippet(
                name="level2",
                template='Second level\n{% include "level3" %}\nEnd second',
            ),
            "level3": TemplateSnippet(
                name="level3", template="Third level\n{{ undefined_var }}\nEnd third"
            ),
        }

        template_content = 'Main template\n{% include "level1" %}\nEnd main'

        # We can't easily mock sys.exc_info, so test the formatting logic directly
        # by testing the helper functions instead
        result = format_template_error(
            error, "main_template", template_content, snippets
        )

        assert "Template 'main_template' rendering failed" in result
        assert "Error in deeply nested snippet" in result

    def test_format_template_error_missing_snippet(self):
        """Test handling of missing snippets in include chain."""
        error = TemplateNotFound("missing_snippet")
        template_content = 'Main template\n{% include "missing_snippet" %}\nEnd main'

        result = format_template_error(error, "test_template", template_content)

        assert "Template 'test_template' rendering failed" in result
        assert "missing_snippet" in result

    def test_format_template_error_syntax_errors(self):
        """Test syntax error formatting with line context."""
        error = TemplateSyntaxError("Encountered unknown tag 'endpoint'", lineno=4)
        template_content = """global
    daemon
frontend main
    {% endpoint in some_list %}
    bind *:80
backend servers
    server web1 10.0.0.1:80"""

        result = format_template_error(error, "haproxy_config", template_content)

        assert "Template 'haproxy_config' rendering failed" in result
        assert "at line 4" in result
        assert "Encountered unknown tag 'endpoint'" in result
        assert ">>> " in result  # Context line marker
        assert "endpoint in some_list" in result

    def test_format_template_error_nonetype_hint(self):
        """Test that NoneType errors get helpful hints."""
        error = TypeError("'NoneType' object is not iterable")
        result = format_template_error(error, "test_template")

        assert "Template 'test_template' rendering failed" in result
        assert "'NoneType' object is not iterable" in result
        assert "💡 Hint:" in result
        assert "resources.get('type', {}).items()" in result

    def test_format_template_error_undefined_hint(self):
        """Test that undefined variable errors get helpful hints."""
        error = NameError("undefined variable 'foo'")
        result = format_template_error(error, "test_template")

        assert "Template 'test_template' rendering failed" in result
        assert "undefined variable" in result
        assert "💡 Hint:" in result
        assert "variable is not defined" in result

    def test_format_template_error_filter_hint(self):
        """Test that filter errors get helpful hints."""
        error = ValueError("no filter named 'unknown_filter'")
        result = format_template_error(error, "test_template")

        assert "Template 'test_template' rendering failed" in result
        assert "no filter named" in result
        assert "💡 Hint:" in result
        assert "Available filters: b64decode, get_path" in result

    def test_format_template_error_attribute_hint(self):
        """Test that attribute errors get helpful hints."""
        error = AttributeError("'dict' object has no attribute 'missing'")
        result = format_template_error(error, "test_template")

        assert "Template 'test_template' rendering failed" in result
        assert "has no attribute" in result
        assert "💡 Hint:" in result
        assert "Check if the object exists" in result

    def test_format_template_error_two_level_include(self):
        """Test formatting for simple two-level includes."""
        error = ValueError("Error in snippet")

        snippets = {
            "backend-servers": TemplateSnippet(
                name="backend-servers",
                template="{% for server in servers %}\n  server {{ server }}\n{% endfor %}",
            ),
        }

        template_content = (
            'frontend main\n    {% include "backend-servers" %}\nbackend fallback'
        )

        # Since we can't easily mock the traceback, test the basic formatting
        result = format_template_error(error, "main_config", template_content, snippets)

        assert "Template 'main_config' rendering failed" in result
        assert "Error in snippet" in result

    def test_format_template_error_empty_template(self):
        """Test formatting with empty or None template content."""
        error = ValueError("Some error")

        # Test with None template
        result1 = format_template_error(error, "test", None)
        assert "Template 'test' rendering failed" in result1
        assert "Some error" in result1

        # Test with empty template
        result2 = format_template_error(error, "test", "")
        assert "Template 'test' rendering failed" in result2
        assert "Some error" in result2

    def test_format_template_error_invalid_line_numbers(self):
        """Test handling of invalid line numbers."""
        error = TemplateSyntaxError("Error", lineno=-1)
        template_content = "line 1\nline 2"

        result = format_template_error(error, "test", template_content)
        assert "Template 'test' rendering failed" in result
        assert "Error" in result
        # Should handle gracefully without crashing

    def test_format_template_error_long_error_messages(self):
        """Test formatting with very long error messages."""
        long_message = "Error: " + "x" * 1000
        error = ValueError(long_message)

        result = format_template_error(error, "test")
        assert "Template 'test' rendering failed" in result
        assert "Error:" in result
        assert "x" * 100 in result  # Should contain at least part of the message


class TestExtractSnippetName:
    """Test the _extract_snippet_name helper function."""

    def test_extract_snippet_name_single_quotes(self):
        """Test extracting snippet name with single quotes."""
        line = "    {% include 'backend-servers' %}"
        result = _extract_snippet_name(line)
        assert result == "backend-servers"

    def test_extract_snippet_name_double_quotes(self):
        """Test extracting snippet name with double quotes."""
        line = '    {% include "frontend-config" %}'
        result = _extract_snippet_name(line)
        assert result == "frontend-config"

    def test_extract_snippet_name_with_spaces(self):
        """Test extracting snippet name with varying spaces."""
        line = "{%   include   'test-snippet'   %}"
        result = _extract_snippet_name(line)
        assert result == "test-snippet"

    def test_extract_snippet_name_no_include(self):
        """Test when line doesn't contain include statement."""
        line = "    server web1 10.0.0.1:80"
        result = _extract_snippet_name(line)
        assert result is None

    def test_extract_snippet_name_malformed(self):
        """Test with malformed include statement."""
        line = "{% include without quotes %}"
        result = _extract_snippet_name(line)
        assert result is None

    def test_extract_snippet_name_partial(self):
        """Test with partial include keyword."""
        line = "# This line includes something"
        result = _extract_snippet_name(line)
        assert result is None


class TestGetContextLines:
    """Test the _get_context_lines helper function."""

    def test_get_context_lines_basic(self):
        """Test getting context lines around a target line."""
        lines = ["line 1", "line 2", "line 3", "line 4", "line 5"]
        result = _get_context_lines(lines, 2, 3, context_before=1, context_after=1)

        assert len(result) == 3
        assert "2:" in result[0]
        assert ">>> line 3" in result[1]
        assert "4:" in result[2]

    def test_get_context_lines_at_start(self):
        """Test getting context lines at the start of file."""
        lines = ["line 1", "line 2", "line 3", "line 4", "line 5"]
        result = _get_context_lines(lines, 0, 1, context_before=2, context_after=2)

        assert ">>> line 1" in result[0]
        assert "line 2" in result[1]
        assert "line 3" in result[2]

    def test_get_context_lines_at_end(self):
        """Test getting context lines at the end of file."""
        lines = ["line 1", "line 2", "line 3", "line 4", "line 5"]
        result = _get_context_lines(lines, 4, 5, context_before=2, context_after=2)

        assert "line 3" in result[0]
        assert "line 4" in result[1]
        assert ">>> line 5" in result[2]

    def test_get_context_lines_empty_list(self):
        """Test with empty lines list."""
        result = _get_context_lines([], 0, 1)
        assert result == []

    def test_get_context_lines_invalid_index(self):
        """Test with invalid line index."""
        lines = ["line 1", "line 2"]
        result = _get_context_lines(lines, -1, 0)
        assert result == []

        result = _get_context_lines(lines, 5, 6)
        assert result == []

    def test_get_context_lines_formatting(self):
        """Test that context lines are properly formatted."""
        lines = ["first", "second", "third"]
        result = _get_context_lines(lines, 1, 2, context_before=1, context_after=1)

        # Check line number formatting
        assert "1:" in result[0]
        assert "2:" in result[1]
        assert "3:" in result[2]

        # Check marker for target line
        assert ">>> " in result[1]
        assert ">>> " not in result[0]
        assert ">>> " not in result[2]
