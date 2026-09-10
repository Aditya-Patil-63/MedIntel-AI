"""
MedIntel AI — ML Schemas & Data Structures.

Phase 7: Pydantic schemas for risk estimation inputs, outputs, and metrics.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


MANDATORY_ML_DISCLAIMER = (
    "This estimated risk score is an educational indicator derived from historical research datasets. "
    "It is NOT a medical diagnosis, clinical prognosis, or treatment recommendation. "
    "Please consult a qualified healthcare professional for comprehensive medical evaluation."
)


class ModelRiskResult(BaseModel):
    """Output schema for an individual disease risk prediction."""

    model_name: str = Field(..., description="Unique model identifier")
    condition: str = Field(..., description="Target medical condition (diabetes, heart_disease, kidney_disease)")
    status: str = Field(..., description="SUCCESS, INSUFFICIENT_FEATURES, or ERROR")
    risk_probability: Optional[float] = Field(None, description="Model-estimated risk probability P(target=1)")
    risk_index: Optional[str] = Field(None, description="Qualitative category: LOW, MODERATE, ELEVATED")
    threshold_used: float = Field(default=0.50, description="Decision threshold used for binary classification")
    binary_prediction: Optional[int] = Field(None, description="Binary prediction at threshold (0 or 1)")
    missing_features: List[str] = Field(default_factory=list, description="List of required features that were not supplied")
    supplied_features_count: int = Field(default=0, description="Number of valid features supplied")
    required_features_count: int = Field(default=0, description="Total features required by model")
    disclaimer: str = Field(default=MANDATORY_ML_DISCLAIMER, description="Mandatory medical safety disclaimer")
    model_version: Optional[str] = Field(None, description="Trained model artifact version")


class EvaluationMetrics(BaseModel):
    """Comprehensive evaluation metrics for binary classification & risk estimation."""

    accuracy: float
    precision: float
    recall: float  # Sensitivity
    specificity: float  # TN / (TN + FP)
    f1: float
    roc_auc: float
    pr_auc: float
    brier_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    total_samples: int
    threshold: float = 0.50
