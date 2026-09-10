"""
MedIntel AI — Reference Analysis API Router.

Exposes REST endpoints for deterministic medical reference range classification
and document text parsing.

Endpoints:
    - POST /api/v1/reference/analyze
    - POST /api/v1/reference/parse-and-analyze

Safety Guarantees:
    - Strictly non-diagnostic: Outputs LOW, NORMAL, HIGH, CRITICAL.
    - Zero disease predictions or treatment advice.
    - Mandatory medical disclaimer on every response.
    - Enforces user verification gate (distinguishes raw OCR from user-verified data).
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reference import (
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    ParseAndAnalyzeRequest,
    ParseAndAnalyzeResponse,
)
from app.services.reference_service import reference_service

logger = logging.getLogger("medintel.reference_api")

router = APIRouter(prefix="/api/v1/reference", tags=["Medical Reference Analysis"])


@router.post(
    "/analyze",
    response_model=BatchAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Deterministic reference range analysis of structured measurements",
    description=(
        "Evaluates one or more clinical measurements against authoritative medical reference intervals. "
        "Outputs deterministic classifications: LOW, NORMAL, HIGH, CRITICAL, or structured non-classifiable "
        "statuses (e.g., UNIT_MISMATCH, REFERENCE_NOT_AVAILABLE). This endpoint strictly performs "
        "reference-interval comparison and does NOT provide medical diagnoses or treatment recommendations."
    ),
)
def analyze_measurements(
    request: BatchAnalysisRequest,
    db: Session = Depends(get_db),
) -> BatchAnalysisResponse:
    """
    Handle batch measurement analysis and optional database persistence.
    """
    try:
        return reference_service.analyze_batch(request, db=db)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in reference analysis endpoint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during reference range analysis.",
        ) from e


@router.post(
    "/parse-and-analyze",
    response_model=ParseAndAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse document text and evaluate extracted medical measurements",
    description=(
        "Deterministically extracts candidate medical measurements from unstructured document or OCR text "
        "and evaluates them against reference intervals. Distinguishes patient measurements from printed "
        "reference ranges. Enforces user verification safety gate (extractions are marked unverified by default). "
        "Does NOT provide medical diagnoses or clinical treatment advice."
    ),
)
def parse_and_analyze_text(
    request: ParseAndAnalyzeRequest,
    db: Session = Depends(get_db),
) -> ParseAndAnalyzeResponse:
    """
    Handle raw text parsing and downstream reference analysis.
    """
    try:
        return reference_service.parse_and_analyze_text(request, db=db)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in parse-and-analyze endpoint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during medical text parsing and analysis.",
        ) from e
