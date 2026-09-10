"""Stratified Cross-Validation Runner for MedIntel AI.

Phase 7: Runs 5-fold Stratified CV strictly inside the training set.
All preprocessing transforms are encapsulated inside the pipeline and fit per fold.
Zero data leakage into validation folds.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold

from ml.common.metrics import calculate_metrics
from ml.common.schemas import EvaluationMetrics


@dataclass
class CrossValidationSummary:
    """Aggregated cross-validation summary across all folds."""

    candidate_name: str
    model_type: str
    hyperparameters: Dict[str, Any]
    fold_metrics: List[EvaluationMetrics]
    mean_metrics: Dict[str, float]
    std_metrics: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary format."""
        return {
            "candidate_name": self.candidate_name,
            "model_type": self.model_type,
            "hyperparameters": self.hyperparameters,
            "mean_metrics": self.mean_metrics,
            "std_metrics": self.std_metrics,
            "fold_metrics": [m.model_dump() for m in self.fold_metrics],
        }


def run_stratified_cv(
    pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    candidate_name: str,
    model_type: str,
    hyperparameters: Dict[str, Any],
    n_splits: int = 5,
    random_state: int = 42,
    threshold: float = 0.50,
) -> CrossValidationSummary:
    """Run 5-fold Stratified Cross-Validation strictly within training data.

    Args:
        pipeline: Unfitted sklearn Pipeline containing preprocessor and classifier.
        X_train: Feature DataFrame for the training split.
        y_train: Target Series for the training split.
        candidate_name: Human-readable name for this candidate configuration.
        model_type: Classifier family name (e.g. LogisticRegression).
        hyperparameters: Dictionary of hyperparameters.
        n_splits: Number of stratified folds (default 5).
        random_state: Random seed for fold splitting (default 42).
        threshold: Decision threshold for threshold-dependent metrics (default 0.50).

    Returns:
        CrossValidationSummary containing fold-level and aggregated metrics.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    fold_metrics: List[EvaluationMetrics] = []

    y_arr = np.asarray(y_train)

    for fold_idx, (train_indices, val_indices) in enumerate(skf.split(X_train, y_arr), start=1):
        if isinstance(X_train, pd.DataFrame):
            X_fold_train = X_train.iloc[train_indices]
            X_fold_val = X_train.iloc[val_indices]
        else:
            X_fold_train = X_train[train_indices]
            X_fold_val = X_train[val_indices]

        y_fold_train = y_arr[train_indices]
        y_fold_val = y_arr[val_indices]

        # Clone creates an unfitted fresh instance of the pipeline
        fold_pipeline = clone(pipeline)
        fold_pipeline.fit(X_fold_train, y_fold_train)

        # Predict probability for positive class (1)
        if hasattr(fold_pipeline, "predict_proba"):
            y_fold_prob = fold_pipeline.predict_proba(X_fold_val)[:, 1]
        elif hasattr(fold_pipeline, "decision_function"):
            # Fallback to sigmoid of decision function if predict_proba is not available
            scores = fold_pipeline.decision_function(X_fold_val)
            y_fold_prob = 1.0 / (1.0 + np.exp(-scores))
        else:
            raise AttributeError(f"Pipeline classifier does not support probability estimation: {candidate_name}")

        metrics = calculate_metrics(y_true=y_fold_val, y_prob=y_fold_prob, threshold=threshold)
        fold_metrics.append(metrics)

    # Compute mean and standard deviation across folds
    metric_keys = [
        "accuracy",
        "precision",
        "recall",
        "specificity",
        "f1",
        "roc_auc",
        "pr_auc",
        "brier_score",
    ]

    mean_metrics: Dict[str, float] = {}
    std_metrics: Dict[str, float] = {}

    for key in metric_keys:
        values = [getattr(m, key) for m in fold_metrics]
        mean_metrics[key] = round(float(np.mean(values)), 4)
        std_metrics[key] = round(float(np.std(values)), 4)

    return CrossValidationSummary(
        candidate_name=candidate_name,
        model_type=model_type,
        hyperparameters=hyperparameters,
        fold_metrics=fold_metrics,
        mean_metrics=mean_metrics,
        std_metrics=std_metrics,
    )
