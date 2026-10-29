"""
MedIntel AI — FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance.
Phase 2: Only the health-check endpoint is active.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.extraction import router as extraction_router
from app.api.genai import router as genai_router
from app.api.health import router as health_router
from app.api.ml_risk import router as ml_risk_router
from app.api.prescriptions import router as prescriptions_router
from app.api.reference import router as reference_router
from app.api.reports import history_router, router as reports_router
from app.core.config import settings
from app.db.session import create_tables

logger = logging.getLogger("medintel.main")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured application instance.
    """
    # Ensure all ORM tables exist in SQLite or Postgres
    try:
        create_tables()
    except Exception as e:
        logger.warning("Startup table creation deferred: %s", type(e).__name__)

    # GenAI Provider fallback & startup logging
    active_provider = settings.GENAI_PROVIDER.lower()
    if active_provider == "gemini":
        if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
            logger.warning(
                "GENAI_PROVIDER is set to 'gemini' but GEMINI_API_KEY is not configured. "
                "Falling back to mock provider for medical explanation safety."
            )
            settings.GENAI_PROVIDER = "mock"
            active_provider = "mock"
    logger.info("Active GenAI Explanation Provider: %s", active_provider)

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

    # Configure CORS for mobile, desktop, and web clients
    cors_origins_str = (settings.CORS_ORIGINS or "").strip()
    if cors_origins_str:
        allowed_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]
        application.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Register routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(reports_router)
    application.include_router(history_router)
    application.include_router(extraction_router)
    application.include_router(reference_router)
    application.include_router(ml_risk_router)
    application.include_router(genai_router)
    application.include_router(prescriptions_router)

    return application


app = create_app()
