# syntax=docker/dockerfile:1

FROM python:3.14-slim

ARG UV_VERSION=0.12.17

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:${PATH}" \
    MCP_TRANSPORT=STREAMABLE_HTTP \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_PATH=/mcp \
    LOG_LEVEL=INFO

WORKDIR /app

RUN pip install --no-cache-dir "uv==${UV_VERSION}"

# Install the locked server dependencies first so this layer remains cached
# when only application source files change. Client and development dependency
# groups are intentionally excluded from the server image.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev --no-editable \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["product-assistant-mcp"]
