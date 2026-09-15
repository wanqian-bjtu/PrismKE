FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --extra neo4j --extra web --no-install-project

COPY src ./src
COPY configs ./configs
RUN uv sync --frozen --no-dev --extra neo4j --extra web

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "prismke", "serve", "--host", "0.0.0.0"]
