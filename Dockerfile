# Remote Job Application Copilot — production container
# Multi-stage build: Node builds the React frontend, Python ships it.
# This image is INTERNAL tooling (developer/CI use only). It is not
# designed to expose the backend to the public internet.

# ----------------------------------------------------------------------------
# Stage 1 — build the React + Three.js frontend
# ----------------------------------------------------------------------------
FROM node:20-bookworm-slim AS frontend-build
WORKDIR /work
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# ----------------------------------------------------------------------------
# Stage 2 — Python runtime with the built frontend bundled in
# ----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    JOBFINDER_HOST=0.0.0.0 \
    JOBFINDER_PORT=8000

# OS deps: git for rendercv / weasyprint-less tooling, build-essential for
# any wheel that needs to compile, libxml/libxslt for lxml, libssl for fernet.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libxml2-dev \
        libxslt1-dev \
        libssl-dev \
        ca-certificates \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer cache).
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the application.
COPY . /app
COPY --from=frontend-build /work/dist /app/frontend_dist

# Run as a non-root user. UID 65532 matches distroless convention.
RUN useradd --system --shell /usr/sbin/nologin --uid 65532 --create-home jobfinder \
    && mkdir -p /app/data /app/data/profiles /app/data/outputs /app/data/bot_profile \
    && chown -R jobfinder:jobfinder /app
USER jobfinder

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${JOBFINDER_PORT}/health || exit 1

# FastAPI runs the API; Streamlit is launched separately by `app.py` for the
# native UI (the React build inside /app/frontend_dist is mounted by
# server.py::serve_frontend()).
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
