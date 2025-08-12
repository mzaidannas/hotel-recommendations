FROM python:3.13-slim AS build

RUN apt-get update && apt-get install -y \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    curl \
    ca-certificates \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.13 \
    UV_PROJECT_ENVIRONMENT=/app

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
    --locked \
    --no-dev \
    --no-install-project

FROM python:3.13-slim

# Optional: add the application virtualenv to search path.
ENV PATH=/app/bin:$PATH

# Copy the pre-built `/app` directory to the runtime container
# and change the ownership to user app and group app in one step.
COPY --from=build /app /app

# If your application is NOT a proper Python package that got
# pip-installed above, you need to copy your application into
# the container HERE:
COPY . /app/

WORKDIR /app

# Expose port
EXPOSE 8000

# Run app
CMD ["fastmcp", "run", "app/main.py", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000", "--path", "/mcp"]
