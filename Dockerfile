# ==============================================================================
# MedIntel AI — Production Container Dockerfile
# Multi-stage production build for FastAPI Backend, ML Inference & OCR Engine
# ==============================================================================

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies:
# - tesseract-ocr & language packs for printed report OCR
# - curl for health check probing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend and subsystem modules
COPY backend /app/backend
COPY reference /app/reference
COPY ocr /app/ocr
COPY ml /app/ml
COPY database /app/database
COPY deploy /app/deploy

# Ensure repository root and backend are on PYTHONPATH and configure production defaults
ENV PYTHONPATH=/app:/app/backend \
    APP_ENV=production \
    DEBUG=false \
    MEDINTEL_ML_MODELS_DIR=/app/deploy/ml_models \
    DEFAULT_OCR_ENGINE=tesseract \
    PORT=8000

# Create volume/runtime mount points
RUN mkdir -p /app/database /app/ml/models /app/reports

EXPOSE 8000

# Health check probing the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Launch production server via Uvicorn with single worker and dynamic PORT
CMD ["sh", "-c", "uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]

