"""
MedIntel AI — ML Risk Service Layer.

Orchestrates machine learning risk model loading, caching, inference,
user verification checks, and optional database persistence into SQLite.

Safety Guarantees:
    - Never mutates or retrains external model artifacts.
    - Caches loaded pipelines in memory (loads once).
    - Verifies artifact SHA-256 against metadata before serving requests.
    - Enforces user verification gate (rejects unverified report inputs).
    - Rejects incomplete feature sets with INSUFFICIENT_FEATURES (zero silent imputation).
    - Preserves strictly non-diagnostic educational terminology.
"""

import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Ensure repo root is on sys.path so ml module is accessible
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.config import settings
from app.models.models import Prediction, Report
from app.schemas.ml_risk import (
    DiabetesRiskRequest,
    HeartDiseaseRiskRequest,
    KidneyDiseaseRiskRequest,
    MLStatusResponse,
    ModelStatusInfo,
    RiskPredictionResponse,
)
from ml.common.schemas import MANDATORY_ML_DISCLAIMER
from ml.inference.predictor import RiskPredictor

logger = logging.getLogger("medintel.ml_service")

SUPPORTED_CONDITIONS = ["diabetes", "heart_disease", "kidney_disease"]


class MLRiskService:
    """Service layer managing trained ML risk estimation models."""

    def __init__(self, models_dir: Optional[str] = None) -> None:
        """Initialize service with models base directory."""
        self.models_dir = Path(models_dir or settings.MEDINTEL_ML_MODELS_DIR)
        self._predictors: Dict[str, RiskPredictor] = {}

    def get_predictor(self, condition: str) -> RiskPredictor:
        """Get or lazy-load the RiskPredictor for a condition with SHA-256 verification.

        Args:
            condition: 'diabetes', 'heart_disease', or 'kidney_disease'

        Returns:
            Loaded and verified RiskPredictor instance.

        Raises:
            HTTPException: 500 if artifact is missing, unreadable, or corrupted.
        """
        if condition in self._predictors:
            return self._predictors[condition]

        try:
            predictor = RiskPredictor(
                condition=condition,
                models_base_dir=str(self.models_dir),
            )
            predictor.load(verify_sha256=True)
            self._predictors[condition] = predictor
            logger.info("Successfully loaded and verified ML artifact for %s.", condition)
            return predictor
        except FileNotFoundError as e:
            logger.error("ML model artifact not found for %s: %s", condition, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model artifact for '{condition}' is not configured or missing on the server.",
            ) from e
        except ValueError as e:
            logger.critical("ML model integrity verification failed for %s: %s", condition, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model artifact for '{condition}' failed cryptographic integrity verification.",
            ) from e
        except Exception as e:
            logger.exception("Unexpected error loading ML model for %s: %s", condition, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while loading the '{condition}' risk model.",
            ) from e

    def _execute_risk_estimation(
        self,
        condition: str,
        feature_dict: Dict[str, Any],
        is_user_verified: bool,
        report_id: Optional[int],
        db: Optional[Session],
    ) -> RiskPredictionResponse:
        """Internal worker executing verification checks, feature validation, inference, and persistence."""
        predictor = self.get_predictor(condition)
        required_features = predictor.required_features
        total_required = len(required_features)

        # 1. User verification safety gate
        if not is_user_verified:
            supplied_count = len([k for k in required_features if k in feature_dict and feature_dict[k] is not None])
            return RiskPredictionResponse(
                condition=condition,
                status="VERIFICATION_REQUIRED",
                risk_probability=None,
                risk_band=None,
                model_name=predictor.metadata.get("candidate_name"),
                model_version=predictor.metadata.get("timestamp"),
                supplied_features_count=supplied_count,
                required_features_count=total_required,
                missing_features=[],
                disclaimer=MANDATORY_ML_DISCLAIMER,
                persisted_prediction_id=None,
            )

        # 2. Check for missing required features
        is_valid, missing = predictor.validator_func(feature_dict)
        supplied_count = len([k for k in required_features if k in feature_dict and feature_dict[k] is not None])

        if not is_valid:
            return RiskPredictionResponse(
                condition=condition,
                status="INSUFFICIENT_FEATURES",
                risk_probability=None,
                risk_band=None,
                model_name=predictor.metadata.get("candidate_name"),
                model_version=predictor.metadata.get("timestamp"),
                supplied_features_count=supplied_count,
                required_features_count=total_required,
                missing_features=missing,
                disclaimer=MANDATORY_ML_DISCLAIMER,
                persisted_prediction_id=None,
            )

        # 3. Perform ML inference
        try:
            result = predictor.predict_risk(feature_dict)
        except Exception as e:
            logger.exception("Inference failed for condition %s: %s", condition, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during {condition} risk estimation.",
            ) from e

        # 4. Optional Database Persistence
        persisted_id: Optional[int] = None
        if report_id is not None and db is not None:
            report = db.query(Report).filter(Report.id == report_id).first()
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report with id {report_id} not found.",
                )

            # Map display band to DB enum ('low', 'moderate', 'high')
            band_map = {"LOW": "low", "MODERATE": "moderate", "ELEVATED": "high"}
            db_level = band_map.get(result.risk_index, "moderate")

            prediction_record = Prediction(
                report_id=report_id,
                condition=condition,
                risk_score=result.risk_probability,
                risk_level=db_level,
                model_name=result.model_name,
                model_version=result.model_version,
                disclaimer=MANDATORY_ML_DISCLAIMER,
            )
            db.add(prediction_record)
            db.commit()
            db.refresh(prediction_record)
            persisted_id = prediction_record.id

        return RiskPredictionResponse(
            condition=condition,
            status="OK",
            risk_probability=result.risk_probability,
            risk_band=result.risk_index,
            model_name=result.model_name,
            model_version=result.model_version,
            supplied_features_count=result.supplied_features_count,
            required_features_count=result.required_features_count,
            missing_features=[],
            disclaimer=MANDATORY_ML_DISCLAIMER,
            persisted_prediction_id=persisted_id,
        )

    def predict_diabetes(
        self,
        request: DiabetesRiskRequest,
        db: Optional[Session] = None,
    ) -> RiskPredictionResponse:
        """Estimate diabetes risk from clinical features."""
        features = request.model_dump(exclude={"is_user_verified", "report_id"})
        return self._execute_risk_estimation(
            condition="diabetes",
            feature_dict=features,
            is_user_verified=request.is_user_verified,
            report_id=request.report_id,
            db=db,
        )

    def predict_heart(
        self,
        request: HeartDiseaseRiskRequest,
        db: Optional[Session] = None,
    ) -> RiskPredictionResponse:
        """Estimate heart disease risk from clinical features."""
        features = request.model_dump(exclude={"is_user_verified", "report_id"})
        return self._execute_risk_estimation(
            condition="heart_disease",
            feature_dict=features,
            is_user_verified=request.is_user_verified,
            report_id=request.report_id,
            db=db,
        )

    def predict_kidney(
        self,
        request: KidneyDiseaseRiskRequest,
        db: Optional[Session] = None,
    ) -> RiskPredictionResponse:
        """Estimate chronic kidney disease risk from clinical features."""
        features = request.model_dump(exclude={"is_user_verified", "report_id"})
        return self._execute_risk_estimation(
            condition="kidney_disease",
            feature_dict=features,
            is_user_verified=request.is_user_verified,
            report_id=request.report_id,
            db=db,
        )

    def get_service_status(self) -> MLStatusResponse:
        """Inspect and report the health and availability of all condition models."""
        models_status = {}
        all_available = True

        for cond in SUPPORTED_CONDITIONS:
            try:
                pred = self.get_predictor(cond)
                models_status[cond] = ModelStatusInfo(
                    available=True,
                    model_name=pred.metadata.get("candidate_name"),
                    model_type=pred.metadata.get("model_type"),
                    integrity_verified=True,
                    version=pred.metadata.get("timestamp"),
                )
            except Exception:
                all_available = False
                models_status[cond] = ModelStatusInfo(
                    available=False,
                    model_name=None,
                    model_type=None,
                    integrity_verified=False,
                    version=None,
                )

        overall_status = "OK" if all_available else ("DEGRADED" if any(m.available for m in models_status.values()) else "ERROR")
        return MLStatusResponse(status=overall_status, models=models_status)


ml_risk_service = MLRiskService()
