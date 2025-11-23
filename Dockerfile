# Multi-stage Dockerfile for pickle-reactor
# Uses uv for fast, reproducible dependency installation

# Builder stage: Install dependencies and compile bytecode
FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim AS builder

# Set working directory
WORKDIR /app

# Copy dependency specifications first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies without the project itself
# This layer is cached unless dependencies change
RUN uv sync --locked --no-install-project --compile-bytecode

# Copy the entire project
COPY . .

# Install the project in non-editable mode with bytecode compilation
# --no-editable ensures no dependency on source code at runtime
RUN uv sync --locked --no-editable --compile-bytecode

# Runtime stage: Minimal image with only the virtual environment
FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim AS runtime

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code (needed for pages, server, client, shared, static)
COPY --from=builder /app/pages /app/pages
COPY --from=builder /app/server /app/server
COPY --from=builder /app/client /app/client
COPY --from=builder /app/shared /app/shared
COPY --from=builder /app/static /app/static
COPY --from=builder /app/src /app/src

# Set up Python path to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose port for uvicorn
EXPOSE 8000

# Run the application with uvicorn
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
