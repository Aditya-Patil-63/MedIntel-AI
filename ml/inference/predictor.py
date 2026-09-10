"""Inference Engine for MedIntel AI Risk Models.

Phase 7: Predicts model-estimated risk probabilities with strict missing-feature rejection
and non-diagnostic educational categorization.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd

from ml.common.schemas import MANDATORY_ML_DISCLAIMER, ModelRiskResult
from ml.diabetes.features import FEATURES as DIABETES_FEATURES, validate_input_features as validate_diabetes
from ml.heart_disease.features import FEATURES as HEART_FEATURES, validate_input_features as validate_heart
from ml.kidney_disease.features import FEATURES as CKD_FEATURES, validate_input_features as validate_ckd


FEATURE_REGISTRY = {
    "diabetes": (DIABETES_FEATURES, validate_diabetes),
    "heart_disease": (HEART_FEATURES, validate_heart),
    "kidney_disease": (CKD_FEATURES, validate_ckd),
}


class RiskPredictor:
    """Loads a serialized pipeline and metadata for safe, non-diagnostic risk inference."""

    def __init__(
        self,
        condition: str,
        models_base_dir: Optional[str] = None,
        threshold: float = 0.50,
    ) -> None:
        """Initialize the RiskPredictor for a specific condition.

        Args:
            condition: 'diabetes', 'heart_disease', or 'kidney_disease'
            models_base_dir: Base directory containing ml_models/{condition}/
            threshold: Decision threshold (default 0.50)
        """
        if condition not in FEATURE_REGISTRY:
            raise ValueError(f"Unknown condition '{condition}'. Must be one of: {list(FEATURE_REGISTRY.keys())}")

        self.condition = condition
        self.threshold = threshold
        self.required_features, self.validator_func = FEATURE_REGISTRY[condition]

        # Resolve artifact path
        base_dir = Path(models_base_dir or os.environ.get("MEDINTEL_DATA_DIR", "D:\\MedIntel-Datasets"))
        self.model_dir = base_dir / "ml_models" / condition

        self.pipeline = None
        self.metadata: Dict[str, Any] = {}
        self.is_loaded = False

    def load(self, verify_sha256: bool = True) -> None:
        """Load serialized pipeline and metadata from disk.

        Args:
            verify_sha256: If True, validates pipeline file SHA-256 against metadata.
        """
        pipeline_path = self.model_dir / "pipeline.joblib"
        metadata_path = self.model_dir / "model_metadata.json"

        if not pipeline_path.exists():
            raise FileNotFoundError(
                f"Model pipeline artifact not found at: {pipeline_path}. "
                "Ensure training has been executed."
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Model metadata not found at: {metadata_path}."
            )

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        if verify_sha256 and "pipeline_sha256" in self.metadata:
            hasher = hashlib.sha256()
            with open(pipeline_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            actual_sha = hasher.hexdigest()
            expected_sha = self.metadata["pipeline_sha256"]
            if actual_sha != expected_sha:
                raise ValueError(
                    f"Integrity check failed for {pipeline_path}! "
                    f"Expected SHA-256 {expected_sha}, got {actual_sha}."
                )

        self.pipeline = joblib.load(pipeline_path)
        self.is_loaded = True

    def predict_risk(self, input_features: Dict[str, Any]) -> ModelRiskResult:
        """Perform risk estimation with strict input validation.

        Args:
            input_features: Dictionary of feature key-value pairs.

        Returns:
            ModelRiskResult schema.
        """
        if not self.is_loaded:
            raise RuntimeError(f"RiskPredictor for {self.condition} has not loaded artifacts. Call .load() first.")

        # 1. Validate feature presence
        is_valid, missing = self.validator_func(input_features)
        supplied_count = len([k for k in self.required_features if k in input_features and input_features[k] is not None])
        required_count = len(self.required_features)

        if not is_valid:
            return ModelRiskResult(
                model_name=self.metadata.get("candidate_name", f"{self.condition}_model"),
                condition=self.condition,
                status="INSUFFICIENT_FEATURES",
                risk_probability=None,
                risk_index=None,
                threshold_used=self.threshold,
                binary_prediction=None,
                missing_features=missing,
                supplied_features_count=supplied_count,
                required_features_count=required_count,
                disclaimer=MANDATORY_ML_DISCLAIMER,
                model_version=self.metadata.get("timestamp", "unknown"),
            )

        # 2. Build single-row DataFrame in the exact feature order
        row_data = {feat: [input_features[feat]] for feat in self.required_features}
        df_input = pd.DataFrame(row_data)

        # 3. Predict probability
        if hasattr(self.pipeline, "predict_proba"):
            probs = self.pipeline.predict_proba(df_input)
            prob_positive = float(probs[0, 1])
        elif hasattr(self.pipeline, "decision_function"):
            scores = self.pipeline.decision_function(df_input)
            prob_positive = float(1.0 / (1.0 + np.exp(-scores[0])))
        else:
            raise AttributeError("Pipeline does not support probability estimation.")

        # Sanity check probability
        if np.isnan(prob_positive) or np.isinf(prob_positive):
            raise ValueError("Model generated invalid NaN or Inf probability.")

        prob_positive = max(0.0, min(1.0, prob_positive))

        # 4. Determine qualitative non-diagnostic risk index
        if prob_positive < 0.30:
            risk_index = "LOW"
        elif prob_positive < 0.70:
            risk_index = "MODERATE"
        else:
            risk_index = "ELEVATED"

        binary_pred = int(prob_positive >= self.threshold)

        return ModelRiskResult(
            model_name=self.metadata.get("candidate_name", f"{self.condition}_model"),
            condition=self.condition,
            status="SUCCESS",
            risk_probability=round(prob_positive, 4),
            risk_index=risk_index,
            threshold_used=self.threshold,
            binary_prediction=binary_pred,
            missing_features=[],
            supplied_features_count=supplied_count,
            required_features_count=required_count,
            disclaimer=MANDATORY_ML_DISCLAIMER,
            model_version=self.metadata.get("timestamp", "unknown"),
        )
