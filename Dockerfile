# syntax=docker/dockerfile:1

# Build arguments for version control
ARG GO_VERSION=1.25
ARG HAPROXY_VERSION=3.2
ARG GIT_COMMIT=unknown
ARG GIT_TAG=unknown

# -----------------------------------------------------------------------------
# Builder stage - compile the Go binary
# -----------------------------------------------------------------------------
FROM --platform=$BUILDPLATFORM golang:${GO_VERSION} AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Leverage Docker cache for Go modules
# Copy go.mod and go.sum first to cache module downloads
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# Copy source code
COPY . .

# Build arguments for cross-compilation and version info
ARG TARGETOS
ARG TARGETARCH
ARG GIT_COMMIT
ARG GIT_TAG

# Build the controller binary
# - CGO_ENABLED=0: static binary, no C dependencies
# - GOOS/GOARCH: cross-compilation for target platform
# - -trimpath: remove file system paths from binary
# - -ldflags: linker flags for optimization and version info
#   - -s: strip debug information
#   - -w: strip DWARF debug information
#   - -X: inject version variables (placeholder for future)
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 \
    GOOS=${TARGETOS} \
    GOARCH=${TARGETARCH} \
    go build \
    -trimpath \
    -ldflags="-s -w -X main.GitCommit=${GIT_COMMIT} -X main.GitTag=${GIT_TAG}" \
    -o /build/controller \
    ./cmd/controller

# -----------------------------------------------------------------------------
# Runtime stage - minimal image with HAProxy for validation
# -----------------------------------------------------------------------------
FROM haproxytech/haproxy-debian:${HAPROXY_VERSION}

# Copy the controller binary from builder
COPY --from=builder /build/controller /usr/local/bin/controller

# Ensure binary is executable
RUN chmod +x /usr/local/bin/controller

# Create validation directories for HAProxy configuration validation
# These directories must be writable by the haproxy user
RUN mkdir -p /usr/local/etc/haproxy/maps \
             /usr/local/etc/haproxy/certs \
             /usr/local/etc/haproxy/general && \
    chown -R haproxy:haproxy /usr/local/etc/haproxy

# Switch to haproxy user for security
# The haproxy user is pre-created by the haproxytech base image
USER haproxy

# Set the entrypoint to the controller
ENTRYPOINT ["/usr/local/bin/controller"]

# Default command (can be overridden)
CMD ["run"]
