#!/usr/bin/env bash

set -euo pipefail

# Ensure we operate from the repo root regardless of where the script is invoked
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ASSETS_DIR="${SCRIPT_DIR}/dev-env-assets"

# Default configuration
CLUSTER_NAME="haproxy-template-ic-dev"
CTRL_NAMESPACE="haproxy-template-ic"
ECHO_NAMESPACE="echo"
ECHO_APP_NAME="echo-server"
ECHO_IMAGE="ealen/echo-server:latest"
LOCAL_IMAGE="haproxy-template-ic-go:dev"
HELM_RELEASE_NAME="haproxy-template-ic"
TIMEOUT="180"
SKIP_BUILD=false
SKIP_ECHO=false
FORCE_REBUILD=false
VERBOSE=false

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

log() {
	local level msg
	level="$1"; shift
	msg="$*"
	echo -e "${BLUE}[$(date +'%Y-%m-%dT%H:%M:%S%z')]${NC} ${level}: ${msg}"
}

ok() { echo -e "${GREEN}✔${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err() { echo -e "${RED}✖${NC} $*"; }
debug() { [[ "$VERBOSE" == "true" ]] && echo -e "${BLUE}[DEBUG]${NC} $*" || true; }

print_section() {
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

show_spinner() {
    local pid=$1
    local message="$2"
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0

    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i+1) %10 ))
        printf "\r%s%s%s %s" "$BLUE" "${spin:$i:1}" "$NC" "$message"
        sleep 0.1
    done

    printf "\r"  # Clear the spinner line
}

run_with_spinner() {
    local message="$1"
    shift
    local command=("$@")

    if [[ "$VERBOSE" == "true" ]]; then
        log INFO "$message"
        "${command[@]}"
    else
        "${command[@]}" &
        local pid=$!
        show_spinner $pid "$message"
        wait $pid
        local exit_code=$?

        if [[ $exit_code -eq 0 ]]; then
            ok "$message"
        else
            err "$message (exit code: $exit_code)"
        fi

        return $exit_code
    fi
}

show_usage() {
    cat <<EOF
Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
    up          Start development environment (default)
    down        Delete the kind cluster
    logs        Follow controller logs
    exec        Execute shell in controller pod
    restart     Rebuild image and restart controller (use --skip-build to skip)
    status      Show deployment status
    clean       Clean up and reset environment
    test        Test ingress controller functionality
    port-forward Setup port forwarding for HAProxy services

OPTIONS:
    --cluster-name NAME     Custom cluster name (default: haproxy-template-ic-dev)
    --namespace NAME        Custom controller namespace (default: haproxy-template-ic)
    --image-tag TAG         Custom image tag (default: dev)
    --timeout SECONDS       Deployment timeout (default: 180)
    --skip-build            Use existing image if available
    --skip-echo             Don't deploy echo server
    --force-rebuild         Force rebuild without cache
    --verbose               Enable debug output
    --help, -h              Show this help

EXAMPLES:
    $0                      # Start dev environment with defaults
    $0 up --skip-build      # Start without rebuilding image
    $0 restart              # Rebuild image and restart controller
    $0 restart --skip-build # Restart controller without rebuilding
    $0 test                 # Test ingress controller functionality
    $0 logs                 # Follow controller logs
    $0 port-forward         # Setup port forwarding for testing
    $0 down                 # Delete cluster
    $0 restart --verbose    # Restart with debug output

EOF
}

parse_args() {
    COMMAND=""

    # Parse command if provided
    if [[ $# -gt 0 ]] && [[ "$1" != --* ]]; then
        COMMAND="$1"
        shift
    fi

    # Default to 'up' if no command specified
    [[ -z "$COMMAND" ]] && COMMAND="up"

    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --cluster-name)
                CLUSTER_NAME="$2"
                shift 2
                ;;
            --namespace)
                CTRL_NAMESPACE="$2"
                shift 2
                ;;
            --image-tag)
                LOCAL_IMAGE="haproxy-template-ic-go:$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-echo)
                SKIP_ECHO=true
                shift
                ;;
            --force-rebuild)
                FORCE_REBUILD=true
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
                err "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    debug "Command: $COMMAND"
    debug "Cluster: $CLUSTER_NAME"
    debug "Namespace: $CTRL_NAMESPACE"
    debug "Image: $LOCAL_IMAGE"
    debug "Timeout: ${TIMEOUT}s"
}

require_cmd() {
	if ! command -v "$1" >/dev/null 2>&1; then
		err "Required command '$1' not found in PATH."
		troubleshooting "missing-$1"
		exit 1
	fi
}

cleanup_on_exit() {
    local exit_code=$?
    debug "Cleanup function called with exit code: $exit_code"

    if [[ $exit_code -ne 0 ]]; then
        warn "Script exited with error code $exit_code"
        warn "Run with --verbose for more detailed output"

        # Offer helpful next steps
        if kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
            warn "Cluster '$CLUSTER_NAME' exists. You can:"
            echo "  - Check status: $0 status"
            echo "  - Clean up: $0 down"
            echo "  - Retry: $0 up"
        fi
    fi

    # Always try to return to original directory
    popd >/dev/null 2>&1 || true
}

cleanup_failed_deployment() {
    warn "Cleaning up failed deployment..."

    # Delete any failed pods to allow clean retry
    kubectl -n "$CTRL_NAMESPACE" delete pods --field-selector=status.phase=Failed 2>/dev/null || true

    # Rollback Helm release if it exists
    if helm list -n "$CTRL_NAMESPACE" | grep -q "$HELM_RELEASE_NAME"; then
        helm rollback "$HELM_RELEASE_NAME" -n "$CTRL_NAMESPACE" 2>/dev/null || true
    fi

    debug "Failed deployment cleanup completed"
}

retry_with_backoff() {
    local max_attempts="$1"
    local delay="$2"
    local command=("${@:3}")
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        debug "Attempt $attempt/$max_attempts: ${command[*]}"

        if "${command[@]}"; then
            debug "Command succeeded on attempt $attempt"
            return 0
        fi

        if [[ $attempt -lt $max_attempts ]]; then
            warn "Command failed (attempt $attempt/$max_attempts), retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * 2))  # Exponential backoff
        fi

        ((attempt++)) || true
    done

    err "Command failed after $max_attempts attempts: ${command[*]}"
    return 1
}

troubleshooting() {
	case "$1" in
		missing-kind)
			warn "Install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
			;;
		missing-kubectl)
			warn "Install kubectl: https://kubernetes.io/docs/tasks/tools/"
			;;
		missing-docker)
			warn "Install Docker: https://docs.docker.com/get-docker/ and ensure your user can run it (linux: add to docker group)."
			;;
		missing-helm)
			warn "Install Helm: https://helm.sh/docs/intro/install/"
			;;
		rollout-timeout)
			warn "Rollout timed out. Inspect events and logs:"
			echo "  kubectl -n ${CTRL_NAMESPACE} get events --sort-by=.lastTimestamp | tail -n 50"
			echo "  kubectl -n ${CTRL_NAMESPACE} describe deploy/haproxy-production"
			echo "  kubectl -n ${CTRL_NAMESPACE} get pods -o wide"
			echo "  kubectl -n ${CTRL_NAMESPACE} logs deploy/${HELM_RELEASE_NAME} --previous || true"
			;;
		*) ;;
	 esac
}

ensure_cluster() {
	if ! kind get clusters | grep -qx "${CLUSTER_NAME}"; then
		log INFO "Creating kind cluster '${CLUSTER_NAME}'..."
		kind create cluster --name "${CLUSTER_NAME}" --config "${ASSETS_DIR}/kind-config.yaml"
		ok "Cluster created with admission controllers enabled."
	else
		ok "Using existing cluster '${CLUSTER_NAME}'."
		# Export kubeconfig for existing cluster to ensure context is up-to-date
		debug "Exporting kubeconfig for existing cluster..."
		kind export kubeconfig --name "${CLUSTER_NAME}" >/dev/null 2>&1
	fi

	local ctx="kind-${CLUSTER_NAME}"
	if ! kubectl config get-contexts -o name | grep -qx "$ctx"; then
		err "kubectl context '$ctx' not found."
		err "Available contexts:"
		kubectl config get-contexts -o name
		exit 1
	fi
	kubectl config use-context "$ctx" >/dev/null
	ok "Context configured."
}

build_and_load_local_image() {
    if [[ "$SKIP_BUILD" == "true" ]] && docker image inspect "${LOCAL_IMAGE}" >/dev/null 2>&1; then
        ok "Using existing image '${LOCAL_IMAGE}'"
        return 0
    fi

    local build_args=("-t" "${LOCAL_IMAGE}")

    if [[ "$FORCE_REBUILD" == "true" ]]; then
        build_args+=("--no-cache")
    fi

    build_args+=("${REPO_ROOT}")

    local docker_path
    docker_path="$(command -v docker)"

    run_with_spinner "Building controller image '${LOCAL_IMAGE}'" \
        "${docker_path}" build "${build_args[@]}"

    run_with_spinner "Loading image into kind cluster '${CLUSTER_NAME}'" \
        kind load docker-image "${LOCAL_IMAGE}" --name "${CLUSTER_NAME}"
}

deploy_controller() {
    build_and_load_local_image || {
        err "Failed to build or load image"
        return 1
    }

    print_section "🚀 Deploying Controller via Helm"

    # Create namespace if it doesn't exist
    kubectl create namespace "${CTRL_NAMESPACE}" 2>/dev/null || true

    log INFO "Deploying haproxy-template-ic to namespace '${CTRL_NAMESPACE}' using Helm..."

    # Use helm upgrade --install for idempotent deployment
    # The --wait flag ensures all resources are ready before returning
    if helm upgrade --install "${HELM_RELEASE_NAME}" \
        "${REPO_ROOT}/charts/haproxy-template-ic-go" \
        --namespace "${CTRL_NAMESPACE}" \
        --values "${ASSETS_DIR}/dev-values.yaml" \
        --wait \
        --timeout "${TIMEOUT}s" 2>&1 | tee /tmp/helm-output.log; then
        ok "Controller deployed and ready."
    else
        err "Helm deployment failed."
        cat /tmp/helm-output.log
        cleanup_failed_deployment
        return 1
    fi
}

deploy_haproxy() {
    print_section "🔧 Deploying HAProxy Production Instances"

    log INFO "Deploying HAProxy production deployment with Dataplane API sidecars..."
    retry_with_backoff 3 2 kubectl apply -f "${ASSETS_DIR}/haproxy-production.yaml" || {
        err "Failed to deploy HAProxy production instances"
        return 1
    }

    log INFO "Waiting for HAProxy production deployment to become ready..."
    if ! kubectl -n "${CTRL_NAMESPACE}" rollout status deployment/haproxy-production --timeout="${TIMEOUT}s"; then
        warn "HAProxy production deployment rollout did not complete in ${TIMEOUT}s."
        echo "  - Check HAProxy deployment status: kubectl -n ${CTRL_NAMESPACE} describe deploy/haproxy-production"
        echo "  - Check HAProxy pod logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-production -c haproxy"
        echo "  - Check dataplane logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-production -c dataplane"
        return 1
    fi
    ok "HAProxy production deployment is ready."
}

deploy_ingressclass() {
    log INFO "Deploying IngressClass resource..."
    kubectl apply -f "${ASSETS_DIR}/ingressclass.yaml" >/dev/null
    ok "IngressClass 'haproxy-template-ic' deployed."
}

deploy_echo_server() {
	log INFO "Creating demo Echo Server in namespace '${ECHO_NAMESPACE}'..."
	kubectl get ns "${ECHO_NAMESPACE}" >/dev/null 2>&1 || kubectl create ns "${ECHO_NAMESPACE}" >/dev/null
	kubectl -n "${ECHO_NAMESPACE}" apply -f - >/dev/null <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${ECHO_APP_NAME}
  labels:
    app: ${ECHO_APP_NAME}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${ECHO_APP_NAME}
  template:
    metadata:
      labels:
        app: ${ECHO_APP_NAME}
    spec:
      containers:
        - name: server
          image: ${ECHO_IMAGE}
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: ${ECHO_APP_NAME}
  labels:
    app: ${ECHO_APP_NAME}
spec:
  selector:
    app: ${ECHO_APP_NAME}
  ports:
    - name: http
      port: 80
      targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${ECHO_APP_NAME}
spec:
  ingressClassName: haproxy-template-ic
  rules:
    - host: echo.localdev.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ${ECHO_APP_NAME}
                port:
                  number: 80
EOF

	log INFO "Waiting for Echo Server deployment to become ready..."
	kubectl -n "${ECHO_NAMESPACE}" rollout status deployment/${ECHO_APP_NAME} --timeout=120s >/dev/null
	ok "Echo Server is ready."

	ok "Echo Server deployed with Ingress resource."
	echo "The Ingress for 'echo.localdev.me' is now being handled by haproxy-template-ic."
	echo "Traffic will be routed through the production HAProxy instances on port 30080."
	echo "Test with: curl -H 'Host: echo.localdev.me' http://localhost:30080"
}

# Development convenience functions
dev_logs() {
    # Use label selector to find controller deployment
    kubectl -n "$CTRL_NAMESPACE" logs -f -l "app.kubernetes.io/instance=${HELM_RELEASE_NAME},app.kubernetes.io/name=haproxy-template-ic-go"
}

dev_exec() {
    # Get the deployment name using label selector
    local deploy_name
    deploy_name=$(kubectl -n "$CTRL_NAMESPACE" get deployment -l "app.kubernetes.io/instance=${HELM_RELEASE_NAME},app.kubernetes.io/name=haproxy-template-ic-go" -o jsonpath='{.items[0].metadata.name}')
    kubectl -n "$CTRL_NAMESPACE" exec -it deploy/"$deploy_name" -- sh
}

dev_restart() {
    print_section "🔄 Restarting Controller"

    # Build and load new image unless skipped
    if [[ "$SKIP_BUILD" != "true" ]]; then
        log INFO "Rebuilding and loading controller image..."
        build_and_load_local_image || {
            err "Failed to rebuild image"
            return 1
        }
    else
        log INFO "Skipping image rebuild (--skip-build flag set)"
    fi

    # Upgrade Helm release to pick up any changes
    log INFO "Upgrading Helm release..."
    helm upgrade "${HELM_RELEASE_NAME}" \
        "${REPO_ROOT}/charts/haproxy-template-ic-go" \
        --namespace "${CTRL_NAMESPACE}" \
        --values "${ASSETS_DIR}/dev-values.yaml" \
        --wait \
        --timeout "${TIMEOUT}s" || {
        warn "Helm upgrade failed, rolling back..."
        helm rollback "${HELM_RELEASE_NAME}" -n "${CTRL_NAMESPACE}"
        return 1
    }

    ok "Controller restarted successfully"
}

dev_status() {
    print_section "📊 Development Environment Status"

    echo "Cluster:"
    if kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
        ok "Cluster '$CLUSTER_NAME' exists"
        kubectl cluster-info --context "kind-$CLUSTER_NAME" | head -n 3
    else
        err "Cluster '$CLUSTER_NAME' not found"
        return 1
    fi

    echo
    echo "Helm Releases:"
    helm list -n "$CTRL_NAMESPACE" 2>/dev/null || {
        warn "Namespace '$CTRL_NAMESPACE' not found or no releases"
    }

    echo
    echo "Deployments:"
    kubectl -n "$CTRL_NAMESPACE" get deploy -o wide 2>/dev/null || {
        warn "Namespace '$CTRL_NAMESPACE' not found or no deployments"
    }

    echo
    echo "Pods:"
    kubectl -n "$CTRL_NAMESPACE" get pods -o wide 2>/dev/null || {
        warn "No pods found in namespace '$CTRL_NAMESPACE'"
    }

    echo
    echo "Services:"
    kubectl -n "$CTRL_NAMESPACE" get svc 2>/dev/null || {
        warn "No services found in namespace '$CTRL_NAMESPACE'"
    }
}

dev_clean() {
    print_section "🧹 Cleaning Development Environment"

    if kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
        log INFO "Deleting kind cluster '$CLUSTER_NAME'..."
        kind delete cluster --name "$CLUSTER_NAME"
        ok "Cluster deleted"
    else
        warn "Cluster '$CLUSTER_NAME' not found"
    fi

    # Clean up local images if requested
    if [[ "${1:-}" == "--images" ]]; then
        log INFO "Removing local images..."
        docker rmi "$LOCAL_IMAGE" 2>/dev/null || true
        docker image prune -f >/dev/null 2>&1 || true
        ok "Local images cleaned"
    fi
}

dev_down() {
    dev_clean "$@"
}

test_ingress() {
    print_section "🧪 Testing Ingress Controller"

    # Check if the echo service is available
    if ! kubectl -n "$ECHO_NAMESPACE" get deployment "$ECHO_APP_NAME" >/dev/null 2>&1; then
        warn "Echo service not found. Deploy it first with: $0 up"
        return 1
    fi

    # Test via NodePort (requires kind cluster)
    if kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
        log INFO "Testing via NodePort (localhost:30080)..."
        echo "Trying to connect to echo service through HAProxy ingress controller..."

        # Wait a moment for the service to be ready
        sleep 2

        if curl -s --max-time 10 -H "Host: echo.localdev.me" http://localhost:30080 >/dev/null 2>&1; then
            ok "Ingress controller is working! Echo service is accessible"
            echo
            echo "Test the ingress controller with:"
            echo "  curl -H 'Host: echo.localdev.me' http://localhost:30080"
            echo "  curl -H 'Host: echo.localdev.me' http://localhost:30080/test"
            echo
            echo "Or in your browser:"
            echo "  Add '127.0.0.1 echo.localdev.me' to /etc/hosts"
            echo "  Then visit: http://echo.localdev.me:30080"
        else
            warn "Could not reach echo service through ingress controller"
            echo "Troubleshooting steps:"
            echo "  1. Check HAProxy status: kubectl -n $CTRL_NAMESPACE get pods -l app=haproxy"
            echo "  2. Check HAProxy logs: kubectl -n $CTRL_NAMESPACE logs deploy/haproxy-production -c haproxy"
            echo "  3. Check dataplane logs: kubectl -n $CTRL_NAMESPACE logs deploy/haproxy-production -c dataplane"
            echo "  4. Check controller logs: $0 logs"
            echo "  5. Check echo service: kubectl -n $ECHO_NAMESPACE get pods -l app=$ECHO_APP_NAME"
            echo "  6. Verify ingress: kubectl -n $ECHO_NAMESPACE get ingress $ECHO_APP_NAME -o wide"
            return 1
        fi
    else
        warn "Kind cluster '$CLUSTER_NAME' not found. Cannot test via NodePort."
        return 1
    fi
}

port_forward_haproxy() {
    print_section "🔄 Setting up Port Forwarding"

    echo "Setting up port forwarding for HAProxy services..."
    echo "This will forward local ports to the HAProxy services in the cluster."
    echo

    # Check if HAProxy is running
    if ! kubectl -n "$CTRL_NAMESPACE" get deployment haproxy-production >/dev/null 2>&1; then
        warn "HAProxy production deployment not found. Deploy it first with: $0 up"
        return 1
    fi

    # Get controller deployment name
    local ctrl_deploy
    ctrl_deploy=$(kubectl -n "$CTRL_NAMESPACE" get deployment -l "app.kubernetes.io/instance=${HELM_RELEASE_NAME},app.kubernetes.io/name=haproxy-template-ic-go" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "controller")

    echo "Available port forwarding options:"
    echo "  1. HAProxy HTTP (port 8080 -> 80): kubectl -n $CTRL_NAMESPACE port-forward svc/haproxy-production 8080:80"
    echo "  2. HAProxy Health (port 8404 -> 8404): kubectl -n $CTRL_NAMESPACE port-forward svc/haproxy-production 8404:8404"
    echo "  3. HAProxy Dataplane API (port 5555 -> 5555): kubectl -n $CTRL_NAMESPACE port-forward svc/haproxy-production-dataplane 5555:5555"
    echo "  4. Controller Health (port 8081 -> 8080): kubectl -n $CTRL_NAMESPACE port-forward deploy/${ctrl_deploy} 8081:8080"
    echo "  5. Controller Metrics (port 9090 -> 9090): kubectl -n $CTRL_NAMESPACE port-forward deploy/${ctrl_deploy} 9090:9090"
    echo

    read -p "Choose an option (1-5) or 'q' to quit: " choice

    case "$choice" in
        1)
            log INFO "Starting port forwarding: localhost:8080 -> HAProxy HTTP"
            echo "Test with: curl -H 'Host: echo.localdev.me' http://localhost:8080"
            kubectl -n "$CTRL_NAMESPACE" port-forward svc/haproxy-production 8080:80
            ;;
        2)
            log INFO "Starting port forwarding: localhost:8404 -> HAProxy Health"
            echo "Test with: curl http://localhost:8404/healthz"
            kubectl -n "$CTRL_NAMESPACE" port-forward svc/haproxy-production 8404:8404
            ;;
        3)
            log INFO "Starting port forwarding: localhost:5555 -> HAProxy Dataplane API"
            echo "Test with: curl -u admin:adminpass http://localhost:5555/v3/info"
            kubectl -n "$CTRL_NAMESPACE" port-forward svc/haproxy-production-dataplane 5555:5555
            ;;
        4)
            log INFO "Starting port forwarding: localhost:8081 -> Controller Health"
            echo "Test with: curl http://localhost:8081/healthz"
            kubectl -n "$CTRL_NAMESPACE" port-forward deploy/${ctrl_deploy} 8081:8080
            ;;
        5)
            log INFO "Starting port forwarding: localhost:9090 -> Controller Metrics"
            echo "Test with: curl http://localhost:9090/metrics"
            kubectl -n "$CTRL_NAMESPACE" port-forward deploy/${ctrl_deploy} 9090:9090
            ;;
        q|Q)
            echo "Exiting port forwarding setup"
            return 0
            ;;
        *)
            err "Invalid choice: $choice"
            return 1
            ;;
    esac
}

post_deploy_tips() {
	echo
	ok "Environment is up. Next steps:"
	echo "  - Watch resources: kubectl get pods -A -w"
	echo "  - Controller logs: $0 logs"
	echo "  - HAProxy production logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-production -f -c haproxy"
	echo "  - Dataplane logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-production -f -c dataplane"
	echo "  - Echo service: kubectl -n ${ECHO_NAMESPACE} get svc ${ECHO_APP_NAME}"
	echo "  - Ingress: kubectl -n ${ECHO_NAMESPACE} get ingress ${ECHO_APP_NAME} -o wide"
	echo

	ok "🧪 Testing the Ingress Controller:"
	echo "  - Quick test: $0 test"
	echo "  - Manual test: curl -H 'Host: echo.localdev.me' http://localhost:30080"
	echo "  - Browser test: Add '127.0.0.1 echo.localdev.me' to /etc/hosts, visit http://echo.localdev.me:30080"
	echo "  - Port forwarding: $0 port-forward"
	echo

	ok "🎛️  HAProxy Production Environment:"
	echo "  - Production HAProxy pods: kubectl -n ${CTRL_NAMESPACE} get deploy/haproxy-production"
	echo "  - HAProxy service: kubectl -n ${CTRL_NAMESPACE} get svc/haproxy-production"
	echo "  - Dataplane API service: kubectl -n ${CTRL_NAMESPACE} get svc/haproxy-production-dataplane"
	echo "  - Dataplane API access: kubectl -n ${CTRL_NAMESPACE} port-forward svc/haproxy-production-dataplane 5555:5555"
	echo "    Access at: http://localhost:5555/v3/info (admin/adminpass)"
	echo

	ok "📊 Monitoring:"
	echo "  - Controller health: curl http://localhost:30080/healthz (via port-forward)"
	echo "  - Controller metrics: curl http://localhost:9090/metrics (via port-forward)"
	echo "  - HAProxy health: curl http://localhost:30404/healthz (via NodePort)"
	echo

	warn "Troubleshooting hints:"
	echo "  - Check status: $0 status"
	echo "  - Inspect events: kubectl get events --all-namespaces --sort-by=.lastTimestamp | tail -n 50"
	echo "  - Describe controller: kubectl -n ${CTRL_NAMESPACE} get deployments -l app.kubernetes.io/instance=${HELM_RELEASE_NAME}"
	echo "  - Describe HAProxy: kubectl -n ${CTRL_NAMESPACE} describe deploy/haproxy-production"
	echo "  - Check Helm release: helm list -n ${CTRL_NAMESPACE}"
	echo "  - Helm history: helm history ${HELM_RELEASE_NAME} -n ${CTRL_NAMESPACE}"
	echo
}


dev_up() {
    print_section "🏗️  Starting Development Environment"

    log INFO "Preflight checks..."
    require_cmd kind
    require_cmd kubectl
    require_cmd docker
    require_cmd helm
    ok "Dependencies present."

    ensure_cluster

    deploy_controller || {
        err "Controller deployment failed"
        return 1
    }

    deploy_haproxy || {
        err "HAProxy deployment failed"
        return 1
    }

    deploy_ingressclass

    if [[ "$SKIP_ECHO" != "true" ]]; then
        deploy_echo_server
    fi

    post_deploy_tips
}


main() {
    parse_args "$@"

    case "$COMMAND" in
        up)
            dev_up
            ;;
        down|clean)
            dev_down "$@"
            ;;
        logs)
            dev_logs
            ;;
        exec)
            dev_exec
            ;;
        restart)
            dev_restart
            ;;
        status)
            dev_status
            ;;
        test)
            test_ingress
            ;;
        port-forward)
            port_forward_haproxy
            ;;
        *)
            err "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Now that all functions are defined, set up the environment and trap
pushd "${REPO_ROOT}" >/dev/null 2>&1 || {
    echo "Error: Could not change to repository root directory"
    exit 1
}
trap cleanup_on_exit EXIT

main "$@"
