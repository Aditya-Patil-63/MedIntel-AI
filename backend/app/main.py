"""
MedIntel AI — FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance.
Phase 2: Only the health-check endpoint is active.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.extraction import router as extraction_router
from app.api.genai import router as genai_router
from app.api.health import router as health_router
from app.api.ml_risk import router as ml_risk_router
from app.api.prescriptions import router as prescriptions_router
from app.api.reference import router as reference_router
from app.api.reports import router as reports_router
from app.core.config import settings
from app.db.session import create_tables


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured application instance.
    """
    # Ensure all ORM tables exist in SQLite
    try:
        create_tables()
    except Exception as e:
        # Don't crash if already created
        pass

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

    # Enable CORS for mobile, desktop, and web clients
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(reports_router)
    application.include_router(extraction_router)
    application.include_router(reference_router)
    application.include_router(ml_risk_router)
    application.include_router(genai_router)
    application.include_router(prescriptions_router)

    return application


app = create_app()
