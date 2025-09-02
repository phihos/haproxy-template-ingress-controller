"""
Custom Pygments lexers for the TUI dashboard.

This module provides custom lexers for syntax highlighting in the template inspector.
"""

from pygments.lexer import RegexLexer, words, bygroups
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    String,
    Text,
    Whitespace,
    Operator,
    Punctuation,
    Generic,
    Literal,
)

__all__ = ["HAProxyLexer"]


class HAProxyLexer(RegexLexer):
    """Custom lexer for HAProxy configuration files."""

    name = "HAProxy"
    aliases = ["haproxy", "haproxy-config"]
    filenames = ["*.cfg"]
    mimetypes = ["text/x-haproxy-config"]

    # HAProxy section keywords
    sections = (
        "global",
        "defaults",
        "frontend",
        "backend",
        "listen",
        "cache",
        "resolvers",
        "mailers",
        "peers",
        "program",
        "userlist",
        "fcgi-app",
        "http-errors",
    )

    # Global configuration directives
    global_keywords = (
        "ca-base",
        "chroot",
        "crt-base",
        "daemon",
        "gid",
        "group",
        "log",
        "log-send-hostname",
        "log-tag",
        "maxconn",
        "nbproc",
        "nbthread",
        "pidfile",
        "presetenv",
        "resetenv",
        "setenv",
        "stats",
        "uid",
        "ulimit-n",
        "user",
        "node",
        "description",
        "cpu-map",
        "external-check",
        "insecure-fork-wanted",
        "insecure-setuid-wanted",
        "issuers-chain-path",
        "localpeer",
        "lua-load",
        "lua-prepend-path",
        "master-worker",
        "mworker-max-reloads",
        "spread-checks",
        "ssl-default-bind-ciphers",
        "ssl-default-bind-ciphersuites",
        "ssl-default-bind-curves",
        "ssl-default-bind-options",
        "ssl-default-server-ciphers",
        "ssl-default-server-ciphersuites",
        "ssl-default-server-options",
        "ssl-dh-param-file",
        "ssl-server-verify",
        "tune",
    )

    # Proxy configuration directives
    proxy_keywords = (
        "acl",
        "appsession",
        "backlog",
        "balance",
        "bind",
        "bind-process",
        "block",
        "capture",
        "cookie",
        "default-server",
        "default_backend",
        "description",
        "disabled",
        "dispatch",
        "email-alert",
        "enabled",
        "errorfile",
        "errorloc",
        "errorloc302",
        "errorloc303",
        "force-persist",
        "fullconn",
        "grace",
        "hash-type",
        "http-after-response",
        "http-check",
        "http-request",
        "http-response",
        "http-reuse",
        "http-send-name-header",
        "id",
        "ignore-persist",
        "load-server-state-from-file",
        "log",
        "log-format",
        "log-format-sd",
        "log-tag",
        "max-keep-alive-queue",
        "maxconn",
        "mode",
        "monitor",
        "monitor-net",
        "monitor-uri",
        "option",
        "persist",
        "rate-limit",
        "redirect",
        "reqadd",
        "reqallow",
        "reqdel",
        "reqdeny",
        "reqiallow",
        "reqidel",
        "reqideny",
        "reqipass",
        "reqirep",
        "reqisetbe",
        "reqitarpit",
        "reqpass",
        "reqrep",
        "reqsetbe",
        "reqtarpit",
        "retries",
        "rspadd",
        "rspallow",
        "rspdel",
        "rspdeny",
        "rspiallow",
        "rspidel",
        "rspideny",
        "rspipass",
        "rspirep",
        "rspisetbe",
        "rspitarpit",
        "rsppass",
        "rspirep",
        "rspsetbe",
        "rsptarpit",
        "server",
        "server-state-file-name",
        "server-template",
        "source",
        "srvtimeout",
        "stats",
        "stick",
        "stick-table",
        "tcp-check",
        "tcp-request",
        "tcp-response",
        "timeout",
        "transparent",
        "unique-id-format",
        "unique-id-header",
        "use_backend",
        "use-server",
    )

    # Option keywords
    option_keywords = (
        "abortonclose",
        "accept-invalid-http-request",
        "accept-invalid-http-response",
        "allbackups",
        "checkcache",
        "clitcpka",
        "contstats",
        "dontlog-normal",
        "dontlognull",
        "forceclose",
        "forwardfor",
        "h1-case-adjust-bogus-client",
        "h1-case-adjust-bogus-server",
        "http-buffer-request",
        "http-ignore-probes",
        "http-keep-alive",
        "http-no-delay",
        "http-pretend-keepalive",
        "http-server-close",
        "http-tunnel",
        "http-use-proxy-header",
        "httpchk",
        "httpclose",
        "httplog",
        "httpslog",
        "independent-streams",
        "ldap-check",
        "log-health-checks",
        "log-separate-errors",
        "logasap",
        "mysql-check",
        "nolinger",
        "originalto",
        "persist",
        "pgsql-check",
        "prefer-last-server",
        "redispatch",
        "redis-check",
        "smtpchk",
        "socket-stats",
        "splice-auto",
        "splice-request",
        "splice-response",
        "srvtcpka",
        "ssl-hello-chk",
        "tcp-check",
        "tcp-smart-accept",
        "tcp-smart-connect",
        "tcpka",
        "tcplog",
        "transparent",
    )

    # Timeout types
    timeout_keywords = (
        "check",
        "client",
        "client-fin",
        "connect",
        "http-keep-alive",
        "http-request",
        "queue",
        "server",
        "server-fin",
        "tarpit",
        "tunnel",
    )

    # Load balancing algorithms
    balance_algorithms = (
        "roundrobin",
        "static-rr",
        "leastconn",
        "first",
        "source",
        "uri",
        "url_param",
        "hdr",
        "rdp-cookie",
        "hash",
    )

    # Server check methods
    check_methods = (
        "ssl-hello-chk",
        "smtpchk",
        "ldap-check",
        "mysql-check",
        "pgsql-check",
        "redis-check",
        "httpchk",
        "tcp-check",
    )

    tokens = {
        "root": [
            # Comments
            (r"#.*$", Comment.Single),
            # Whitespace
            (r"\s+", Whitespace),
            # Section headers
            (words(sections, suffix=r"\b"), Keyword.Namespace),
            # Timeout directives with specific handling
            (
                rf"\btimeout\s+({'|'.join(timeout_keywords)})\b",
                bygroups(Name.Builtin),
            ),
            (r"\btimeout\b", Keyword),
            # Option directives
            (
                rf"\boption\s+({'|'.join(option_keywords)})\b",
                bygroups(Name.Builtin),
            ),
            (r"\boption\b", Keyword),
            # Balance directive with algorithms
            (
                rf"\bbalance\s+({'|'.join(balance_algorithms)})\b",
                bygroups(Name.Builtin),
            ),
            (r"\bbalance\b", Keyword),
            # Server directive with parameters
            (
                r"\b(server|server-template)(\s+)([^\s]+)",
                bygroups(Keyword, Whitespace, Name.Variable),
            ),
            # Check methods
            (words(check_methods, suffix=r"\b"), Name.Builtin),
            # Global keywords
            (words(global_keywords, suffix=r"\b"), Keyword),
            # Proxy keywords
            (words(proxy_keywords, suffix=r"\b"), Keyword),
            # ACL conditions and expressions
            (r"\b(if|unless)\s+\{[^}]*\}", Generic.Strong),
            (r"\{[^}]*\}", Generic.Strong),
            # IP addresses (IPv4)
            (r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:/[0-9]{1,2})?\b", Literal.Number),
            # IPv6 addresses (simplified pattern)
            (r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b", Literal.Number),
            (
                r"\b(?:[0-9a-fA-F]{1,4}:)*::[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4})*\b",
                Literal.Number,
            ),
            # Port numbers and ranges
            (r":[0-9]{1,5}(?:-[0-9]{1,5})?\b", Number.Integer),
            # Timeouts with units
            (r"\b[0-9]+(?:us|ms|s|m|h|d)\b", Number.Integer),
            # Percentages and weights
            (r"\b[0-9]+%\b", Number.Integer),
            (
                r"\b(weight|backup|check|inter|fastinter|downinter|rise|fall)\s+([0-9]+)\b",
                bygroups(Name.Attribute, Number.Integer),
            ),
            # HTTP status codes
            (r"\b(?:status\s+)?[1-5][0-9][0-9]\b", Number.Integer),
            # HTTP methods
            (
                r"\b(?:GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH|CONNECT|TRACE)\b",
                Name.Builtin,
            ),
            # Quoted strings
            (r'"[^"]*"', String.Double),
            (r"'[^']*'", String.Single),
            # File paths
            (r"/[^\s]*", String),
            # URLs and URIs
            (r"https?://[^\s]+", String),
            # Boolean values
            (r"\b(?:on|off|yes|no|true|false|enabled|disabled)\b", Name.Constant),
            # Server parameters
            (
                r"\b(?:check|backup|weight|maxconn|maxqueue|slowstart|track|addr|port|"
                r"cookie|redir|rise|fall|inter|fastinter|downinter|observe|"
                r"error-limit|on-error|on-marked-down|on-marked-up|send-proxy|"
                r"send-proxy-v2|ssl|verify|verifyhost|ca-file|crt|crl-file|"
                r"ciphers|ciphersuites|curves|ecdhe|no-sslv3|no-tlsv10|no-tlsv11|"
                r"no-tlsv12|no-tlsv13|force-sslv3|force-tlsv10|force-tlsv11|"
                r"force-tlsv12|force-tlsv13|alpn|npn|sni)\b",
                Name.Attribute,
            ),
            # Configuration values and parameters
            (r"\b[a-zA-Z_][a-zA-Z0-9_-]*\b", Name),
            # Numbers
            (r"\b[0-9]+\b", Number.Integer),
            # Operators and punctuation
            (r"[=<>!]", Operator),
            (r"[{}()[\],;]", Punctuation),
            # Everything else
            (r".", Text),
        ]
    }
