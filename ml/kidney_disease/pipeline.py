"""Chronic Kidney Disease preprocessing and model pipeline construction."""

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.kidney_disease.features import CATEGORICAL_FEATURES, NUMERICAL_FEATURES


def create_kidney_disease_preprocessor() -> ColumnTransformer:
    """Create ColumnTransformer preprocessor for Chronic Kidney Disease.

    Transformations:
    - Numerical features (14): StandardScaler
    - Categorical features (10): OneHotEncoder(drop='first', handle_unknown='ignore')
    """
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            (
                "cat",
                OneHotEncoder(drop="first", handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )


def create_kidney_disease_pipeline(classifier) -> Pipeline:
    """Create a complete sklearn Pipeline for CKD risk estimation.

    Args:
        classifier: A scikit-learn compatible classifier instance.

    Returns:
        Configured Pipeline containing preprocessor and classifier.
    """
    preprocessor = create_kidney_disease_preprocessor()
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )
