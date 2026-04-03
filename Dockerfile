# =============================================================================
# CareerWeave — Dockerfile
# Target: Google Cloud Run (fully managed, serverless)
# Base:   Python 3.11 slim (small image = faster cold starts on Cloud Run)
# =============================================================================

FROM python:3.11-slim

# ── System metadata ───────────────────────────────────────────────────────────
LABEL maintainer="CareerWeave Team"
LABEL description="CareerWeave Multi-Agent Job Orchestrator — GEN AI APAC Hackathon"

# ── Prevent Python from writing .pyc files and buffering stdout/stderr ────────
# PYTHONDONTWRITEBYTECODE → no __pycache__ clutter in the image
# PYTHONUNBUFFERED        → logs appear in Cloud Run console in real-time
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Cloud Run injects PORT at runtime (default 8080).
#    Streamlit must bind to this port.
ENV PORT=8080

# ── Working directory inside the container ────────────────────────────────────
WORKDIR /app

# ── Install OS-level dependencies ─────────────────────────────────────────────
# build-essential: needed by some Python C-extension packages
# curl:            used by the health-check probe
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Copy and install Python dependencies FIRST (layer caching) ────────────────
# Docker caches this layer until requirements.txt changes, speeding rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy application source ───────────────────────────────────────────────────
COPY . .

# ── Streamlit config is baked in via .streamlit/config.toml (see that file).
#    Expose the port for documentation purposes (Cloud Run ignores EXPOSE).
EXPOSE 8080

# ── Health-check so Cloud Run knows the container is healthy ──────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# ── Entrypoint: run Streamlit bound to Cloud Run's dynamic PORT ───────────────
CMD streamlit run app.py \
        --server.port=$PORT \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --server.enableCORS=false \
        --server.enableXsrfProtection=false \
        --browser.gatherUsageStats=false
