"""MedIntel AI — ML Dataset Loaders and Schema Validators.

Phase 7: Validates external prepared datasets, ensuring zero column drift,
correct binary target encoding, and non-empty records.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from ml.diabetes.features import FEATURES as DIABETES_FEATURES, TARGET_COLUMN as DIABETES_TARGET
from ml.heart_disease.features import FEATURES as HEART_FEATURES, TARGET_COLUMN as HEART_TARGET
from ml.kidney_disease.features import FEATURES as CKD_FEATURES, TARGET_COLUMN as CKD_TARGET

CONDITION_CONFIG = {
    "diabetes": {
        "features": DIABETES_FEATURES,
        "target": DIABETES_TARGET,
        "subpath": Path("processed") / "diabetes" / "diabetes_prepared.csv",
    },
    "heart_disease": {
        "features": HEART_FEATURES,
        "target": HEART_TARGET,
        "subpath": Path("processed") / "heart_disease" / "heart_disease_prepared.csv",
    },
    "kidney_disease": {
        "features": CKD_FEATURES,
        "target": CKD_TARGET,
        "subpath": Path("processed") / "kidney_disease" / "kidney_disease_prepared.csv",
    },
}


def get_data_dir() -> Path:
    """Resolve the external datasets directory from environment or fallback paths."""
    env_dir = os.environ.get("MEDINTEL_DATA_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.exists():
            return p

    # Standard default paths
    candidates = [
        Path(r"D:\MedIntel-Datasets"),
        Path(__file__).resolve().parents[3] / "MedIntel-Datasets",
        Path.cwd() / "MedIntel-Datasets",
    ]
    for c in candidates:
        if c.exists():
            return c

    # Fallback default
    return Path(r"D:\MedIntel-Datasets")


class DatasetValidationError(ValueError):
    """Raised when an external dataset fails schema or integrity validation."""
    pass


def load_and_validate_dataset(
    condition_or_path: Union[str, Path],
    expected_features: Optional[List[str]] = None,
    target_column: Optional[str] = None,
    data_dir: Optional[Union[str, Path]] = None,
) -> Tuple[pd.DataFrame, List[str], str]:
    """Load a CSV dataset and rigorously validate schema and target values.

    Args:
        condition_or_path: Condition name ('diabetes', 'heart_disease', 'kidney_disease')
                           or direct Path to CSV file.
        expected_features: Optional list of required features (inferred if condition name provided).
        target_column: Optional target column name (inferred if condition name provided).
        data_dir: Base directory override for dataset storage.

    Returns:
        Tuple of (df: pd.DataFrame, features: List[str], target_column: str)

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        DatasetValidationError: If schema or value constraints are violated.
    """
    if isinstance(condition_or_path, str) and condition_or_path in CONDITION_CONFIG:
        cfg = CONDITION_CONFIG[condition_or_path]
        features = expected_features or cfg["features"]
        target_col = target_column or cfg["target"]
        base = Path(data_dir or get_data_dir())
        file_path = base / cfg["subpath"]
    else:
        file_path = Path(condition_or_path)
        if expected_features is None or target_column is None:
            raise ValueError("expected_features and target_column must be supplied when loading from direct path.")
        features = expected_features
        target_col = target_column

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file does not exist: {file_path}. "
            f"Ensure Phase 3 datasets are prepared in MEDINTEL_DATA_DIR."
        )

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise DatasetValidationError(f"Failed to read CSV at {file_path}: {e}")

    if df.empty:
        raise DatasetValidationError(f"Dataset at {file_path} is empty (0 rows).")

    # 1. Target column validation
    if target_col not in df.columns:
        raise DatasetValidationError(
            f"Required target column '{target_col}' is missing from {file_path}. "
            f"Found columns: {df.columns.tolist()}"
        )

    unique_targets = set(df[target_col].dropna().unique())
    if not unique_targets.issubset({0, 1}):
        raise DatasetValidationError(
            f"Target column '{target_col}' must contain only binary values in {{0, 1}}. Found: {unique_targets}."
        )

    # 2. Features validation
    missing_cols = [col for col in features if col not in df.columns]
    if missing_cols:
        raise DatasetValidationError(
            f"Dataset at {file_path} is missing {len(missing_cols)} expected feature columns: {missing_cols}."
        )

    # 3. Check for null values in features
    X = df[features]
    null_counts = X.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if not cols_with_nulls.empty:
        raise DatasetValidationError(
            f"Dataset features in {file_path} contain unexpected null values: {cols_with_nulls.to_dict()}."
        )

    return df, features, target_col


def load_diabetes_dataset(data_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """Load and validate the prepared Pima Indians Diabetes dataset."""
    df, features, target = load_and_validate_dataset("diabetes", data_dir=data_dir)
    return df[features], df[target]


def load_heart_disease_dataset(data_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """Load and validate the prepared UCI Cleveland Heart Disease dataset."""
    df, features, target = load_and_validate_dataset("heart_disease", data_dir=data_dir)
    return df[features], df[target]


def load_kidney_disease_dataset(data_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """Load and validate the prepared UCI Chronic Kidney Disease dataset."""
    df, features, target = load_and_validate_dataset("kidney_disease", data_dir=data_dir)
    return df[features], df[target]
