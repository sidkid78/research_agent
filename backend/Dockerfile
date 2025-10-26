# --- Stage 1: Build Stage ---
# Use a slim, modern Python base image
FROM python:3.11-slim-bookworm as builder

WORKDIR /app

# Install uv (our fast package installer)
RUN pip install uv

# Copy the file that defines your dependencies
COPY pyproject.toml .

# Create the virtual environment
RUN uv venv

# Set the path to use the new venv
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies using uv sync
# This reads pyproject.toml and installs everything
# We also cache the downloads to speed up future builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# --- Stage 2: Final Stage ---
# Use a fresh, minimal image for the final product
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy your application code
# This copies everything in the 'app' directory
COPY ./app /app/app

# Set the environment variable for the Python path
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 8000
EXPOSE 8000

# Health check
# Note: We don't need 'curl' anymore. We can ask Python to do it!
# This removes the need for 'apt-get install curl'
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost', 8000); conn.request('GET', '/health'); exit(0 if conn.getresponse().status == 200 else 1)"

# Run with uvicorn
# Removed --reload, which is not for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]