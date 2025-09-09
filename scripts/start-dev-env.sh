#!/usr/bin/env bash

set -euo pipefail

# Ensure we operate from the repo root regardless of where the script is invoked
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default configuration
CLUSTER_NAME="haproxy-template-ic-dev"
CTRL_NAMESPACE="haproxy-template-ic"
ECHO_NAMESPACE="echo"
ECHO_APP_NAME="echo-server"
ECHO_IMAGE="ealen/echo-server:latest"
LOCAL_IMAGE="haproxy-template-ic:dev"
TIMEOUT="180"
SKIP_BUILD=false
SKIP_ECHO=false
FORCE_REBUILD=false
VERBOSE=false
WATCH_MODE=false

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

detect_kind_host_ip() {
    local kind_network_name="kind"
    
    # Try to get the Kind Docker network gateway IP
    if command -v docker &>/dev/null; then
        local gateway_ip
        gateway_ip=$(docker network inspect "$kind_network_name" 2>/dev/null | grep -A5 '"Config"' | grep '"Gateway"' | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')
        
        if [[ -n "$gateway_ip" && "$gateway_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "$gateway_ip"
            return 0
        fi
    fi
    
    # Fallback to common Kind gateway IPs
    for candidate in "172.20.0.1" "172.18.0.1" "172.17.0.1"; do
        if timeout 1 bash -c "exec 3<>/dev/tcp/$candidate/1" 2>/dev/null; then
            echo "$candidate"
            return 0
        fi 2>/dev/null
    done
    
    # Last resort: Kind default
    echo "172.20.0.1"
}

ensure_buildx_builder() {
    local builder_name="haproxy-ic-builder"
    
    debug "Checking for docker-container builder..."
    
    # Check if our builder already exists
    if docker buildx ls 2>/dev/null | grep -q "^${builder_name}"; then
        debug "Builder '${builder_name}' already exists"
        docker buildx use "${builder_name}" >/dev/null 2>&1
        return 0
    fi
    
    # Create and bootstrap the builder
    debug "Creating docker-container builder '${builder_name}'..."
    if [[ "$VERBOSE" == "true" ]]; then
        log INFO "Setting up docker-container builder for optimized caching..."
        docker buildx create --driver docker-container --name "${builder_name}" --bootstrap
    else
        docker buildx create --driver docker-container --name "${builder_name}" --bootstrap >/dev/null 2>&1
    fi
    
    if [[ $? -eq 0 ]]; then
        docker buildx use "${builder_name}" >/dev/null 2>&1
        debug "Builder '${builder_name}' created and activated"
        return 0
    else
        warn "Failed to create docker-container builder, falling back to default driver"
        return 1
    fi
}

cleanup_buildx_builder() {
    local builder_name="haproxy-ic-builder"
    
    debug "Cleaning up docker-container builder..."
    
    # Switch back to default builder first
    docker buildx use default >/dev/null 2>&1
    
    # Remove our builder if it exists
    if docker buildx ls 2>/dev/null | grep -q "^${builder_name}"; then
        log INFO "Removing docker-container builder '${builder_name}'..."
        docker buildx rm "${builder_name}" >/dev/null 2>&1 || true
        ok "Builder removed"
    fi
}


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
    dashboard   Launch live status dashboard for monitoring
    port-forward Setup port forwarding for HAProxy services
    debug       Enable debug mode (sleeps controller, creates dev config)
    no-debug    Disable debug mode (restores normal operation)
    telepresence-connect    Connect to cluster via Telepresence
    telepresence-disconnect Disconnect Telepresence
    telepresence-status     Show Telepresence connection status

OPTIONS:
    --cluster-name NAME     Custom cluster name (default: haproxy-template-ic-dev)
    --namespace NAME        Custom controller namespace (default: haproxy-template-ic)
    --image-tag TAG         Custom image tag (default: dev)
    --timeout SECONDS       Deployment timeout (default: 180)
    --skip-build            Use existing image if available
    --skip-echo             Don't deploy echo server
    --force-rebuild         Force rebuild without cache
    --verbose               Enable debug output
    --watch                 Watch for changes and auto-rebuild
    --help, -h              Show this help

EXAMPLES:
    $0                      # Start dev environment with defaults
    $0 up --skip-build      # Start without rebuilding image
    $0 restart              # Rebuild image and restart controller
    $0 restart --skip-build # Restart controller without rebuilding
    $0 test                 # Test ingress controller functionality
    $0 dashboard            # Launch live monitoring dashboard
    $0 logs                 # Follow controller logs
    $0 port-forward         # Setup port forwarding for testing
    $0 down                 # Delete cluster
    $0 restart --verbose    # Restart with debug output
    $0 debug                # Enter debug mode for local development
    $0 telepresence-connect # Connect via Telepresence for debugging
    $0 no-debug             # Exit debug mode

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
                LOCAL_IMAGE="haproxy-template-ic:$2"
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
            --watch)
                WATCH_MODE=true
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
    
    # Reset any failed deployments
    kubectl -n "$CTRL_NAMESPACE" rollout undo deployment/haproxy-template-ic 2>/dev/null || true
    kubectl -n "$CTRL_NAMESPACE" rollout undo deployment/haproxy-production 2>/dev/null || true
    
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
		missing-telepresence)
			warn "Install Telepresence: https://www.telepresence.io/docs/latest/install/"
			echo "  - Linux/macOS: curl -fL https://app.getambassador.io/download/tel2/linux/amd64/latest/telepresence -o telepresence"
			echo "  - Or use package manager:"
			echo "    - Homebrew: brew install datawire/blackbird/telepresence"
			echo "    - Arch: yay -S telepresence2"
			;;
		pull-failure)
			warn "If the controller image cannot be pulled from GHCR:"
			echo "  - Ensure network access to ghcr.io"
			echo "  - If the image is private, run: docker login ghcr.io"
			echo "  - Alternatively, build locally and load into kind:"
			echo "      docker build --target production -t haproxy-template-ic:dev ."
			echo "      kind load docker-image haproxy-template-ic:dev --name ${CLUSTER_NAME}"
			echo "      kubectl -n ${CTRL_NAMESPACE} set image deploy/haproxy-template-ic controller=haproxy-template-ic:dev"
			;;
		rollout-timeout)
			warn "Rollout timed out. Inspect events and logs:"
			echo "  kubectl -n ${CTRL_NAMESPACE} get events --sort-by=.lastTimestamp | tail -n 50"
			echo "  kubectl -n ${CTRL_NAMESPACE} describe deploy/haproxy-template-ic"
			echo "  kubectl -n ${CTRL_NAMESPACE} get pods -o wide"
			echo "  kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-template-ic --previous || true"
			;;
		*) ;;
	 esac
}

ensure_cluster() {
	if ! kind get clusters | grep -qx "${CLUSTER_NAME}"; then
		log INFO "Creating kind cluster '${CLUSTER_NAME}'..."
		kind create cluster --name "${CLUSTER_NAME}" --config "${REPO_ROOT}/kind-config.yaml"
		ok "Cluster created with admission controllers enabled."
	else
		ok "Using existing cluster '${CLUSTER_NAME}'."
	fi

	local ctx="kind-${CLUSTER_NAME}"
	if ! kubectl config get-contexts -o name | grep -qx "$ctx"; then
		err "kubectl context '$ctx' not found after cluster creation."
		exit 1
	fi
	kubectl config use-context "$ctx" >/dev/null
	ok "Context configured."
}

install_metrics_server() {
	log INFO "Installing metrics-server for pod resource monitoring..."
	
	# Install the latest metrics-server components
	if run_with_spinner "Installing metrics-server v0.8.0" \
		kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.8.0/components.yaml; then
		ok "Metrics-server manifest applied."
	else
		warn "Failed to apply metrics-server manifest"
		return 1
	fi
	
	# Apply the required patch for kind clusters (disable TLS verification)
	log INFO "Configuring metrics-server for kind cluster..."
	if kubectl patch -n kube-system deployment metrics-server --type=json \
		-p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]' >/dev/null 2>&1; then
		ok "Metrics-server configured for kind cluster."
	else
		warn "Failed to patch metrics-server configuration"
		return 1
	fi
	
	# Wait for metrics-server to be ready
	log INFO "Waiting for metrics-server to become ready..."
	if kubectl -n kube-system rollout status deployment/metrics-server --timeout=60s >/dev/null 2>&1; then
		ok "Metrics-server is ready."
	else
		warn "Metrics-server rollout did not complete in 60s"
		return 1
	fi
	
	# Verify metrics are available (may take a few more seconds)
	log INFO "Verifying metrics availability..."
	attempts=0
	while [[ $attempts -lt 10 ]]; do
		if kubectl top nodes >/dev/null 2>&1; then
			ok "Metrics-server is collecting node metrics successfully."
			return 0
		fi
		debug "Metrics not ready yet, waiting 10 seconds... (attempt $((attempts + 1))/10)"
		sleep 10
		((attempts++)) || true
	done
	
	warn "Metrics-server installed but metrics may not be immediately available"
	warn "This is normal and metrics should be available within a few minutes"
	return 0
}

install_telepresence_traffic_manager() {
	log INFO "Installing Telepresence traffic manager..."
	if telepresence helm install 2>/dev/null; then
		ok "Telepresence traffic manager installed."
	else
		warn "Telepresence traffic manager already installed or installation failed."
	fi
}

create_dev_configmap() {
	log INFO "Creating development ConfigMap for Telepresence..."
	
	# Get the original ConfigMap
	kubectl -n "${CTRL_NAMESPACE}" get configmap haproxy-template-ic-config -o yaml > /tmp/original-configmap.yaml
	
	# Create modified ConfigMap with dev-specific settings
	sed -e 's/name: haproxy-template-ic-config/name: haproxy-template-ic-config-dev/' \
	    -e 's/dataplane_host: localhost/dataplane_host: haproxy-template-ic/' \
	    -e 's|socket_path: /run/haproxy-template-ic/management.sock|socket_path: mgmt.sock|' \
	    /tmp/original-configmap.yaml | kubectl apply -f -
	
	rm -f /tmp/original-configmap.yaml
	ok "Development ConfigMap created."
}

remove_dev_configmap() {
	log INFO "Removing development ConfigMap..."
	kubectl -n "${CTRL_NAMESPACE}" delete configmap haproxy-template-ic-config-dev --ignore-not-found=true
	ok "Development ConfigMap removed."
}

enter_debug_mode() {
	print_section "🐛 Entering Debug Mode"
	
	log INFO "Setting controller to sleep mode..."
	kubectl -n "${CTRL_NAMESPACE}" patch deployment haproxy-template-ic \
		--type='json' \
		-p='[{"op": "replace", "path": "/spec/template/spec/containers/0/command", "value": ["/usr/bin/sleep"]}, 
		     {"op": "replace", "path": "/spec/template/spec/containers/0/args", "value": ["infinity"]},
		     {"op": "replace", "path": "/spec/template/spec/containers/0/env/0/value", "value": "haproxy-template-ic-config-dev"}]'
	
	log INFO "Waiting for controller to enter sleep mode..."
	kubectl -n "${CTRL_NAMESPACE}" rollout status deployment/haproxy-template-ic --timeout=60s
	
	create_dev_configmap
	
	ok "Debug mode enabled. Controller is sleeping and dev ConfigMap created."
	echo
	ok "🚀 Next steps for local development:"
	echo "  1. Connect via Telepresence: $0 telepresence-connect"
	echo "  2. Run locally: CONFIGMAP_NAME=haproxy-template-ic-config-dev SECRET_NAME=haproxy-template-ic-credentials uv run haproxy-template-ic run"
	echo "  3. Management socket will be available at: mgmt.sock"
	echo "  4. When done, restore: $0 no-debug"
}

exit_debug_mode() {
	print_section "🔄 Exiting Debug Mode"
	
	log INFO "Restoring controller to normal operation..."
	kubectl -n "${CTRL_NAMESPACE}" patch deployment haproxy-template-ic \
		--type='json' \
		-p='[{"op": "replace", "path": "/spec/template/spec/containers/0/command", "value": ["haproxy-template-ic"]}, 
		     {"op": "replace", "path": "/spec/template/spec/containers/0/args", "value": ["run"]},
		     {"op": "replace", "path": "/spec/template/spec/containers/0/env/0/value", "value": "haproxy-template-ic-config"}]'
	
	log INFO "Waiting for controller to restart..."
	kubectl -n "${CTRL_NAMESPACE}" rollout status deployment/haproxy-template-ic --timeout=120s
	
	remove_dev_configmap
	
	ok "Debug mode disabled. Controller restored to normal operation."
}

telepresence_connect() {
	print_section "🔌 Connecting via Telepresence"
	
	if ! command -v telepresence >/dev/null 2>&1; then
		err "Telepresence not found. Please install it first."
		troubleshooting "missing-telepresence"
		return 1
	fi
	
	log INFO "Connecting to cluster via Telepresence..."
	telepresence connect --context "kind-${CLUSTER_NAME}" --namespace "${CTRL_NAMESPACE}"
	
	if [ $? -eq 0 ]; then
		ok "Telepresence connected successfully."
		echo
		ok "🎯 Development environment ready:"
		echo "  - Run locally: CONFIGMAP_NAME=haproxy-template-ic-config-dev SECRET_NAME=haproxy-template-ic-credentials uv run haproxy-template-ic run"
		echo "  - Management socket: mgmt.sock"
		echo "  - Validation endpoint: haproxy-template-ic:5555"
		echo "  - Disconnect: $0 telepresence-disconnect"
	else
		err "Failed to connect via Telepresence."
		return 1
	fi
}

telepresence_disconnect() {
	print_section "🔌 Disconnecting Telepresence"
	
	log INFO "Disconnecting from cluster..."
	telepresence quit
	
	ok "Telepresence disconnected."
}

telepresence_status() {
	print_section "📊 Telepresence Status"
	
	if ! command -v telepresence >/dev/null 2>&1; then
		err "Telepresence not found."
		troubleshooting "missing-telepresence"
		return 1
	fi
	
	telepresence status
}

build_and_load_local_image() {
    if [[ "$SKIP_BUILD" == "true" ]] && docker image inspect "${LOCAL_IMAGE}" >/dev/null 2>&1; then
        ok "Using existing image '${LOCAL_IMAGE}'"
        return 0
    fi
    
    # Determine build target based on image tag
    local build_target="production"
    if [[ "${LOCAL_IMAGE}" == *":debug" ]]; then
        build_target="debug"
    fi
    
    # Set up docker-container builder for cache optimization
    local use_cache=false
    if ensure_buildx_builder; then
        use_cache=true
        debug "Using docker-container builder with cache optimization"
    else
        debug "Using default docker driver without cache"
        export DOCKER_BUILDKIT=1
    fi
    
    local build_args=("--target" "${build_target}" "-t" "${LOCAL_IMAGE}" "--load")
    local docker_path
    docker_path="$(command -v docker)"
    local build_cmd="${docker_path}"
    
    if [[ "$use_cache" == "true" ]]; then
        build_cmd="${docker_path} buildx"
        
        # Add cache optimization for faster rebuilds
        if [[ "$FORCE_REBUILD" == "true" ]]; then
            build_args+=("--no-cache")
        else
            # Use local cache for faster iteration
            local cache_dir="/tmp/haproxy-template-ic-buildcache"
            build_args+=(
                "--cache-from" "type=local,src=${cache_dir}"
                "--cache-to" "type=local,dest=${cache_dir}"
            )
        fi
    else
        # Fallback to standard docker build without cache
        if [[ "$FORCE_REBUILD" == "true" ]]; then
            build_args+=("--no-cache")
        fi
    fi
    
    build_args+=(".")
    
    local build_message="Building controller image '${LOCAL_IMAGE}' (target: ${build_target}"
    if [[ "$use_cache" == "true" ]]; then
        build_message+=", with cache optimization"
    fi
    build_message+=")"
    
    if [[ "$use_cache" == "true" ]]; then
        run_with_spinner "$build_message" \
            "${docker_path}" buildx build "${build_args[@]}"
    else
        run_with_spinner "$build_message" \
            "${build_cmd}" build "${build_args[@]}"
    fi
    
    run_with_spinner "Loading image into kind cluster '${CLUSTER_NAME}'" \
        kind load docker-image "${LOCAL_IMAGE}" --name "${CLUSTER_NAME}"
}

deploy_controller() {
    local overlay_name="${1:-dev}"
    
    build_and_load_local_image || {
        err "Failed to build or load image"
        return 1
    }
    
    print_section "🚀 Deploying Controller (${overlay_name} mode)"
    
    log INFO "Deploying haproxy-template-ic to namespace '${CTRL_NAMESPACE}' using kustomize overlay..."
    retry_with_backoff 3 2 kubectl apply -k "deploy/overlays/${overlay_name}" || {
        err "Failed to apply kustomize overlay"
        cleanup_failed_deployment
        return 1
    }
    
    log INFO "Pointing deployment to local image '${LOCAL_IMAGE}'..."
    kubectl -n "${CTRL_NAMESPACE}" set image deployment/haproxy-template-ic controller="${LOCAL_IMAGE}" >/dev/null || true
    
    log INFO "Waiting for controller deployment to become ready..."
    if ! kubectl -n "${CTRL_NAMESPACE}" rollout status deployment/haproxy-template-ic --timeout="${TIMEOUT}s"; then
        err "Controller rollout did not complete in ${TIMEOUT}s."
        troubleshooting "rollout-timeout"
        cleanup_failed_deployment
        return 1
    fi
    ok "Controller is ready."
    
    # Wait for HAProxy production deployment (skip in debug mode since controller needs to configure it first)
    if [[ "${overlay_name}" != "debug" ]]; then
        log INFO "Waiting for HAProxy production deployment to become ready..."
        if ! kubectl -n "${CTRL_NAMESPACE}" rollout status deployment/haproxy-production --timeout="${TIMEOUT}s"; then
            warn "HAProxy production deployment rollout did not complete in ${TIMEOUT}s."
            echo "  - Check HAProxy deployment status: kubectl -n ${CTRL_NAMESPACE} describe deploy/haproxy-production"
            echo "  - Check HAProxy pod logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-production -c haproxy"
            echo "  - Check dataplane logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-production -c dataplane"
            return 1
        else
            ok "HAProxy production deployment is ready."
        fi
    else
        log INFO "Skipping HAProxy production deployment readiness check in debug mode"
        ok "Debug mode: HAProxy will be configured once controller starts running."
    fi
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
    kubectl -n "$CTRL_NAMESPACE" logs -f deploy/haproxy-template-ic
}

dev_exec() {
    kubectl -n "$CTRL_NAMESPACE" exec -it deploy/haproxy-template-ic -- bash
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
    
    # Restart the deployment with the new image
    kubectl -n "$CTRL_NAMESPACE" rollout restart deploy/haproxy-template-ic
    kubectl -n "$CTRL_NAMESPACE" rollout status deploy/haproxy-template-ic --timeout="${TIMEOUT}s"
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
    
    # Clean up docker-container builder
    cleanup_buildx_builder
    
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
            ok "✅ Ingress controller is working! Echo service is accessible"
            echo
            echo "Test the ingress controller with:"
            echo "  curl -H 'Host: echo.localdev.me' http://localhost:30080"
            echo "  curl -H 'Host: echo.localdev.me' http://localhost:30080/test"
            echo
            echo "Or in your browser:"
            echo "  Add '127.0.0.1 echo.localdev.me' to /etc/hosts"
            echo "  Then visit: http://echo.localdev.me:30080"
        else
            warn "❌ Could not reach echo service through ingress controller"
            echo "Troubleshooting steps:"
            echo "  1. Check HAProxy status: kubectl -n $CTRL_NAMESPACE get pods -l app=haproxy"
            echo "  2. Check HAProxy logs: kubectl -n $CTRL_NAMESPACE logs deploy/haproxy-production -c haproxy"
            echo "  3. Check echo service: kubectl -n $ECHO_NAMESPACE get pods -l app=$ECHO_APP_NAME"
            echo "  4. Verify ingress: kubectl -n $ECHO_NAMESPACE get ingress $ECHO_APP_NAME -o wide"
            return 1
        fi
    else
        warn "Kind cluster '$CLUSTER_NAME' not found. Cannot test via NodePort."
        return 1
    fi
}

launch_dashboard() {
    print_section "📊 Launching Live Status Dashboard"
    
    # Check if haproxy-template-ic CLI is available
    if ! command -v haproxy-template-ic >/dev/null 2>&1; then
        warn "haproxy-template-ic CLI not found. Installing from current directory..."
        log INFO "Installing haproxy-template-ic CLI..."
        if command -v uv >/dev/null 2>&1; then
            uv pip install -e "${REPO_ROOT}"
        else
            pip install -e "${REPO_ROOT}"
        fi
    fi
    
    # Check if cluster exists
    if ! kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
        err "Cluster '$CLUSTER_NAME' not found. Start environment first with: $0 up"
        return 1
    fi
    
    # Check if controller is deployed
    if ! kubectl -n "$CTRL_NAMESPACE" get deployment haproxy-template-ic >/dev/null 2>&1; then
        err "Controller not found in namespace '$CTRL_NAMESPACE'. Deploy it first with: $0 up"
        return 1
    fi
    
    # Set kubectl context
    kubectl config use-context "kind-${CLUSTER_NAME}" >/dev/null
    
    # Launch dashboard with appropriate parameters
    log INFO "Starting dashboard for cluster '${CLUSTER_NAME}' namespace '${CTRL_NAMESPACE}'..."
    echo
    ok "Dashboard is starting with:"
    echo "  - Context: kind-${CLUSTER_NAME}"
    echo "  - Namespace: ${CTRL_NAMESPACE}"
    echo "  - Refresh interval: 5 seconds"
    echo
    echo "Press 'q' to quit, 'r' to refresh, 'h' for help"
    echo
    
    # Run the dashboard command
    uv run haproxy-template-ic dashboard \
        --namespace "${CTRL_NAMESPACE}" \
        --context "kind-${CLUSTER_NAME}" \
        --refresh 5
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
    
    echo "Available port forwarding options:"
    echo "  1. HAProxy HTTP (port 8080 -> 80): kubectl -n $CTRL_NAMESPACE port-forward svc/haproxy-production 8080:80"
    echo "  2. HAProxy Health (port 8404 -> 8404): kubectl -n $CTRL_NAMESPACE port-forward svc/haproxy-production 8404:8404"
    echo "  3. Controller Metrics (port 9090 -> 9090): kubectl -n $CTRL_NAMESPACE port-forward svc/haproxy-template-ic-metrics 9090:9090"
    echo "  4. Controller Health (port 8081 -> 8080): kubectl -n $CTRL_NAMESPACE port-forward deploy/haproxy-template-ic 8081:8080"
    echo
    
    read -p "Choose an option (1-4) or 'q' to quit: " choice
    
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
            log INFO "Starting port forwarding: localhost:9090 -> Controller Metrics"
            echo "Test with: curl http://localhost:9090/metrics"
            kubectl -n "$CTRL_NAMESPACE" port-forward svc/haproxy-template-ic-metrics 9090:9090
            ;;
        4)
            log INFO "Starting port forwarding: localhost:8081 -> Controller Health"
            echo "Test with: curl http://localhost:8081/healthz"
            kubectl -n "$CTRL_NAMESPACE" port-forward deploy/haproxy-template-ic 8081:8080
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
	echo "  - Controller logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-template-ic -f"
	echo "  - HAProxy production logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-production -f"
	echo "  - Echo service: kubectl -n ${ECHO_NAMESPACE} get svc ${ECHO_APP_NAME}"
	echo "  - Ingress: kubectl -n ${ECHO_NAMESPACE} get ingress ${ECHO_APP_NAME} -o wide"
	echo
	
	ok "🧪 Testing the Ingress Controller:"
	echo "  - Quick test: $0 test"
	echo "  - Manual test: curl -H 'Host: echo.localdev.me' http://localhost:30080"
	echo "  - Browser test: Add '127.0.0.1 echo.localdev.me' to /etc/hosts, visit http://echo.localdev.me:30080"
	echo "  - Port forwarding: $0 port-forward"
	echo
	
	ok "📊 Live Monitoring:"
	echo "  - Dashboard: $0 dashboard"
	echo "  - Dashboard help: $0 dashboard --help"
	echo "  - Pod resource usage: kubectl top pods -A"
	echo "  - Node resource usage: kubectl top nodes"
	echo
	ok "Monitoring & Observability:"
	echo "  - Metrics (Prometheus): kubectl -n ${CTRL_NAMESPACE} port-forward svc/haproxy-template-ic-metrics 9090:9090"
	echo "    Access at: http://localhost:9090/metrics"
	echo "  - Health check: kubectl -n ${CTRL_NAMESPACE} port-forward deploy/haproxy-template-ic 8080:8080"
	echo "    Access at: http://localhost:8080/healthz"
	echo "  - HAProxy health: kubectl -n ${CTRL_NAMESPACE} port-forward svc/haproxy-production 8404:8404"
	echo "    Access at: http://localhost:8404/healthz"
	echo "  - ServiceMonitor: kubectl -n ${CTRL_NAMESPACE} get servicemonitor haproxy-template-ic -o yaml"
	echo
	ok "HAProxy Production Environment:"
	echo "  - Production HAProxy pods: kubectl -n ${CTRL_NAMESPACE} get deploy/haproxy-production"
	echo "  - HAProxy service: kubectl -n ${CTRL_NAMESPACE} get svc/haproxy-production"
	echo "  - Dataplane API service: kubectl -n ${CTRL_NAMESPACE} get svc/haproxy-production-dataplane"
	echo "  - Dataplane API access: kubectl -n ${CTRL_NAMESPACE} port-forward svc/haproxy-production-dataplane 5555:5555"
	echo "    Access at: http://localhost:5555/v3/info (admin/adminpass)"
	echo
	ok "Advanced Features (enabled in dev):"
	echo "  - Validation sidecars: HAProxy config validation before deployment (port 8404/5555)"
	echo "  - Production HAProxy: 2 replica deployment with Dataplane API sidecars"
	echo "  - Validating admission webhooks: Validate ConfigMaps and watched resources (Ingress, Secrets)"
	echo "  - Template snippet system: Reusable Jinja2 snippets with {% include %} support"
	echo "  - Resilience patterns: Adaptive timeouts, retry logic, and circuit breakers"
	echo "  - Comprehensive observability: Prometheus metrics and OpenTelemetry tracing"
	echo "  - Permissive networking: All traffic allowed for easier development and debugging"
	echo "  - Optional features (disabled by default):"
	echo "    - Structured JSON logging: Set STRUCTURED_LOGGING=true environment variable"
	echo "    - Distributed tracing: Set TRACING_ENABLED=true and configure Jaeger endpoint"
	echo
	warn "Troubleshooting hints:"
	echo "  - Image pull issues: see notes above to build locally and 'kind load docker-image'"
	echo "  - Inspect events: kubectl get events --all-namespaces --sort-by=.lastTimestamp | tail -n 50"
	echo "  - Describe resources: kubectl -n ${CTRL_NAMESPACE} describe deploy/haproxy-template-ic"
	echo "  - Describe HAProxy: kubectl -n ${CTRL_NAMESPACE} describe deploy/haproxy-production"
	echo "  - Socket debug: kubectl -n ${CTRL_NAMESPACE} exec -it deploy/haproxy-template-ic -- sh -c 'nc local:/run/haproxy-template-ic/management.sock'"
	echo "  - Check metrics: kubectl -n ${CTRL_NAMESPACE} get pods -l app=haproxy-template-ic --show-labels"
	echo "  - Check HAProxy pods: kubectl -n ${CTRL_NAMESPACE} get pods -l app=haproxy,component=loadbalancer --show-labels"
	echo "  - Network policies: kubectl -n ${CTRL_NAMESPACE} get networkpolicy"
	echo
	warn "Optional components (may be missing in basic clusters):"
	echo "  - ServiceMonitor requires Prometheus Operator CRDs"
	echo "  - To enable monitoring features, install Prometheus Operator first"
	echo "  - ValidatingAdmissionWebhook is enabled via kind cluster configuration"
	echo
}


dev_up() {
    local overlay_mode="${1:-dev}"
    
    print_section "🏗️  Starting Development Environment (${overlay_mode} mode)"
    
    log INFO "Preflight checks..."
    require_cmd kind
    require_cmd kubectl
    require_cmd docker
    ok "Dependencies present."

    ensure_cluster
    
    install_metrics_server
    
    install_telepresence_traffic_manager

    deploy_controller "${overlay_mode}" || { 
        troubleshooting pull-failure
        return 1
    }
    
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
        dashboard)
            launch_dashboard
            ;;
        port-forward)
            port_forward_haproxy
            ;;
        debug)
            enter_debug_mode
            ;;
        no-debug)
            exit_debug_mode
            ;;
        telepresence-connect)
            telepresence_connect
            ;;
        telepresence-disconnect)
            telepresence_disconnect
            ;;
        telepresence-status)
            telepresence_status
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
