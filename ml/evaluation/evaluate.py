"""Evaluation and Artifact Serialization for MedIntel AI ML Models.

Phase 7: Evaluates champion model ONCE on the untouched 20% held-out test set.
Serializes pipeline.joblib and model_metadata.json strictly into external directory:
D:\\MedIntel-Datasets\\ml_models\\{condition}\\
Never inside Git.
"""

import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional
import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.common.metrics import calculate_metrics
from ml.common.schemas import MANDATORY_ML_DISCLAIMER, EvaluationMetrics
from ml.training.cross_validator import CrossValidationSummary


def evaluate_on_test_set(
    pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float = 0.50,
) -> EvaluationMetrics:
    """Evaluate a trained pipeline on the untouched held-out test split.

    Args:
        pipeline: Refitted pipeline.
        X_test: Feature DataFrame for held-out test set.
        y_test: True labels for held-out test set.
        threshold: Decision threshold for classification metrics.

    Returns:
        EvaluationMetrics instance with test results.
    """
    if hasattr(pipeline, "predict_proba"):
        y_prob = pipeline.predict_proba(X_test)[:, 1]
    elif hasattr(pipeline, "decision_function"):
        scores = pipeline.decision_function(X_test)
        y_prob = 1.0 / (1.0 + np.exp(-scores))
    else:
        raise AttributeError("Pipeline does not support probability estimation.")

    y_true = np.asarray(y_test)
    return calculate_metrics(y_true=y_true, y_prob=y_prob, threshold=threshold)


def export_model_artifacts(
    condition: str,
    pipeline: Any,
    champion_cv: CrossValidationSummary,
    test_metrics: EvaluationMetrics,
    feature_list: list,
    target_column: str,
    train_samples: int,
    test_samples: int,
    data_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Export pipeline.joblib and model_metadata.json to external storage.

    Target location:
    {MEDINTEL_DATA_DIR}/ml_models/{condition}/

    Args:
        condition: 'diabetes', 'heart_disease', or 'kidney_disease'
        pipeline: Refit champion pipeline
        champion_cv: CrossValidationSummary of the champion
        test_metrics: EvaluationMetrics on held-out test set
        feature_list: Predictor feature names
        target_column: Target column name
        train_samples: Number of training samples
        test_samples: Number of test samples
        data_dir: Base directory (defaults to MEDINTEL_DATA_DIR or D:\\MedIntel-Datasets)

    Returns:
        Saved metadata dictionary.
    """
    base_dir = Path(data_dir or os.environ.get("MEDINTEL_DATA_DIR", "D:\\MedIntel-Datasets"))
    output_dir = base_dir / "ml_models" / condition
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline_path = output_dir / "pipeline.joblib"
    metadata_path = output_dir / "model_metadata.json"

    # 1. Serialize pipeline.joblib
    joblib.dump(pipeline, pipeline_path)

    # 2. Compute SHA-256 hash of pipeline.joblib
    hasher = hashlib.sha256()
    with open(pipeline_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    pipeline_sha256 = hasher.hexdigest()

    # 3. Assemble model_metadata.json
    metadata = {
        "condition": condition,
        "dataset_name": f"{condition}_prepared",
        "feature_list": feature_list,
        "target_column": target_column,
        "positive_class": 1,
        "negative_class": 0,
        "model_type": champion_cv.model_type,
        "candidate_name": champion_cv.candidate_name,
        "hyperparameters": champion_cv.hyperparameters,
        "random_seed": 42,
        "train_test_split": {
            "train_samples": int(train_samples),
            "test_samples": int(test_samples),
            "train_ratio": 0.80,
            "test_ratio": 0.20,
            "stratified": True,
        },
        "cv_summary": champion_cv.to_dict(),
        "test_metrics": test_metrics.model_dump(),
        "environment_versions": {
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
            "python": sys.version,
        },
        "pipeline_description": str(pipeline),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pipeline_sha256": pipeline_sha256,
        "pipeline_path": str(pipeline_path),
        "disclaimer": MANDATORY_ML_DISCLAIMER,
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata
