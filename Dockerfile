# Start with slim Python image
FROM python:3.13.2-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/


# Set working directory
WORKDIR /app


# Copy dependency files first (better layer caching)
COPY pyproject.toml .python-version uv.lock ./

# Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY pipeline.py .

ENTRYPOINT [ "python", "pipeline.py" ]