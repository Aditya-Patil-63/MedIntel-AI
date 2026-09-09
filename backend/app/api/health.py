"""
MedIntel AI — Health Check Endpoint.

Provides a simple health-check route to verify that the backend
is running and responsive. This is the only endpoint in Phase 2.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict:
    """Check that the backend service is running.

    Returns:
        dict: Status information including application name,
              current status, environment, and server timestamp.
    """
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
