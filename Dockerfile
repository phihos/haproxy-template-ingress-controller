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

# Create a Python wrapper that ensures coverage data is saved
RUN cat > /app/coverage_wrapper.py << 'EOF'
import sys
import os
import atexit
import signal
import coverage

# Initialize coverage with explicit data file location  
data_file = '/app/.coverage'
cov = coverage.Coverage(source=['haproxy_template_ic'], data_file=data_file)
cov.start()

# Ensure coverage is saved on exit
def save_coverage():
    try:
        print(f"Saving coverage data to {data_file}", file=sys.stderr)
        cov.stop()
        cov.save()
        print(f"Coverage data saved successfully", file=sys.stderr)
    except Exception as e:
        print(f"Failed to save coverage: {e}", file=sys.stderr)

atexit.register(save_coverage)

# Handle signals gracefully
def signal_handler(signum, frame):
    print(f"Received signal {signum}, saving coverage and exiting", file=sys.stderr)
    save_coverage()
    sys.exit(0)

def save_signal_handler(signum, frame):
    print(f"Received signal {signum}, saving coverage but continuing", file=sys.stderr)
    save_coverage()

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGUSR1, save_signal_handler)

# Import and run the main module
os.chdir('/app')
sys.path.insert(0, '/app/lib/python3.13/site-packages')
from haproxy_template_ic.__main__ import main
if __name__ == '__main__':
    main()
EOF

# Create a wrapper script 
RUN echo '#!/bin/bash\ncd /app\nPYTHONPATH=/app/lib/python3.13/site-packages:/app/.local/lib/python3.13/site-packages python /app/coverage_wrapper.py "$@"' > /app/run-with-coverage.sh && \
    chmod +x /app/run-with-coverage.sh

ENTRYPOINT ["dumb-init", "/app/run-with-coverage.sh"]
