FROM python:3.12-slim

WORKDIR /app

# Install uv binary via official installer script
RUN apt-get update && apt-get install -y curl && curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependency specifications
COPY pyproject.toml uv.lock ./

# Sync dependencies using uv
RUN uv sync --frozen --no-cache

# Copy application source files
COPY . .

# Initialize database
RUN uv run python -c "from mcp_server.db_helpers import init_db; init_db()"

EXPOSE 8000

CMD ["uv", "run", "python", "web/app.py"]
