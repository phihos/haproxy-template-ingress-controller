ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}-slim-bookworm AS base
# Install dumb-init for proper signal handling
RUN apt-get update && apt-get install -y dumb-init && rm -rf /var/lib/apt/lists/*

FROM base AS build
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python${PYTHON_VERSION} \
    UV_PROJECT_ENVIRONMENT=/app

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project

COPY . /src
WORKDIR /src
RUN --mount=type=cache,target=/root/.cache \
    uv sync \
        --locked \
        --no-dev \
        --no-editable

FROM base AS runtime-base

# Optional: add the application virtualenv to search path.
ENV PATH=/app/bin:$PATH

# Don't run your app as root.
RUN <<EOT
groupadd -r app
useradd -r -d /app -g app -N app
EOT

COPY --from=build --chown=app:app /app /app

USER app
WORKDIR /app

RUN <<EOT
python -V
python -Im site
python -c 'import haproxy_template_ic'
EOT

FROM runtime-base AS production
ENTRYPOINT ["dumb-init", "/app/bin/haproxy-template-ic"]

FROM runtime-base AS coverage
# Install coverage for the container
RUN pip install coverage

# Copy the coverage wrapper script
COPY coverage_wrapper.py /app/coverage_wrapper.py

# Create a wrapper script 
RUN echo '#!/bin/bash\ncd /app\nPYTHONPATH=/app/lib/python3.13/site-packages:/app/.local/lib/python3.13/site-packages python /app/coverage_wrapper.py "$@"' > /app/run-with-coverage.sh && \
    chmod +x /app/run-with-coverage.sh

ENTRYPOINT ["dumb-init", "/app/run-with-coverage.sh"]
