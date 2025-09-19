"""
Integration tests for missing HAProxy Dataplane Structured API section types.

This test file follows Test-Driven Development methodology to ensure that all
missing HAProxy section types are properly supported in the ConfigAPI. These
tests will initially fail with "Unsupported section type" errors and should
be used to guide implementation of the missing section handlers.

Missing section types being tested:
- USERLIST: User authentication lists with groups and users
- CACHE: HTTP cache sections with size and timeout settings
- MAILERS: Email notification sections for alerts
- RESOLVER: DNS resolver configurations with nameservers
- PEER: Peer synchronization sections for clustering
- FCGI_APP: FastCGI application definitions
- HTTP_ERRORS: Custom error page sections
- RING: Log ring buffer sections
- LOG_FORWARD: Log forwarding configurations
- PROGRAM: External program execution sections
"""

import pytest
from haproxy_template_ic.dataplane import DataplaneClient
from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
from haproxy_template_ic.dataplane.types import (
    ConfigChange,
    ConfigChangeType,
    ConfigSectionType,
    DataplaneAPIError,
)
from haproxy_template_ic.credentials import DataplaneAuth
from pydantic import SecretStr

# Import HAProxy model objects for each section type
from haproxy_dataplane_v3.models.userlist import Userlist
from haproxy_dataplane_v3.models.cache import Cache
from haproxy_dataplane_v3.models.mailers_section import MailersSection
from haproxy_dataplane_v3.models.resolver import Resolver
from haproxy_dataplane_v3.models.peer_section import PeerSection
from haproxy_dataplane_v3.models.fcgi_app import FcgiApp
from haproxy_dataplane_v3.models.http_errors_section import HttpErrorsSection
from haproxy_dataplane_v3.models.ring import Ring
from haproxy_dataplane_v3.models.log_forward import LogForward
from haproxy_dataplane_v3.models.program import Program

# Base HAProxy configuration used in all tests
BASE_HAPROXY_CONFIG = """
global
    daemon
    master-worker

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:80
    default_backend servers

backend servers
    balance roundrobin
    server web1 192.168.1.100:8080 check

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
"""


async def setup_base_config(client: DataplaneClient):
    """Deploy base configuration before running section-specific tests."""
    await client.deploy_configuration(BASE_HAPROXY_CONFIG)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_userlist_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for USERLIST sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.USERLIST"
    and should guide implementation of userlist section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create USERLIST section changes
    userlist_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.USERLIST,
            section_name="api_users",
            new_config=Userlist(
                name="api_users",
                # Basic userlist for API authentication
            ),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.USERLIST,
            section_name="admin_users",
            new_config=Userlist(
                name="admin_users",
                # Admin userlist with elevated privileges
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(userlist_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 2  # Should have applied 2 USERLIST changes
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for CACHE sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.CACHE"
    and should guide implementation of cache section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create CACHE section changes
    cache_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.CACHE,
            section_name="web_cache",
            new_config=Cache(
                name="web_cache",
                total_max_size=100,  # 100MB cache
            ),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.CACHE,
            section_name="api_cache",
            new_config=Cache(
                name="api_cache",
                total_max_size=50,  # 50MB cache for API responses
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(cache_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 2  # Should have applied 2 CACHE changes
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mailers_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for MAILERS sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.MAILERS"
    and should guide implementation of mailers section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create MAILERS section changes
    mailers_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.MAILERS,
            section_name="alerts",
            new_config=MailersSection(
                name="alerts",
                timeout=10,  # timeout in seconds (integer)
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(mailers_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 1  # Should have applied 1 MAILERS change
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolver_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for RESOLVER sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.RESOLVER"
    and should guide implementation of resolver section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create RESOLVER section changes
    resolver_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.RESOLVER,
            section_name="local_dns",
            new_config=Resolver(
                name="local_dns",
                parse_resolv_conf=True,
            ),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.RESOLVER,
            section_name="public_dns",
            new_config=Resolver(
                name="public_dns",
                parse_resolv_conf=False,
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(resolver_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 2  # Should have applied 2 RESOLVER changes
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_peer_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for PEER sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.PEER"
    and should guide implementation of peer section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create PEER section changes
    peer_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.PEER,
            section_name="cluster_sync",
            new_config=PeerSection(
                name="cluster_sync",
                # Peer section for cluster synchronization
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(peer_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 1  # Should have applied 1 PEER change
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fcgi_app_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for FCGI_APP sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.FCGI_APP"
    and should guide implementation of fcgi_app section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create FCGI_APP section changes
    fcgi_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FCGI_APP,
            section_name="php_app",
            new_config=FcgiApp(
                name="php_app",
                docroot="/var/www/html",
            ),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FCGI_APP,
            section_name="python_app",
            new_config=FcgiApp(
                name="python_app",
                docroot="/opt/python_app",
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(fcgi_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 2  # Should have applied 2 FCGI_APP changes
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_errors_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for HTTP_ERRORS sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.HTTP_ERRORS"
    and should guide implementation of http_errors section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create HTTP_ERRORS section changes
    http_errors_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.HTTP_ERRORS,
            section_name="custom_errors",
            new_config=HttpErrorsSection(
                name="custom_errors",
                error_files=[],  # Empty error files list
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(http_errors_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 1  # Should have applied 1 HTTP_ERRORS change
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ring_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for RING sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.RING"
    and should guide implementation of ring section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create RING section changes
    ring_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.RING,
            section_name="log_ring",
            new_config=Ring(
                name="log_ring",
                size=32768,  # 32KB ring buffer
            ),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.RING,
            section_name="event_ring",
            new_config=Ring(
                name="event_ring",
                size=65536,  # 64KB ring buffer
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(ring_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 2  # Should have applied 2 RING changes
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_log_forward_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for LOG_FORWARD sections via structured API.

    This test will initially fail with "Unsupported section type: ConfigSectionType.LOG_FORWARD"
    and should guide implementation of log_forward section handlers.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create LOG_FORWARD section changes
    log_forward_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.LOG_FORWARD,
            section_name="syslog_forward",
            new_config=LogForward(
                name="syslog_forward",
                # Log forwarding configuration
            ),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.LOG_FORWARD,
            section_name="audit_forward",
            new_config=LogForward(
                name="audit_forward",
                # Audit log forwarding
            ),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(log_forward_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 2  # Should have applied 2 LOG_FORWARD changes
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_program_section_create_operations(production_dataplane_client_raw):
    """Test CREATE operations for PROGRAM sections via structured API.

    NOTE: PROGRAM sections are deprecated in HAProxy 3.1+ and will be removed in HAProxy 3.3.
    This test validates that our implementation handles the section type but expects validation
    failures due to HAProxy's deprecation of this feature. Users should migrate to external
    process managers like Systemd, Supervisord, or Docker for program management.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create PROGRAM section changes
    program_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.PROGRAM,
            section_name="health_check",
            new_config=Program(
                name="health_check",
                command="/bin/echo health-check",
            ),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.PROGRAM,
            section_name="log_processor",
            new_config=Program(
                name="log_processor",
                command="/bin/echo log-processor",
            ),
        ),
    ]

    # PROGRAM sections are deprecated in HAProxy 3.1+ and often fail validation
    # We expect this to fail due to HAProxy's deprecation of this feature
    with pytest.raises(DataplaneAPIError) as exc_info:
        await client.deploy_structured_configuration(program_changes)

    # Verify that the error is related to configuration validation (expected behavior)
    error_msg = str(exc_info.value)
    assert "validation error" in error_msg.lower() or "commit" in error_msg.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_comprehensive_missing_sections_workflow(production_dataplane_client_raw):
    """Test a comprehensive workflow that creates multiple missing section types.

    This test combines multiple missing section types in a single structured deployment
    to verify that the implementation works correctly for supported sections.
    PROGRAM sections are excluded due to HAProxy 3.1+ deprecation.
    """
    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # Create changes for multiple missing section types
    # NOTE: PROGRAM sections are excluded due to HAProxy 3.1+ deprecation causing validation failures
    mixed_changes = [
        # USERLIST
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.USERLIST,
            section_name="api_users",
            new_config=Userlist(name="api_users"),
        ),
        # CACHE
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.CACHE,
            section_name="web_cache",
            new_config=Cache(name="web_cache", total_max_size=100),
        ),
        # RESOLVER
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.RESOLVER,
            section_name="local_dns",
            new_config=Resolver(name="local_dns", parse_resolv_conf=True),
        ),
        # MAILERS
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.MAILERS,
            section_name="alerts",
            new_config=MailersSection(name="alerts", timeout=10),
        ),
    ]

    # This should now succeed with our implementation
    result = await client.deploy_structured_configuration(mixed_changes)

    # Verify the deployment was successful
    assert hasattr(result, "changes_applied")
    assert result.changes_applied == 4  # Should have applied all 4 changes
    assert hasattr(result, "transaction_used")
    assert result.transaction_used  # Should have used transaction successfully


@pytest.mark.integration
@pytest.mark.asyncio
async def test_section_update_and_delete_operations(production_dataplane_client_raw):
    """Test UPDATE and DELETE operations for missing section types.

    This test validates UPDATE and DELETE functionality for the newly implemented
    section handlers, including the delete+create pattern for sections without
    native replace operations.
    """

    # Setup client
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    client = DataplaneClient(endpoint)

    # Deploy base configuration
    await setup_base_config(client)

    # First, create some sections to update/delete
    create_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.CACHE,
            section_name="test_cache",
            new_config=Cache(name="test_cache", total_max_size=50),
        ),
    ]

    create_result = await client.deploy_structured_configuration(create_changes)
    assert create_result.changes_applied == 1

    # Test UPDATE operations
    update_changes = [
        ConfigChange(
            change_type=ConfigChangeType.UPDATE,
            section_type=ConfigSectionType.CACHE,
            section_name="test_cache",
            new_config=Cache(name="test_cache", total_max_size=100),  # Increased size
        ),
    ]

    update_result = await client.deploy_structured_configuration(update_changes)
    assert update_result.changes_applied == 1

    # Test DELETE operations
    delete_changes = [
        ConfigChange(
            change_type=ConfigChangeType.DELETE,
            section_type=ConfigSectionType.CACHE,
            section_name="test_cache",
        ),
    ]

    delete_result = await client.deploy_structured_configuration(delete_changes)
    assert delete_result.changes_applied == 1
