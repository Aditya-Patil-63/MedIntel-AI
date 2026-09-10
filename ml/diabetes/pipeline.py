"""
MedIntel AI — Diabetes Preprocessing & Model Pipeline Factory.

Encapsulates StandardScaler within a leakage-safe ColumnTransformer.
"""

from typing import Any
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.diabetes.features import NUMERICAL_FEATURES


def create_diabetes_preprocessor() -> ColumnTransformer:
    """Create ColumnTransformer for diabetes features."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
        ],
        remainder="drop",
    )


def create_diabetes_pipeline(classifier: Any) -> Pipeline:
    """
    Construct a complete, leak-free scikit-learn Pipeline for diabetes risk estimation.

    Args:
        classifier: Initialized scikit-learn compatible classifier.

    Returns:
        Unified Pipeline object.
    """
    preprocessor = create_diabetes_preprocessor()
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )
