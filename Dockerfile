ARG PYTHON_VERSION=3.13

# Base system dependencies stage - rarely changes, good for caching
FROM python:${PYTHON_VERSION}-slim-bookworm AS system-deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        dumb-init \
        libssl3 \
        libssl-dev \
        ca-certificates \
        git \
        socat && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# UV setup stage - cache UV installation separately
FROM system-deps AS uv-base
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python${PYTHON_VERSION} \
    UV_PROJECT_ENVIRONMENT=/app

# Dependencies-only stage - maximizes cache reuse when only code changes
FROM uv-base AS dependencies
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project

# Build stage - installs the actual project
FROM dependencies AS build
WORKDIR /src

# Copy source files needed for installation
COPY haproxy_template_ic/ haproxy_template_ic/
COPY pyproject.toml .
COPY uv.lock .
COPY README.md . 

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv sync \
        --locked \
        --no-dev \
        --no-editable

FROM system-deps AS runtime-base

# Optional: add the application virtualenv to search path.
ENV PATH=/app/bin:$PATH

# Don't run your app as root.
RUN groupadd -r app && \
    useradd -r -d /app -g app -N app && \
    mkdir -p /run/haproxy-template-ic && \
    chown app:app /run/haproxy-template-ic

COPY --from=build --chown=app:app /app /app

USER app
WORKDIR /app

# Verify installation in a single layer
RUN python -V && \
    python -Im site && \
    python -c 'import haproxy_template_ic'

FROM runtime-base AS production
ENTRYPOINT ["dumb-init", "/app/bin/haproxy-template-ic"]

FROM runtime-base AS coverage
# Switch to root temporarily to install coverage
USER root
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-cache \
    pip install --no-cache-dir coverage

# Copy the coverage wrapper script and create wrapper script in single layer
RUN --mount=type=bind,source=coverage_wrapper.py,target=/tmp/coverage_wrapper.py \
    cp /tmp/coverage_wrapper.py /app/coverage_wrapper.py && \
    echo '#!/bin/bash\ncd /app\nPYTHONPATH=/app/lib/python3.13/site-packages:/app/.local/lib/python3.13/site-packages python /app/coverage_wrapper.py "$@"' > /app/run-with-coverage.sh && \
    chmod +x /app/run-with-coverage.sh && \
    chown app:app /app/coverage_wrapper.py /app/run-with-coverage.sh

USER app
ENTRYPOINT ["dumb-init", "/app/run-with-coverage.sh"]
