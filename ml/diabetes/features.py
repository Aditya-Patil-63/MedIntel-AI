"""
MedIntel AI — Diabetes Risk Feature Definitions & Validator.

Dataset: Pima Indians Diabetes Database (NIDDK / UCI DOI: 10.24432/C58K5K).
"""

from typing import Any, Dict, List, Tuple

CONDITION_NAME = "diabetes"
MODEL_NAME = "diabetes_risk_estimator"
TARGET_NAME = "Outcome"
TARGET_COLUMN = TARGET_NAME
POSITIVE_CLASS = 1
NEGATIVE_CLASS = 0

FEATURE_NAMES: List[str] = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]

FEATURES = FEATURE_NAMES
NUMERICAL_FEATURES: List[str] = FEATURE_NAMES.copy()
CATEGORICAL_FEATURES: List[str] = []


def validate_input_features(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate patient inputs against required diabetes feature schema.

    Returns:
        (is_valid: bool, missing_features: List[str])
    """
    missing = [f for f in FEATURE_NAMES if f not in data or data[f] is None]
    return len(missing) == 0, missing
