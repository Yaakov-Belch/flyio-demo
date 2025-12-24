# Use Python 3.14 slim base image
FROM python:3.14-slim

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv (without lockfile, create virtual env)
RUN uv sync --no-dev

# Copy application code
COPY src/ ./src/

# Expose port (Fly.io uses PORT env variable, defaults to 8080)
ENV PORT=8080
EXPOSE 8080

# Run the FastMCP server with uvicorn
# The PORT environment variable will be set by Fly.io
CMD ["uv", "run", "uvicorn", "flyio_demo.code_insight.mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]
