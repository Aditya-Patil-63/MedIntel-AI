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
# - libgl1 & libglib2.0-0 for OpenCV / image processing
# - curl for health check probing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    libgl1 \
    libglib2.0-0 \
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

# Ensure repository root and backend are on PYTHONPATH
ENV PYTHONPATH=/app:/app/backend \
    MEDINTEL_ENV=production \
    DEFAULT_OCR_ENGINE=tesseract \
    PORT=8000

# Create volume mount points for database and models
RUN mkdir -p /app/database /app/ml/models /app/reports

EXPOSE 8000

# Health check probing the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch production server via Uvicorn
CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
