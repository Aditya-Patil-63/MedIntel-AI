"""
MedIntel AI — Heart Disease Risk Feature Definitions & Validator.

Dataset: UCI Cleveland Heart Disease Dataset (DOI: 10.24432/C52P4X).
"""

from typing import Any, Dict, List, Tuple

CONDITION_NAME = "heart_disease"
MODEL_NAME = "heart_disease_risk_estimator"
TARGET_NAME = "target"
TARGET_COLUMN = TARGET_NAME
POSITIVE_CLASS = 1
NEGATIVE_CLASS = 0

CONTINUOUS_FEATURES: List[str] = [
    "age",
    "trestbps",
    "chol",
    "thalach",
    "oldpeak",
]

BINARY_FEATURES: List[str] = [
    "sex",
    "fbs",
    "exang",
]

CATEGORICAL_FEATURES: List[str] = [
    "cp",
    "restecg",
    "slope",
    "ca",
    "thal",
]

FEATURE_NAMES: List[str] = (
    CONTINUOUS_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES
)
FEATURES = FEATURE_NAMES


def validate_input_features(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate patient inputs against required heart disease feature schema.

    Returns:
        (is_valid: bool, missing_features: List[str])
    """
    missing = [f for f in FEATURE_NAMES if f not in data or data[f] is None]
    return len(missing) == 0, missing
