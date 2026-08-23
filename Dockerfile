# ==============================================================================
# Multi-Stage Production Dockerfile: Cornerstone Realty Group MCP Platform
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React 18/19 Single Page Application (SPA)
# ------------------------------------------------------------------------------
FROM node:22-alpine AS frontend-builder
WORKDIR /app/platform

# Enable corepack and activate pnpm 9
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate

# Install frontend dependencies with layer caching
COPY platform/package.json platform/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install

# Copy platform source and build production bundle
COPY platform/ ./
RUN pnpm build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Backend Service
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

WORKDIR /app

# Install uv package manager and curl for container health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install Python dependencies using uv
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-cache

# Copy application source code
COPY . .

# Copy compiled React SPA assets from Stage 1 into web/dist
COPY --from=frontend-builder /app/web/dist ./web/dist

EXPOSE 8000

# Start FastAPI application via Uvicorn
CMD ["uv", "run", "python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
