"""Chronic Kidney Disease (CKD) feature definitions and validation."""

from typing import Any

NUMERICAL_FEATURES: list[str] = [
    "age",
    "bp",
    "sg",
    "al",
    "su",
    "bgr",
    "bu",
    "sc",
    "sod",
    "pot",
    "hemo",
    "pcv",
    "wc",
    "rc",
]

CATEGORICAL_FEATURES: list[str] = [
    "rbc",
    "pc",
    "pcc",
    "ba",
    "htn",
    "dm",
    "cad",
    "appet",
    "pe",
    "ane",
]

FEATURES: list[str] = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

TARGET_COLUMN: str = "classification"
POSITIVE_CLASS: int = 1  # CKD present
NEGATIVE_CLASS: int = 0  # Not CKD


def validate_input_features(input_data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate that all required features for CKD prediction are present.

    Args:
        input_data: Mapping of feature names to values.

    Returns:
        Tuple of (is_valid, missing_features_list).
    """
    missing = [feat for feat in FEATURES if feat not in input_data or input_data[feat] is None]
    return len(missing) == 0, missing
