"""
Unit tests for TUI lexers module.

Tests the custom HAProxy lexer for syntax highlighting,
including token recognition, keyword matching, and pattern handling.
"""

import pytest
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    String,
    Whitespace,
    Operator,
    Punctuation,
    Literal,
)

from haproxy_template_ic.tui.lexers import HAProxyLexer


class TestHAProxyLexer:
    """Test the HAProxyLexer class."""

    @pytest.fixture
    def lexer(self):
        """Create an HAProxyLexer instance."""
        return HAProxyLexer()

    def test_lexer_attributes(self, lexer):
        """Test lexer basic attributes."""
        assert lexer.name == "HAProxy"
        assert "haproxy" in lexer.aliases
        assert "haproxy-config" in lexer.aliases
        assert "*.cfg" in lexer.filenames
        assert "text/x-haproxy-config" in lexer.mimetypes

    def test_comment_tokenization(self, lexer):
        """Test comment tokenization."""
        text = "# This is a comment"
        tokens = list(lexer.get_tokens(text))

        # Should contain comment token
        assert any(token[0] == Comment.Single for token in tokens)
        # Should capture the comment text
        comment_tokens = [token for token in tokens if token[0] == Comment.Single]
        assert len(comment_tokens) == 1
        assert "This is a comment" in comment_tokens[0][1]

    def test_section_keywords(self, lexer):
        """Test section keyword tokenization."""
        sections = ["global", "defaults", "frontend", "backend", "listen"]

        for section in sections:
            tokens = list(lexer.get_tokens(section))
            # Should contain namespace keyword token
            assert any(token[0] == Keyword.Namespace for token in tokens)

    def test_timeout_directives(self, lexer):
        """Test timeout directive tokenization."""
        text = "timeout connect 5000ms\ntimeout client 30s"
        tokens = list(lexer.get_tokens(text))

        # Should contain builtin name tokens for timeout types
        builtin_tokens = [token for token in tokens if token[0] == Name.Builtin]
        assert len(builtin_tokens) >= 2

        # Should contain timeout values with units
        number_tokens = [token for token in tokens if token[0] == Number.Integer]
        assert len(number_tokens) >= 2

    def test_option_directives(self, lexer):
        """Test option directive tokenization."""
        text = "option httplog\noption forwardfor"
        tokens = list(lexer.get_tokens(text))

        # Should contain builtin name tokens for option types
        builtin_tokens = [token for token in tokens if token[0] == Name.Builtin]
        assert len(builtin_tokens) >= 2

    def test_balance_algorithms(self, lexer):
        """Test balance algorithm tokenization."""
        text = "balance roundrobin\nbalance leastconn"
        tokens = list(lexer.get_tokens(text))

        # Should contain builtin name tokens for balance algorithms
        builtin_tokens = [token for token in tokens if token[0] == Name.Builtin]
        assert len(builtin_tokens) >= 2

    def test_server_directives(self, lexer):
        """Test server directive tokenization."""
        text = "server web1 192.168.1.10:80 check"
        tokens = list(lexer.get_tokens(text))

        # Should contain keyword for 'server'
        keyword_tokens = [token for token in tokens if token[0] == Keyword]
        assert any("server" in token[1] for token in keyword_tokens)

        # Should contain variable name for server name
        variable_tokens = [token for token in tokens if token[0] == Name.Variable]
        assert any("web1" in token[1] for token in variable_tokens)

    def test_ip_address_tokenization(self, lexer):
        """Test IP address tokenization."""
        # IPv4 addresses
        ipv4_addresses = ["192.168.1.1", "10.0.0.0/8", "172.16.0.0/12", "127.0.0.1"]

        for ip in ipv4_addresses:
            tokens = list(lexer.get_tokens(ip))
            # Should contain literal number token for IP
            assert any(token[0] == Literal.Number for token in tokens)

    def test_ipv6_address_tokenization(self, lexer):
        """Test IPv6 address tokenization."""
        ipv6_addresses = [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "::1",
            "2001:db8::1",
        ]

        for ip in ipv6_addresses:
            tokens = list(lexer.get_tokens(ip))
            # Should contain some form of number token for IPv6 components
            number_tokens = [token for token in tokens if "Number" in str(token[0])]
            assert len(number_tokens) >= 1, (
                f"No number tokens found for {ip}, got: {tokens}"
            )

    def test_port_numbers(self, lexer):
        """Test port number tokenization."""
        text = "bind *:80\nbind *:443-8443"
        tokens = list(lexer.get_tokens(text))

        # Should contain integer number tokens for ports
        number_tokens = [token for token in tokens if token[0] == Number.Integer]
        assert len(number_tokens) >= 2

    def test_time_units(self, lexer):
        """Test time unit tokenization."""
        time_values = ["5000ms", "30s", "10m", "1h", "7d"]

        for time_val in time_values:
            tokens = list(lexer.get_tokens(time_val))
            # Should contain integer number token
            assert any(token[0] == Number.Integer for token in tokens)

    def test_percentages_and_weights(self, lexer):
        """Test percentage and weight tokenization."""
        text = "weight 100\ncheck inter 2000ms rise 3 fall 5"
        tokens = list(lexer.get_tokens(text))

        # Should contain attribute names
        attribute_tokens = [token for token in tokens if token[0] == Name.Attribute]
        assert len(attribute_tokens) >= 3  # weight, rise, fall

        # Should contain integer values
        number_tokens = [token for token in tokens if token[0] == Number.Integer]
        assert len(number_tokens) >= 4

    def test_http_status_codes(self, lexer):
        """Test HTTP status code tokenization."""
        status_codes = ["200", "404", "500", "status 301"]

        for status in status_codes:
            tokens = list(lexer.get_tokens(status))
            # Should contain integer number token
            assert any(token[0] == Number.Integer for token in tokens)

    def test_http_methods(self, lexer):
        """Test HTTP method tokenization."""
        methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]

        for method in methods:
            tokens = list(lexer.get_tokens(method))
            # Should contain builtin name token
            assert any(token[0] == Name.Builtin for token in tokens)

    def test_quoted_strings(self, lexer):
        """Test quoted string tokenization."""
        text = "\"Hello World\" 'Single quoted'"
        tokens = list(lexer.get_tokens(text))

        # Should contain double and single quoted strings
        string_tokens = [
            token for token in tokens if token[0] in (String.Double, String.Single)
        ]
        assert len(string_tokens) == 2

    def test_file_paths(self, lexer):
        """Test file path tokenization."""
        paths = ["/var/log/haproxy.log", "/etc/ssl/certs/cert.pem"]

        for path in paths:
            tokens = list(lexer.get_tokens(path))
            # Should contain string token
            assert any(token[0] == String for token in tokens)

    def test_urls(self, lexer):
        """Test URL tokenization."""
        urls = ["http://example.com", "https://api.example.com/v1"]

        for url in urls:
            tokens = list(lexer.get_tokens(url))
            # Should contain string token
            assert any(token[0] == String for token in tokens)

    def test_boolean_values(self, lexer):
        """Test boolean value tokenization."""
        booleans = ["on", "off", "yes", "no", "true", "false", "enabled", "disabled"]

        for boolean in booleans:
            tokens = list(lexer.get_tokens(boolean))
            # Should contain either constant name token or keyword token
            has_constant = any(token[0] == Name.Constant for token in tokens)
            has_keyword = any(token[0] == Keyword for token in tokens)
            assert has_constant or has_keyword, (
                f"No constant or keyword token found for {boolean}, got: {tokens}"
            )

    def test_server_parameters(self, lexer):
        """Test server parameter tokenization."""
        text = "server web1 192.168.1.1:80 check backup weight 100 maxconn 1000"
        tokens = list(lexer.get_tokens(text))

        # Should contain attribute or keyword tokens for server parameters
        attribute_tokens = [
            token for token in tokens if token[0] in (Name.Attribute, Keyword)
        ]
        expected_attrs = ["check", "backup", "weight", "maxconn"]

        attr_values = [token[1] for token in attribute_tokens]
        for attr in expected_attrs:
            assert any(attr in attr_val for attr_val in attr_values), (
                f"Attribute {attr} not found in {attr_values}"
            )

    def test_acl_expressions(self, lexer):
        """Test ACL expression tokenization."""
        text = "acl is_static path_end -i .jpg .gif .png"
        tokens = list(lexer.get_tokens(text))

        # Should contain keyword for 'acl'
        keyword_tokens = [token for token in tokens if token[0] == Keyword]
        assert any("acl" in token[1] for token in keyword_tokens)

    def test_operators_and_punctuation(self, lexer):
        """Test operator and punctuation tokenization."""
        text = "balance uri depth 1 len 64"
        tokens = list(lexer.get_tokens(text))

        # Should handle various tokens
        assert any(
            token[0] in (Operator, Punctuation, Name, Number.Integer, Keyword)
            for token in tokens
        )

    def test_whitespace_handling(self, lexer):
        """Test whitespace tokenization."""
        text = "global\n    daemon\n    maxconn 4000"
        tokens = list(lexer.get_tokens(text))

        # Should contain whitespace tokens
        whitespace_tokens = [token for token in tokens if token[0] == Whitespace]
        assert len(whitespace_tokens) > 0

    def test_complex_haproxy_config(self, lexer):
        """Test tokenization of a complex HAProxy configuration."""
        config = """
# HAProxy Configuration
global
    daemon
    maxconn 4000
    log 127.0.0.1:514 local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend web_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/haproxy.pem
    redirect scheme https if !{ ssl_fc }
    default_backend web_servers

backend web_servers
    balance roundrobin
    option httpchk GET /health
    server web1 192.168.1.10:80 check
    server web2 192.168.1.11:80 check backup
"""

        tokens = list(lexer.get_tokens(config))

        # Should contain various token types
        token_types = set(token[0] for token in tokens)

        expected_types = {
            Comment.Single,
            Keyword.Namespace,
            Keyword,
            Name.Builtin,
            Name.Variable,
            Name.Attribute,
            Number.Integer,
            Literal.Number,
            String,
            Whitespace,
        }

        # Check that most expected types are present
        present_types = expected_types.intersection(token_types)
        assert len(present_types) >= 6  # At least 6 of the expected types

    def test_lexer_consistency(self, lexer):
        """Test lexer consistency with repeated tokenization."""
        text = "global\n    daemon\nfrontend web\n    bind *:80"

        # Tokenize the same text multiple times
        tokens1 = list(lexer.get_tokens(text))
        tokens2 = list(lexer.get_tokens(text))

        # Should produce identical results
        assert tokens1 == tokens2

    def test_empty_input(self, lexer):
        """Test lexer with empty input."""
        tokens = list(lexer.get_tokens(""))
        # Should handle empty input gracefully
        assert isinstance(tokens, list)

    def test_whitespace_only_input(self, lexer):
        """Test lexer with whitespace-only input."""
        text = "   \n\t  \n   "
        tokens = list(lexer.get_tokens(text))

        # Should contain only whitespace tokens
        non_whitespace_tokens = [token for token in tokens if token[0] != Whitespace]
        assert len(non_whitespace_tokens) == 0

    def test_comment_only_input(self, lexer):
        """Test lexer with comment-only input."""
        text = "# This is just a comment\n# Another comment"
        tokens = list(lexer.get_tokens(text))

        # Should contain comment and whitespace tokens only
        token_types = set(token[0] for token in tokens)
        assert token_types.issubset({Comment.Single, Whitespace})

    def test_unknown_keywords(self, lexer):
        """Test lexer with unknown keywords."""
        text = "unknown_keyword some_value"
        tokens = list(lexer.get_tokens(text))

        # Should handle unknown keywords as generic names
        name_tokens = [token for token in tokens if token[0] == Name]
        assert len(name_tokens) >= 1

    def test_lexer_instantiation(self):
        """Test that lexer can be instantiated multiple times."""
        lexer1 = HAProxyLexer()
        lexer2 = HAProxyLexer()

        # Should be separate instances
        assert lexer1 is not lexer2

        # But should have same attributes
        assert lexer1.name == lexer2.name
        assert lexer1.aliases == lexer2.aliases

    def test_keyword_collections(self, lexer):
        """Test that keyword collections are properly defined."""
        # Test that keyword collections exist and contain expected items
        assert hasattr(lexer, "sections")
        assert hasattr(lexer, "global_keywords")
        assert hasattr(lexer, "proxy_keywords")
        assert hasattr(lexer, "option_keywords")
        assert hasattr(lexer, "timeout_keywords")
        assert hasattr(lexer, "balance_algorithms")
        assert hasattr(lexer, "check_methods")

        # Test that collections are tuples/lists and non-empty
        assert len(lexer.sections) > 0
        assert len(lexer.global_keywords) > 0
        assert len(lexer.proxy_keywords) > 0
        assert len(lexer.option_keywords) > 0

        # Test that common keywords are present
        assert "global" in lexer.sections
        assert "frontend" in lexer.sections
        assert "backend" in lexer.sections
        assert "maxconn" in lexer.global_keywords
        assert "bind" in lexer.proxy_keywords
        assert "roundrobin" in lexer.balance_algorithms

    def test_token_rules_structure(self, lexer):
        """Test that token rules are properly structured."""
        # Should have a 'root' state in tokens
        assert "root" in lexer.tokens

        # Root should contain rules
        root_rules = lexer.tokens["root"]
        assert isinstance(root_rules, list)
        assert len(root_rules) > 0

        # Each rule should be a tuple
        for rule in root_rules:
            assert isinstance(rule, tuple)
            assert len(rule) >= 2  # Pattern and token type
