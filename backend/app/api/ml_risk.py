"""
MedIntel AI — ML Risk Estimation API Router.

Exposes REST endpoints for disease risk probability estimation across:
- Diabetes (Pima Indians benchmark)
- Heart Disease (UCI Cleveland benchmark)
- Chronic Kidney Disease (UCI CKD benchmark)

Safety & Governance:
    - Strictly non-diagnostic: Outputs estimated risk probability P(target=1) and educational risk band.
    - Zero disease diagnosis declarations or clinical treatment advice.
    - Mandatory medical disclaimer included on every response.
    - Enforces user verification gate (rejects unverified report-derived data).
    - Rejects incomplete feature sets with INSUFFICIENT_FEATURES (no guessing/imputing).
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ml_risk import (
    DiabetesRiskRequest,
    HeartDiseaseRiskRequest,
    KidneyDiseaseRiskRequest,
    MLStatusResponse,
    RiskPredictionResponse,
)
from app.services.ml_risk_service import ml_risk_service

logger = logging.getLogger("medintel.ml_api")

router = APIRouter(prefix="/api/v1/ml", tags=["Machine Learning Risk Prediction"])


@router.post(
    "/diabetes-risk",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate diabetes risk probability from clinical measurements",
    description=(
        "Evaluates 8 clinical features against the trained Diabetes risk pipeline (Random Forest). "
        "Returns continuous model-estimated risk probability P(Outcome=1) and educational display band. "
        "Enforces user verification and strict missing-feature rejection. "
        "Does NOT provide medical diagnosis or treatment advice."
    ),
)
def estimate_diabetes_risk(
    request: DiabetesRiskRequest,
    db: Session = Depends(get_db),
) -> RiskPredictionResponse:
    """Handle diabetes risk estimation and optional prediction persistence."""
    try:
        return ml_risk_service.predict_diabetes(request, db=db)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in diabetes risk endpoint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during diabetes risk estimation.",
        ) from e


@router.post(
    "/heart-risk",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate heart disease risk probability from clinical measurements",
    description=(
        "Evaluates 13 clinical features against the trained Heart Disease risk pipeline (Logistic Regression). "
        "Returns continuous model-estimated risk probability P(target=1) and educational display band. "
        "Enforces user verification and strict missing-feature rejection. "
        "Does NOT provide medical diagnosis or treatment advice."
    ),
)
def estimate_heart_risk(
    request: HeartDiseaseRiskRequest,
    db: Session = Depends(get_db),
) -> RiskPredictionResponse:
    """Handle heart disease risk estimation and optional prediction persistence."""
    try:
        return ml_risk_service.predict_heart(request, db=db)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in heart risk endpoint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during heart disease risk estimation.",
        ) from e


@router.post(
    "/kidney-risk",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate chronic kidney disease risk probability from clinical measurements",
    description=(
        "Evaluates 24 clinical features against the trained Chronic Kidney Disease risk pipeline (Logistic Regression). "
        "Returns continuous model-estimated risk probability P(classification=1) and educational display band. "
        "Enforces user verification and strict missing-feature rejection. "
        "Does NOT provide medical diagnosis or treatment advice."
    ),
)
def estimate_kidney_risk(
    request: KidneyDiseaseRiskRequest,
    db: Session = Depends(get_db),
) -> RiskPredictionResponse:
    """Handle chronic kidney disease risk estimation and optional prediction persistence."""
    try:
        return ml_risk_service.predict_kidney(request, db=db)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in kidney risk endpoint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during kidney disease risk estimation.",
        ) from e


@router.get(
    "/status",
    response_model=MLStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check availability and integrity of ML risk models",
    description=(
        "Reports availability, candidate model identifiers, and cryptographic integrity verification status "
        "for each trained disease risk estimation pipeline without exposing sensitive file paths."
    ),
)
def get_ml_status() -> MLStatusResponse:
    """Return health and availability status of all ML models."""
    try:
        return ml_risk_service.get_service_status()
    except Exception as e:
        logger.exception("Unexpected error in ML status endpoint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ML service status.",
        ) from e
