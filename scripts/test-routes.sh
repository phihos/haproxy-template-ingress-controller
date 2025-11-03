#!/usr/bin/env bash

set -euo pipefail

# Test script for HAProxy Template Ingress Controller
# Tests all Ingresses and HTTPRoutes in the dev environment

# Ensure we operate from the repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
CLUSTER_NAME="haproxy-template-ic-dev"
ECHO_NAMESPACE="echo"
NODEPORT="30080"
BASE_URL="http://localhost:${NODEPORT}"

# Options
VERBOSE=false
TEST_FILTER=""
INGRESS_ONLY=false
HTTPROUTE_ONLY=false

# Colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

# Test statistics
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging functions
log() {
    local level msg
    level="$1"; shift
    msg="$*"
    echo -e "${BLUE}[$(date +'%Y-%m-%dT%H:%M:%S%z')]${NC} ${level}: ${msg}"
}

ok() {
    echo -e "${GREEN}✔${NC} $*"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $*"
}

err() {
    echo -e "${RED}✖${NC} $*"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

debug() {
    [[ "$VERBOSE" == "true" ]] && echo -e "${BLUE}[DEBUG]${NC} $*" || true
}

print_section() {
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Test all Ingresses and HTTPRoutes in the dev environment.

OPTIONS:
    --test NAME         Test only a specific route (ingress or httproute name)
    --ingress-only      Test only Ingress resources
    --httproute-only    Test only HTTPRoute resources
    --verbose           Enable debug output
    --help, -h          Show this help

EXAMPLES:
    $0                          # Test all routes
    $0 --test echo-basic        # Test only echo-basic HTTPRoute
    $0 --test echo-server-auth  # Test only auth ingress
    $0 --ingress-only           # Test only Ingress resources
    $0 --httproute-only         # Test only HTTPRoute resources
    $0 --verbose                # Run with debug output

EXIT CODES:
    0   All tests passed
    1   One or more tests failed

EOF
}

# Test assertion helpers
assert_response_ok() {
    local description="$1"
    local host="$2"
    local path="${3:-/}"
    local expected_backend="${4:-}"
    shift 4
    local extra_args=("$@")

    debug "Testing: $description"
    debug "  Host: $host, Path: $path"
    debug "  Extra args: ${extra_args[*]}"

    local response
    if ! response=$(curl -s --max-time 5 -H "Host: $host" "${extra_args[@]}" "${BASE_URL}${path}" 2>&1); then
        err "$description - Connection failed"
        return 1
    fi

    debug "  Response: ${response:0:200}..."

    # Check for expected backend if specified
    if [[ -n "$expected_backend" ]]; then
        if echo "$response" | grep -q "\"ENVIRONMENT\":\"$expected_backend\""; then
            ok "$description - Routed to $expected_backend"
        elif echo "$response" | grep -q "\"ENVIRONMENT\""; then
            local actual_backend=$(echo "$response" | grep -o '"ENVIRONMENT":"[^"]*"' | cut -d'"' -f4)
            err "$description - Expected backend '$expected_backend', got '$actual_backend'"
            return 1
        else
            ok "$description - Routed to default backend"
        fi
    else
        # Just check for successful response
        if echo "$response" | grep -q "\"http\":"; then
            ok "$description - Response OK"
        else
            err "$description - Invalid response"
            echo "  Received: ${response:0:500}"
            return 1
        fi
    fi
}

assert_weighted_distribution() {
    local description="$1"
    local host="$2"
    local expected_default_pct="$3"
    local expected_v2_pct="$4"
    local num_requests="${5:-20}"
    local tolerance="${6:-10}"

    debug "Testing weighted distribution: $description"
    debug "  Host: $host, Requests: $num_requests"
    debug "  Expected: ${expected_default_pct}% default, ${expected_v2_pct}% v2"

    local count_default=0
    local count_v2=0

    for i in $(seq 1 "$num_requests"); do
        local response
        response=$(curl -s --max-time 5 -H "Host: $host" "${BASE_URL}/" 2>&1)

        if echo "$response" | grep -q '"ENVIRONMENT":"v2"'; then
            count_v2=$((count_v2 + 1))
        else
            count_default=$((count_default + 1))
        fi
    done

    local actual_default_pct=$(( (count_default * 100) / num_requests ))
    local actual_v2_pct=$(( (count_v2 * 100) / num_requests ))

    debug "  Actual: ${actual_default_pct}% default ($count_default/$num_requests), ${actual_v2_pct}% v2 ($count_v2/$num_requests)"

    # Check if within tolerance
    local default_diff=$(( actual_default_pct - expected_default_pct ))
    default_diff=${default_diff#-}  # absolute value
    local v2_diff=$(( actual_v2_pct - expected_v2_pct ))
    v2_diff=${v2_diff#-}

    if [[ $default_diff -le $tolerance ]] && [[ $v2_diff -le $tolerance ]]; then
        ok "$description - Distribution OK (${actual_default_pct}% default, ${actual_v2_pct}% v2)"
    else
        err "$description - Distribution out of range (${actual_default_pct}% default, ${actual_v2_pct}% v2, expected ${expected_default_pct}%/${expected_v2_pct}% ±${tolerance}%)"
        return 1
    fi
}

assert_auth_required() {
    local description="$1"
    local host="$2"

    debug "Testing auth requirement: $description"

    local response_code
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -H "Host: $host" "${BASE_URL}/" 2>&1)

    if [[ "$response_code" == "401" ]]; then
        ok "$description - Auth required (401)"
    else
        err "$description - Expected 401, got $response_code"
        return 1
    fi
}

assert_auth_success() {
    local description="$1"
    local host="$2"
    local username="$3"
    local password="$4"

    debug "Testing auth success: $description"

    local response
    if ! response=$(curl -s --max-time 5 -u "$username:$password" -H "Host: $host" "${BASE_URL}/" 2>&1); then
        err "$description - Connection failed"
        return 1
    fi

    if echo "$response" | grep -q "\"http\":"; then
        ok "$description - Auth successful with $username:$password"
    else
        err "$description - Auth failed"
        echo "  Received: ${response:0:500}"
        return 1
    fi
}

# Verify cluster is accessible
verify_cluster() {
    if ! kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
        echo -e "${RED}Error:${NC} Kind cluster '$CLUSTER_NAME' not found"
        echo "Start the dev environment with: ./scripts/start-dev-env.sh"
        exit 1
    fi

    if ! kubectl --context "kind-$CLUSTER_NAME" cluster-info &>/dev/null; then
        echo -e "${RED}Error:${NC} Cannot access cluster 'kind-$CLUSTER_NAME'"
        exit 1
    fi

    debug "Cluster verified: kind-$CLUSTER_NAME"
}

# Wait for services to be ready and accepting connections
wait_for_services_ready() {
    log INFO "Waiting for services to be ready..."

    local max_attempts=10
    local delay=2
    local attempt=1
    local ready=false

    # Test basic ingress connectivity (echo.localdev.me)
    while [[ $attempt -le $max_attempts ]]; do
        debug "Readiness check attempt $attempt/$max_attempts..."

        local response
        if response=$(curl -s --max-time 5 -H "Host: echo.localdev.me" "${BASE_URL}/" 2>&1); then
            # Check that response contains valid JSON with expected structure
            if echo "$response" | grep -q "\"http\":"; then
                debug "Services responding with valid JSON"
                ready=true
                break
            else
                debug "Connection succeeded but response invalid or empty"
            fi
        else
            debug "Connection failed"
        fi

        if [[ $attempt -lt $max_attempts ]]; then
            debug "Services not ready yet, waiting ${delay}s before retry..."
            sleep "$delay"
        fi

        attempt=$((attempt + 1))
    done

    if [[ "$ready" == "true" ]]; then
        ok "Services are ready and accepting connections"
    else
        echo
        err "Services did not become ready after $max_attempts attempts (${max_attempts}x${delay}s)"
        echo
        echo "This typically means:"
        echo "  - HAProxy pods are not running or not ready"
        echo "  - Echo service pods are not ready"
        echo "  - HAProxy configuration has not synced yet"
        echo "  - Endpoints have not been populated"
        echo
        echo "Troubleshooting steps:"
        echo "  1. Check HAProxy pods: kubectl -n haproxy-template-ic get pods -l app=haproxy"
        echo "  2. Check echo pods: kubectl -n echo get pods"
        echo "  3. Check HAProxy logs: kubectl -n haproxy-template-ic logs deploy/haproxy-production -c haproxy"
        echo "  4. Check controller logs: ./scripts/start-dev-env.sh logs"
        echo "  5. Check endpoints: kubectl -n echo get endpoints"
        echo "  6. Wait longer and try again, or restart: ./scripts/start-dev-env.sh restart"
        echo
        exit 1
    fi
}

should_test() {
    local resource_name="$1"

    if [[ -n "$TEST_FILTER" ]]; then
        [[ "$resource_name" == "$TEST_FILTER" ]]
    else
        true
    fi
}

#═══════════════════════════════════════════════════════════════════════════
# INGRESS TESTS
#═══════════════════════════════════════════════════════════════════════════

test_ingress_basic() {
    if ! should_test "echo-server"; then
        return 0
    fi

    print_section "Testing Ingress: echo-server (echo.localdev.me)"

    assert_response_ok \
        "Basic ingress routing" \
        "echo.localdev.me" \
        "/" \
        ""
}

test_ingress_auth() {
    if ! should_test "echo-server-auth"; then
        return 0
    fi

    print_section "Testing Ingress: echo-server-auth (echo-auth.localdev.me)"

    assert_auth_required \
        "Auth required without credentials" \
        "echo-auth.localdev.me"

    assert_auth_success \
        "Auth with admin:admin" \
        "echo-auth.localdev.me" \
        "admin" \
        "admin"

    assert_auth_success \
        "Auth with user:password" \
        "echo-auth.localdev.me" \
        "user" \
        "password"
}

#═══════════════════════════════════════════════════════════════════════════
# HTTPROUTE TESTS
#═══════════════════════════════════════════════════════════════════════════

test_httproute_basic() {
    if ! should_test "echo-basic"; then
        return 0
    fi

    print_section "Testing HTTPRoute: echo-basic"

    assert_response_ok \
        "Basic PathPrefix routing" \
        "echo-gateway.localdev.me" \
        "/" \
        ""
}

test_httproute_paths() {
    if ! should_test "echo-paths"; then
        return 0
    fi

    print_section "Testing HTTPRoute: echo-paths"

    assert_response_ok \
        "Exact path match /exact" \
        "echo-paths.localdev.me" \
        "/exact" \
        ""

    assert_response_ok \
        "Prefix path match /api/test" \
        "echo-paths.localdev.me" \
        "/api/test" \
        ""

    assert_response_ok \
        "Root path /" \
        "echo-paths.localdev.me" \
        "/" \
        ""
}

test_httproute_methods() {
    if ! should_test "echo-methods"; then
        return 0
    fi

    print_section "Testing HTTPRoute: echo-methods"

    assert_response_ok \
        "GET /api routes to v2" \
        "echo-methods.localdev.me" \
        "/api" \
        "v2" \
        -X GET

    assert_response_ok \
        "POST /api routes to default" \
        "echo-methods.localdev.me" \
        "/api" \
        "" \
        -X POST

    assert_response_ok \
        "Catch-all /" \
        "echo-methods.localdev.me" \
        "/" \
        "" \
        -X GET
}

test_httproute_headers() {
    if ! should_test "echo-headers"; then
        return 0
    fi

    print_section "Testing HTTPRoute: echo-headers"

    assert_response_ok \
        "Exact header X-Api-Version: v2" \
        "echo-headers.localdev.me" \
        "/api" \
        "v2" \
        -H "X-Api-Version: v2"

    assert_response_ok \
        "Regex header X-User-Agent: mobile-app" \
        "echo-headers.localdev.me" \
        "/api" \
        "v2" \
        -H "X-User-Agent: mobile-app"

    assert_response_ok \
        "No headers - catch-all" \
        "echo-headers.localdev.me" \
        "/" \
        ""
}

test_httproute_query() {
    if ! should_test "echo-query"; then
        return 0
    fi

    print_section "Testing HTTPRoute: echo-query"

    assert_response_ok \
        "Query param version=beta" \
        "echo-query.localdev.me" \
        "/api?version=beta" \
        "v2"

    assert_response_ok \
        "Query param debug=true" \
        "echo-query.localdev.me" \
        "/api?debug=true" \
        "v2"

    assert_response_ok \
        "Query param debug=1" \
        "echo-query.localdev.me" \
        "/api?debug=1" \
        "v2"

    assert_response_ok \
        "No query params - catch-all" \
        "echo-query.localdev.me" \
        "/" \
        ""
}

test_httproute_split() {
    if ! should_test "echo-split"; then
        return 0
    fi

    print_section "Testing HTTPRoute: echo-split (weighted routing)"

    # Weighted routing uses HAProxy's rand() for load balancing
    # With larger sample sizes, distribution converges to configured weights
    # Note: Individual test runs may still show variance due to randomness
    assert_weighted_distribution \
        "70/30 traffic split" \
        "echo-split.localdev.me" \
        70 \
        30 \
        100 \
        12
}

test_httproute_precedence() {
    if ! should_test "echo-precedence"; then
        return 0
    fi

    print_section "Testing HTTPRoute: echo-precedence"

    assert_response_ok \
        "Most specific (GET + 2 headers + query)" \
        "echo-precedence.localdev.me" \
        "/?debug=true" \
        "v2" \
        -X GET \
        -H "X-Version: v2" \
        -H "X-Environment: prod"

    assert_response_ok \
        "Specific (GET + header)" \
        "echo-precedence.localdev.me" \
        "/" \
        "" \
        -X GET \
        -H "X-Version: v1"

    assert_response_ok \
        "Medium (GET only)" \
        "echo-precedence.localdev.me" \
        "/" \
        "v2" \
        -X GET

    assert_response_ok \
        "Least specific (catch-all)" \
        "echo-precedence.localdev.me" \
        "/" \
        "" \
        -X POST
}

test_httproute_combined() {
    if ! should_test "echo-combined"; then
        return 0
    fi

    print_section "Testing HTTPRoute: echo-combined"

    assert_response_ok \
        "All matchers (POST + /api + header + query)" \
        "echo-combined.localdev.me" \
        "/api?token=secret123" \
        "v2" \
        -X POST \
        -H "Content-Type: application/json"

    assert_response_ok \
        "Wrong token pattern - catch-all" \
        "echo-combined.localdev.me" \
        "/other?token=wrongtoken" \
        "" \
        -X POST \
        -H "Content-Type: application/json"

    assert_response_ok \
        "Wrong content-type - catch-all" \
        "echo-combined.localdev.me" \
        "/other?token=secret123" \
        "" \
        -X POST \
        -H "Content-Type: text/plain"

    assert_response_ok \
        "Wrong method - catch-all" \
        "echo-combined.localdev.me" \
        "/other" \
        "" \
        -X GET
}

#═══════════════════════════════════════════════════════════════════════════
# MAIN
#═══════════════════════════════════════════════════════════════════════════

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --test)
                TEST_FILTER="$2"
                shift 2
                ;;
            --ingress-only)
                INGRESS_ONLY=true
                shift
                ;;
            --httproute-only)
                HTTPROUTE_ONLY=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

main() {
    parse_args "$@"

    echo
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo " HAProxy Template Ingress Controller - Route Tests"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo

    verify_cluster
    wait_for_services_ready

    # Run Ingress tests
    if [[ "$HTTPROUTE_ONLY" != "true" ]]; then
        test_ingress_basic
        test_ingress_auth
    fi

    # Run HTTPRoute tests
    if [[ "$INGRESS_ONLY" != "true" ]]; then
        test_httproute_basic
        test_httproute_paths
        test_httproute_methods
        test_httproute_headers
        test_httproute_query
        test_httproute_split
        test_httproute_precedence
        test_httproute_combined
    fi

    # Print summary
    print_section "Test Summary"
    echo "Total tests:  $TOTAL_TESTS"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "Failed:       ${GREEN}$FAILED_TESTS${NC}"
    else
        echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
    fi
    echo

    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}✔ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}✖ $FAILED_TESTS test(s) failed${NC}"
        exit 1
    fi
}

main "$@"
