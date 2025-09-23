"""
Integration tests for HAProxy Dataplane Structured API functionality.

These tests specifically target the structured configuration API operations
that were missing from the basic integration tests. They test ConfigChange
objects, nested element operations, and the exact scenarios that trigger
API parameter errors in production.

This test file was created to catch critical bugs that were missed by
existing integration tests, specifically:
- `asyncio() got an unexpected keyword argument 'index'` in CREATE operations
- `asyncio() got an unexpected keyword argument 'backend/frontend'` in fetch operations
"""

import pytest
from haproxy_template_ic.dataplane import (
    DataplaneClient,
)
from haproxy_template_ic.metrics import MetricsCollector
from haproxy_template_ic.dataplane.endpoint import DataplaneEndpoint
from haproxy_template_ic.dataplane.types import (
    ConfigChange,
    ConfigChangeType,
    ConfigSectionType,
    ConfigElementType,
)
from haproxy_template_ic.credentials import DataplaneAuth
from pydantic import SecretStr

# Import HAProxy API model objects
from haproxy_dataplane_v3.models.acl_lines import ACLLines
from haproxy_dataplane_v3.models.http_request_rule import HTTPRequestRule
from haproxy_dataplane_v3.models.http_request_rule_type import HTTPRequestRuleType
from haproxy_dataplane_v3.models.http_request_rule_redir_type import (
    HTTPRequestRuleRedirType,
)
from haproxy_dataplane_v3.models.http_request_rule_cond import HTTPRequestRuleCond

# Test configurations that contain nested elements
HAPROXY_CONFIG_WITH_NESTED_ELEMENTS = """
global
    daemon
    master-worker
    
defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend test_frontend
    bind *:80
    acl is_api path_beg /api
    acl is_admin path_beg /admin
    acl is_test path_beg /test
    http-request deny if is_admin
    http-request set-header X-API-Request true if is_api
    http-response set-header X-Response-Time %Ts
    default_backend test_backend

backend test_backend
    balance roundrobin
    acl valid_user hdr(Authorization) -m found
    acl internal_ip src 192.168.1.0/24
    http-request deny unless valid_user
    http-request set-header X-Internal-Request true if internal_ip
    http-response del-header Server
    server web1 192.168.1.100:8080 check
    server web2 192.168.1.101:8080 check

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
"""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_structured_configuration_with_nested_elements(
    production_dataplane_client,
):
    """
    Test fetching structured configuration that contains nested elements.

    This test specifically targets the backend/frontend parameter bugs in
    the _fetch_nested_elements function that cause:
    'asyncio() got an unexpected keyword argument backend/frontend'
    """
    client = production_dataplane_client

    # Deploy configuration that contains ACLs and HTTP rules
    await client.deploy_configuration(HAPROXY_CONFIG_WITH_NESTED_ELEMENTS)

    # This should trigger the backend/frontend parameter errors with current implementation
    try:
        structured_config = await client.fetch_structured_configuration()

        # Validate the response structure
        assert isinstance(structured_config, dict)
        assert "backends" in structured_config
        assert "frontends" in structured_config

        # Validate that nested elements were fetched
        if "backend_acls" in structured_config:
            backend_acls = structured_config["backend_acls"]
            assert isinstance(backend_acls, dict)

        if "frontend_acls" in structured_config:
            frontend_acls = structured_config["frontend_acls"]
            assert isinstance(frontend_acls, dict)

    except Exception as e:
        # With current implementation, this should fail with parameter errors
        error_msg = str(e)
        if "got an unexpected keyword argument" in error_msg:
            # This is the bug we're trying to catch and fix
            pytest.fail(f"API parameter error detected: {error_msg}")
        else:
            # Unexpected error - re-raise
            raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_structured_create_acl_operations(production_dataplane_client_raw):
    """
    Test CREATE operations for ACL elements via structured API.

    This test specifically targets the CREATE parameter bugs that cause:
    'asyncio() got an unexpected keyword argument index'
    """
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics)

    # Deploy minimal config with frontend and backend
    base_config = """
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend test_frontend
    bind *:80
    default_backend test_backend

backend test_backend
    balance roundrobin
    server web1 192.168.1.100:8080 check

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
"""
    await client.deploy_configuration(base_config)

    # Create ConfigChange objects to add ACL rules using proper model objects
    # These should trigger the CREATE parameter bugs with current implementation
    acl_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="test_frontend",
            element_type=ConfigElementType.ACL,
            element_index=0,  # This triggers the index parameter bug
            new_config=ACLLines(acl_name="is_api", criterion="path_beg", value="/api"),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="test_backend",
            element_type=ConfigElementType.ACL,
            element_index=0,  # This triggers the index parameter bug
            new_config=ACLLines(
                acl_name="has_auth",
                criterion="hdr(Authorization)",
                value="-m found",
            ),
        ),
    ]

    # This should trigger the CREATE parameter errors with current implementation
    try:
        result = await client.deploy_structured_configuration(acl_changes)

        assert hasattr(result, "changes_applied")
        assert hasattr(result, "changes_applied")
        assert result.changes_applied == 2  # Should have applied 2 ACL changes
        assert hasattr(result, "transaction_used")
        assert result.transaction_used  # Should have used transaction successfully

    except Exception as e:
        # With current implementation, this should fail with parameter errors
        error_msg = str(e)
        if "got an unexpected keyword argument" in error_msg:
            # This is the bug we're trying to catch and fix
            pytest.fail(f"API parameter error detected: {error_msg}")
        else:
            # Unexpected error - re-raise
            raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_structured_create_http_rules_operations(production_dataplane_client_raw):
    """
    Test CREATE operations for HTTP Request Rules via structured API.

    This test targets CREATE operations for another type of index-based element.
    """
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics)

    # Deploy minimal config
    base_config = """
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend test_frontend
    bind *:80
    default_backend test_backend

backend test_backend
    balance roundrobin
    server web1 192.168.1.100:8080 check

frontend status
    bind *:8404
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
"""
    await client.deploy_configuration(base_config)

    # Create ConfigChange objects to add HTTP request rules using proper model objects
    http_rule_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="test_frontend",
            element_type=ConfigElementType.HTTP_REQUEST_RULE,
            element_index=0,  # This triggers the index parameter bug
            new_config=HTTPRequestRule(
                type_=HTTPRequestRuleType.SET_HEADER,
                hdr_name="X-Frontend-Request",
                hdr_format="true",
            ),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.BACKEND,
            section_name="test_backend",
            element_type=ConfigElementType.HTTP_REQUEST_RULE,
            element_index=0,  # This triggers the index parameter bug
            new_config=HTTPRequestRule(
                type_=HTTPRequestRuleType.SET_HEADER,
                hdr_name="X-Backend-Request",
                hdr_format="true",
            ),
        ),
    ]

    # This should trigger the CREATE parameter errors with current implementation
    try:
        result = await client.deploy_structured_configuration(http_rule_changes)

        assert hasattr(result, "changes_applied")
        assert result.version is not None

    except Exception as e:
        # With current implementation, this should fail with parameter errors
        error_msg = str(e)
        if "got an unexpected keyword argument" in error_msg:
            # This is the bug we're trying to catch and fix
            pytest.fail(f"API parameter error detected: {error_msg}")
        else:
            # Unexpected error - re-raise
            raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_structured_update_delete_operations(production_dataplane_client_raw):
    """
    Test UPDATE and DELETE operations for nested elements.

    This test validates that the already-fixed UPDATE/DELETE logic works correctly.
    """
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics)

    # Deploy config that already has elements we can update/delete
    await client.deploy_configuration(HAPROXY_CONFIG_WITH_NESTED_ELEMENTS)

    # Test UPDATE operations (should work with current fixes)
    update_changes = [
        ConfigChange(
            change_type=ConfigChangeType.UPDATE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="test_frontend",
            element_type=ConfigElementType.ACL,
            element_index=2,
            new_config=ACLLines(
                acl_name="is_test", criterion="path_beg", value="/test/v2"
            ),
        )
    ]

    try:
        update_result = await client.deploy_structured_configuration(update_changes)
        assert hasattr(update_result, "changes_applied")

    except Exception:
        # UPDATE should work with current fixes
        raise

    # Test DELETE operations (should work with current fixes)
    delete_changes = [
        ConfigChange(
            change_type=ConfigChangeType.DELETE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="test_frontend",
            element_type=ConfigElementType.ACL,
            element_index=2,
        )
    ]

    try:
        delete_result = await client.deploy_structured_configuration(delete_changes)
        assert hasattr(delete_result, "changes_applied")

    except Exception:
        # DELETE should work with current fixes
        raise


@pytest.mark.integration
@pytest.mark.asyncio
async def test_comprehensive_structured_api_workflow(production_dataplane_client_raw):
    """
    Test a complete workflow that exercises all the problematic code paths.

    This test combines fetch operations (backend/frontend bugs) with
    CREATE operations (index parameter bugs) in a realistic scenario.
    """
    base_url = str(production_dataplane_client_raw.base_url).rstrip("/")
    if not base_url.endswith("/v3"):
        base_url += "/v3"

    auth = DataplaneAuth(username="admin", password=SecretStr("adminpass"))
    endpoint = DataplaneEndpoint(url=base_url, dataplane_auth=auth)
    metrics = MetricsCollector()
    client = DataplaneClient(endpoint, metrics)

    # Start with simple config
    simple_config = """
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend simple_frontend
    bind *:80
    default_backend simple_backend

backend simple_backend
    balance roundrobin
    server web1 192.168.1.100:8080 check

frontend status
    bind *:8404  
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
"""
    await client.deploy_configuration(simple_config)

    # Fetch initial config (tests fetch operations)
    try:
        initial_config = await client.fetch_structured_configuration()
        assert isinstance(initial_config, dict)
    except Exception as e:
        if "got an unexpected keyword argument" in str(e):
            pytest.fail(f"Fetch API parameter error: {e}")
        else:
            raise

    # Add ACLs and HTTP rules (tests CREATE operations)
    create_changes = [
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="simple_frontend",
            element_type=ConfigElementType.ACL,
            element_index=0,
            new_config=ACLLines(acl_name="is_secure", criterion="ssl_fc"),
        ),
        ConfigChange(
            change_type=ConfigChangeType.CREATE,
            section_type=ConfigSectionType.FRONTEND,
            section_name="simple_frontend",
            element_type=ConfigElementType.HTTP_REQUEST_RULE,
            element_index=0,  # Start HTTP rules at index 0 (separate from ACLs)
            new_config=HTTPRequestRule(
                type_=HTTPRequestRuleType.REDIRECT,
                redir_type=HTTPRequestRuleRedirType.SCHEME,
                redir_value="https",
                cond=HTTPRequestRuleCond.UNLESS,
                cond_test="is_secure",
            ),
        ),
    ]

    try:
        create_result = await client.deploy_structured_configuration(create_changes)
        assert hasattr(create_result, "changes_applied")
    except Exception as e:
        if "got an unexpected keyword argument" in str(e):
            pytest.fail(f"CREATE API parameter error: {e}")
        else:
            raise

    # Fetch updated config (tests fetch with nested elements)
    try:
        final_config = await client.fetch_structured_configuration()
        assert isinstance(final_config, dict)

        # Verify that nested elements were created and fetched
        if "frontend_acls" in final_config:
            frontend_acls = final_config["frontend_acls"]
            if "simple_frontend" in frontend_acls:
                assert len(frontend_acls["simple_frontend"]) > 0

        if "frontend_http_request_rules" in final_config:
            http_rules = final_config["frontend_http_request_rules"]
            if "simple_frontend" in http_rules:
                assert len(http_rules["simple_frontend"]) > 0

    except Exception as e:
        if "got an unexpected keyword argument" in str(e):
            pytest.fail(f"Final fetch API parameter error: {e}")
        else:
            raise
