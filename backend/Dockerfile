# ===========================================================================
# Lorri Backend — FastAPI Application Container
#
# Multi-purpose Dockerfile for both local development (via docker-compose)
# and production deployment (via Render). Uses Python 3.11 slim to keep
# the image small while still supporting all our scientific dependencies
# (scikit-learn, numpy, networkx).
#
# Build context should be the REPO ROOT (not backend/), so that the
# Python import paths (backend.app.models, etc.) resolve correctly.
# docker-compose.yml handles this automatically.
# ===========================================================================

FROM python:3.11-slim

# -- System dependencies --
# gcc and python3-dev are needed for compiling some pip packages
# (e.g. scikit-learn wheels on certain platforms). curl is for the
# Docker health check. We clean up the apt cache to keep the image small.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev curl && \
    rm -rf /var/lib/apt/lists/*

# -- Working directory --
# Set to /app (repo root inside container). The full path to our code
# becomes /app/backend/app/main.py, which matches the import structure
# backend.app.main that we use everywhere.
WORKDIR /app

# -- Install Python dependencies --
# Copy requirements first (before the rest of the code) so Docker
# can cache this layer. If requirements.txt hasn't changed, pip install
# is skipped on rebuilds — saves a lot of time during development.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# -- Copy application code --
# Copy the entire backend directory into the container.
# We copy at the end so code changes don't bust the pip cache.
COPY backend/ backend/

# -- Python path --
# This is critical. Our code uses imports like `from backend.app.models import ...`
# which means Python needs to find `backend` as a top-level package.
# Setting PYTHONPATH to /app makes /app/backend/ discoverable as `backend`.
ENV PYTHONPATH=/app

# -- Expose the API port --
EXPOSE 8000

# -- Health check --
# Docker (and Render) will periodically hit this endpoint to verify
# the container is alive. If it fails 3 times, the container is restarted.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# -- Start the server --
# host 0.0.0.0 makes it accessible outside the container.
# workers=1 for dev; increase for production (or let Render handle scaling).
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]