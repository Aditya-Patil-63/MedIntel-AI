"""
MedIntel AI — ML Risk Prediction Schemas.

Pydantic request and response models for machine learning risk estimation.
Enforces non-diagnostic semantics, educational risk bands, strict feature
validation, and user verification safety gates.
"""

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from ml.common.schemas import MANDATORY_ML_DISCLAIMER


# ---------------------------------------------------------------------------
# Base Request Validator for numeric NaN / Inf rejection
# ---------------------------------------------------------------------------

def validate_finite_numeric(v: Optional[float]) -> Optional[float]:
    """Ensure numeric values are finite (no NaN or Inf)."""
    if v is not None:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Feature value must be a finite number (NaN and Inf are not allowed).")
    return v


# ---------------------------------------------------------------------------
# Individual Condition Request Models
# ---------------------------------------------------------------------------

class DiabetesRiskRequest(BaseModel):
    """Input features for Diabetes risk estimation (Pima Indians benchmark)."""

    Pregnancies: Optional[float] = Field(None, description="Number of pregnancies")
    Glucose: Optional[float] = Field(None, description="Plasma glucose concentration (mg/dL)")
    BloodPressure: Optional[float] = Field(None, description="Diastolic blood pressure (mm Hg)")
    SkinThickness: Optional[float] = Field(None, description="Triceps skin fold thickness (mm)")
    Insulin: Optional[float] = Field(None, description="2-hour serum insulin (mu U/ml)")
    BMI: Optional[float] = Field(None, description="Body mass index (weight in kg / height in m²)")
    DiabetesPedigreeFunction: Optional[float] = Field(None, description="Diabetes pedigree function score")
    Age: Optional[float] = Field(None, description="Age in years")

    is_user_verified: bool = Field(
        True,
        description="Whether values have been verified by the user. False triggers safety hold.",
    )
    report_id: Optional[int] = Field(
        None,
        description="Optional Report ID for audit database persistence",
    )

    @field_validator(
        "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
        "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
        mode="before"
    )
    @classmethod
    def check_finite(cls, v: Any) -> Any:
        if v is None:
            return None
        try:
            val = float(v)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Value must be a valid number: {v}") from exc
        return validate_finite_numeric(val)


class HeartDiseaseRiskRequest(BaseModel):
    """Input features for Heart Disease risk estimation (UCI Cleveland benchmark)."""

    age: Optional[float] = Field(None, description="Age in years")
    sex: Optional[float] = Field(None, description="Sex (1 = male, 0 = female)")
    cp: Optional[float] = Field(None, description="Chest pain type (1, 2, 3, or 4)")
    trestbps: Optional[float] = Field(None, description="Resting blood pressure (mm Hg)")
    chol: Optional[float] = Field(None, description="Serum cholesterol (mg/dl)")
    fbs: Optional[float] = Field(None, description="Fasting blood sugar > 120 mg/dl (1 = true, 0 = false)")
    restecg: Optional[float] = Field(None, description="Resting ECG results (0, 1, or 2)")
    thalach: Optional[float] = Field(None, description="Maximum heart rate achieved")
    exang: Optional[float] = Field(None, description="Exercise-induced angina (1 = yes, 0 = no)")
    oldpeak: Optional[float] = Field(None, description="ST depression induced by exercise")
    slope: Optional[float] = Field(None, description="Slope of peak exercise ST segment (1, 2, or 3)")
    ca: Optional[float] = Field(None, description="Major vessels colored by fluoroscopy (0–3)")
    thal: Optional[float] = Field(None, description="Thalassemia (3 = normal, 6 = fixed, 7 = reversible)")

    is_user_verified: bool = Field(
        True,
        description="Whether values have been verified by the user. False triggers safety hold.",
    )
    report_id: Optional[int] = Field(
        None,
        description="Optional Report ID for audit database persistence",
    )

    @field_validator(
        "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
        "thalach", "exang", "oldpeak", "slope", "ca", "thal",
        mode="before"
    )
    @classmethod
    def check_finite(cls, v: Any) -> Any:
        if v is None:
            return None
        try:
            val = float(v)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Value must be a valid number: {v}") from exc
        return validate_finite_numeric(val)


class KidneyDiseaseRiskRequest(BaseModel):
    """Input features for Chronic Kidney Disease risk estimation (UCI CKD benchmark)."""

    # 14 Numerical Features
    age: Optional[float] = Field(None, description="Age in years")
    bp: Optional[float] = Field(None, description="Blood pressure (mm Hg)")
    sg: Optional[float] = Field(None, description="Specific gravity")
    al: Optional[float] = Field(None, description="Albumin (0 to 5)")
    su: Optional[float] = Field(None, description="Sugar (0 to 5)")
    bgr: Optional[float] = Field(None, description="Blood glucose random (mgs/dl)")
    bu: Optional[float] = Field(None, description="Blood urea (mgs/dl)")
    sc: Optional[float] = Field(None, description="Serum creatinine (mgs/dl)")
    sod: Optional[float] = Field(None, description="Sodium (mEq/L)")
    pot: Optional[float] = Field(None, description="Potassium (mEq/L)")
    hemo: Optional[float] = Field(None, description="Hemoglobin (gms)")
    pcv: Optional[float] = Field(None, description="Packed cell volume")
    wc: Optional[float] = Field(None, description="White blood cell count (cells/cumm)")
    rc: Optional[float] = Field(None, description="Red blood cell count (millions/cmm)")

    # 10 Categorical Features
    rbc: Optional[str] = Field(None, description="Red blood cells (normal, abnormal)")
    pc: Optional[str] = Field(None, description="Pus cell (normal, abnormal)")
    pcc: Optional[str] = Field(None, description="Pus cell clumps (present, notpresent)")
    ba: Optional[str] = Field(None, description="Bacteria (present, notpresent)")
    htn: Optional[str] = Field(None, description="Hypertension (yes, no)")
    dm: Optional[str] = Field(None, description="Diabetes mellitus (yes, no)")
    cad: Optional[str] = Field(None, description="Coronary artery disease (yes, no)")
    appet: Optional[str] = Field(None, description="Appetite (good, poor)")
    pe: Optional[str] = Field(None, description="Pedal edema (yes, no)")
    ane: Optional[str] = Field(None, description="Anemia (yes, no)")

    is_user_verified: bool = Field(
        True,
        description="Whether values have been verified by the user. False triggers safety hold.",
    )
    report_id: Optional[int] = Field(
        None,
        description="Optional Report ID for audit database persistence",
    )

    @field_validator(
        "age", "bp", "sg", "al", "su", "bgr", "bu", "sc", "sod",
        "pot", "hemo", "pcv", "wc", "rc",
        mode="before"
    )
    @classmethod
    def check_finite_num(cls, v: Any) -> Any:
        if v is None:
            return None
        try:
            val = float(v)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Value must be a valid number: {v}") from exc
        return validate_finite_numeric(val)

    @field_validator(
        "rbc", "pc", "pcc", "ba", "htn", "dm", "cad", "appet", "pe", "ane",
        mode="before"
    )
    @classmethod
    def clean_string(cls, v: Any) -> Any:
        if v is None:
            return None
        return str(v).strip().lower()


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class RiskPredictionResponse(BaseModel):
    """Output schema for an individual condition ML risk prediction."""

    condition: str = Field(..., description="Target condition: diabetes, heart_disease, kidney_disease")
    status: str = Field(..., description="OK, INSUFFICIENT_FEATURES, VERIFICATION_REQUIRED, or ERROR")
    risk_probability: Optional[float] = Field(
        None,
        description="Model-estimated risk probability P(target=1) in [0.0, 1.0]",
    )
    risk_band: Optional[str] = Field(
        None,
        description="Educational display band: LOW (<0.30), MODERATE (0.30-0.70), ELEVATED (>=0.70)",
    )
    model_name: Optional[str] = Field(None, description="Champion model identifier")
    model_version: Optional[str] = Field(None, description="Artifact timestamp / version")
    supplied_features_count: int = Field(0, description="Count of supplied valid feature values")
    required_features_count: int = Field(0, description="Total features required by the model")
    missing_features: List[str] = Field(default_factory=list, description="List of missing required features")
    disclaimer: str = Field(
        MANDATORY_ML_DISCLAIMER,
        description="Mandatory non-diagnostic safety disclaimer",
    )
    persisted_prediction_id: Optional[int] = Field(
        None,
        description="Database primary key if prediction was persisted",
    )


class ModelStatusInfo(BaseModel):
    """Status details for a single disease risk model."""

    available: bool = Field(..., description="Whether model artifact loaded successfully")
    model_name: Optional[str] = Field(None, description="Model candidate identifier")
    model_type: Optional[str] = Field(None, description="Classifier family name")
    integrity_verified: bool = Field(..., description="Whether artifact SHA-256 matches metadata")
    version: Optional[str] = Field(None, description="Model training timestamp / version")


class MLStatusResponse(BaseModel):
    """Health and availability status of backend ML risk models."""

    status: str = Field(..., description="Overall service status: OK, DEGRADED, or ERROR")
    models: Dict[str, ModelStatusInfo] = Field(..., description="Per-condition model status")
