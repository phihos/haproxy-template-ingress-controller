#!/usr/bin/env bash

set -euo pipefail

# Ensure we operate from the repo root regardless of where the script is invoked
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
pushd "${REPO_ROOT}" >/dev/null
trap 'popd >/dev/null' EXIT

CLUSTER_NAME="haproxy-template-ic-dev"
CTRL_NAMESPACE="haproxy-template-ic"
ECHO_NAMESPACE="echo"
ECHO_APP_NAME="echo-server"
ECHO_IMAGE="ealen/echo-server:latest"
LOCAL_IMAGE="haproxy-template-ic:dev"

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

require_cmd() {
	if ! command -v "$1" >/dev/null 2>&1; then
		err "Required command '$1' not found in PATH."
		troubleshooting "missing-$1"
		exit 1
	fi
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
		kind create cluster --name "${CLUSTER_NAME}"
		ok "Kind cluster '${CLUSTER_NAME}' created."
	else
		ok "Kind cluster '${CLUSTER_NAME}' already exists."
	fi

	# Ensure kubectl context is set
	local ctx="kind-${CLUSTER_NAME}"
	if ! kubectl config get-contexts -o name | grep -qx "$ctx"; then
		err "kubectl context '$ctx' not found after cluster creation."
		exit 1
	fi
	kubectl config use-context "$ctx" >/dev/null
	ok "Using kubectl context '$ctx'."
}

build_and_load_local_image() {
	log INFO "Building local controller image '${LOCAL_IMAGE}' (this can take a while)..."
	docker build --no-cache --target production -t "${LOCAL_IMAGE}" .
	log INFO "Loading image into kind cluster '${CLUSTER_NAME}'..."
	kind load docker-image "${LOCAL_IMAGE}" --name "${CLUSTER_NAME}"
}

deploy_controller() {
	# Always build and load the local image first, then deploy and point to it
	build_and_load_local_image
	log INFO "Deploying haproxy-template-ic to namespace '${CTRL_NAMESPACE}' using kustomize overlay..."
	kubectl apply -k deploy/overlays/dev > /dev/null
	log INFO "Pointing deployment to local image '${LOCAL_IMAGE}'..."
	kubectl -n "${CTRL_NAMESPACE}" set image deployment/haproxy-template-ic controller="${LOCAL_IMAGE}" --record >/dev/null || true
	log INFO "Forcing controller rollout restart..."
	kubectl -n "${CTRL_NAMESPACE}" rollout restart deployment/haproxy-template-ic >/dev/null || true
	log INFO "Waiting for controller deployment to become ready..."
	if ! kubectl -n "${CTRL_NAMESPACE}" rollout status deployment/haproxy-template-ic --timeout=180s; then
		err "Controller rollout did not complete in time."
		troubleshooting "rollout-timeout"
		exit 1
	fi
	ok "Controller is ready."
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

	warn "The created Ingress targets host 'echo.localdev.me'. If you need real traffic routing, install an ingress controller (e.g. ingress-nginx) or integrate HAProxy dataplane as a data-plane. This project currently focuses on templating and watching resources. See Echo-Server docs: https://ealenn.github.io/Echo-Server/pages/quick-start/kubernetes.html"
}

post_deploy_tips() {
	echo
	ok "Environment is up. Next steps:"
	echo "  - Watch resources: kubectl get pods -A -w"
	echo "  - Controller logs: kubectl -n ${CTRL_NAMESPACE} logs deploy/haproxy-template-ic -f"
	echo "  - Echo service: kubectl -n ${ECHO_NAMESPACE} get svc ${ECHO_APP_NAME}"
	echo "  - Ingress: kubectl -n ${ECHO_NAMESPACE} get ingress ${ECHO_APP_NAME} -o wide"
	echo
	warn "Troubleshooting hints:"
	echo "  - Image pull issues: see notes above to build locally and 'kind load docker-image'"
	echo "  - Inspect events: kubectl get events --all-namespaces --sort-by=.lastTimestamp | tail -n 50"
	echo "  - Describe resources: kubectl -n ${CTRL_NAMESPACE} describe deploy/haproxy-template-ic"
	echo "  - Socket debug (if enabled): kubectl -n ${CTRL_NAMESPACE} exec -it deploy/haproxy-template-ic -- sh -c 'socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock'"
	echo
}

main() {
	log INFO "Preflight checks..."
	require_cmd kind
	require_cmd kubectl
	require_cmd docker
	ok "Dependencies present."

	ensure_cluster

	deploy_controller || { troubleshooting pull-failure; exit 1; }
	deploy_echo_server
	post_deploy_tips
}

main "$@"


