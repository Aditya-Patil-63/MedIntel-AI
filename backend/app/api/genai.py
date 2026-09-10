"""
MedIntel AI — GenAI Explanation API Router.

Exposes REST endpoints for generating patient-friendly educational explanations
and multilingual translations of verified medical reports.

Endpoints:
    - POST /api/v1/genai/explain: Generate explanation from verified findings
    - GET /api/v1/genai/status: Check GenAI provider health and configuration

Safety & Security Guarantees:
    - Non-diagnostic: Explains findings educationally without disease assertions.
    - Non-prescriptive: Zero medication, dosage, or treatment advice.
    - Mandatory medical disclaimer on every response.
    - Enforces user verification gate (rejects unverified report data).
    - Preserves clinical invariance across English, Hindi, Marathi, and Gujarati.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.genai import (
    GenAIExplainRequest,
    GenAIExplainResponse,
    GenAIStatusResponse,
)
from app.services.genai_service import genai_service

logger = logging.getLogger("medintel.genai_api")

router = APIRouter(prefix="/api/v1/genai", tags=["Generative AI Explanation"])


@router.post(
    "/explain",
    response_model=GenAIExplainResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate plain-language explanation and translation of verified medical findings",
    description=(
        "Translates verified laboratory measurements and ML disease risk probabilities into "
        "clear, patient-friendly educational explanations. Supports English, Hindi, Marathi, "
        "and Gujarati. Enforces mandatory user verification before generation and includes "
        "a non-diagnostic safety disclaimer. Does NOT formulate medical diagnoses or prescribe treatments."
    ),
)
async def explain_findings(
    request: GenAIExplainRequest,
    db: Session = Depends(get_db),
) -> GenAIExplainResponse:
    """Generate structured educational explanation from verified clinical findings."""
    try:
        return await genai_service.explain_findings(request, db=db)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in /explain endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the explanation.",
        ) from exc


@router.get(
    "/status",
    response_model=GenAIStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect GenAI provider status and operational configuration",
    description=(
        "Returns active provider details, model configuration, and operational mode. "
        "Does NOT expose API keys, internal credentials, or server filesystem paths."
    ),
)
async def get_genai_status() -> GenAIStatusResponse:
    """Check health and availability of the GenAI explanation provider."""
    try:
        return await genai_service.get_service_status()
    except Exception as exc:
        logger.exception("Unexpected error in /status endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GenAI service status.",
        ) from exc
