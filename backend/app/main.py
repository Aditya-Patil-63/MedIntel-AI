"""
MedIntel AI — FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance.
Phase 2: Only the health-check endpoint is active.
"""

from fastapi import FastAPI

from app.api.extraction import router as extraction_router
from app.api.health import router as health_router
from app.api.ml_risk import router as ml_risk_router
from app.api.reference import router as reference_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured application instance.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Intelligent Medical Report Analyzer Using Machine Learning "
            "and Generative AI. This is an academic project — NOT a "
            "certified medical device."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Register routers
    application.include_router(health_router)
    application.include_router(extraction_router)
    application.include_router(reference_router)
    application.include_router(ml_risk_router)

    return application


app = create_app()
