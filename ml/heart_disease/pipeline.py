"""
MedIntel AI — Heart Disease Preprocessing & Model Pipeline Factory.

Applies StandardScaler to continuous features, passthrough to binary features,
and OneHotEncoder(drop='first', handle_unknown='ignore') to categorical features.
"""

from typing import Any
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.heart_disease.features import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
)


def create_heart_disease_preprocessor() -> ColumnTransformer:
    """Create ColumnTransformer for heart disease clinical features."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), CONTINUOUS_FEATURES),
            ("bin", "passthrough", BINARY_FEATURES),
            (
                "cat",
                OneHotEncoder(drop="first", handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )


def create_heart_disease_pipeline(classifier: Any) -> Pipeline:
    """
    Construct a complete, leak-free scikit-learn Pipeline for heart disease risk estimation.

    Args:
        classifier: Initialized scikit-learn compatible classifier.

    Returns:
        Unified Pipeline object.
    """
    preprocessor = create_heart_disease_preprocessor()
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )
