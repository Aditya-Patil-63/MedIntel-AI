"""
MedIntel AI — ML Evaluation Metrics.

Phase 7: Deterministic calculation of classification and probability calibration metrics.
Strictly handles zero-division edge cases for sensitivity and specificity.
"""

from typing import Dict, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.common.schemas import EvaluationMetrics


def calculate_metrics(
    y_true: Union[np.ndarray, list],
    y_prob: Union[np.ndarray, list],
    threshold: float = 0.50,
) -> EvaluationMetrics:
    """
    Compute comprehensive evaluation metrics from ground-truth labels and predicted probabilities.

    Args:
        y_true: Ground-truth binary labels in {0, 1}.
        y_prob: Predicted probabilities for the positive class (class 1), in [0.0, 1.0].
        threshold: Decision cutoff for threshold-dependent binary classification metrics.

    Returns:
        EvaluationMetrics instance containing discrimination, calibration, and confusion matrix stats.
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)

    if len(y_true_arr) == 0:
        raise ValueError("Cannot calculate metrics on empty arrays.")

    if len(y_true_arr) != len(y_prob_arr):
        raise ValueError(
            f"Length mismatch: y_true has {len(y_true_arr)} items, y_prob has {len(y_prob_arr)}."
        )

    # Validate probability bounds
    if np.any(y_prob_arr < 0.0) or np.any(y_prob_arr > 1.0):
        raise ValueError("Probabilities must lie strictly within [0.0, 1.0].")

    # Binary decisions from continuous probability
    y_pred_arr = (y_prob_arr >= threshold).astype(int)

    # Confusion matrix extraction
    # labels=[0, 1] ensures 2x2 shape even if a class is absent in batch
    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    total = int(len(y_true_arr))

    # Standard metrics
    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0.0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0.0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0.0))

    # Specificity = TN / (TN + FP)
    actual_negatives = tn + fp
    spec = float(tn / actual_negatives) if actual_negatives > 0 else 0.0

    # Probabilistic metrics (ROC-AUC, PR-AUC, Brier score)
    # Check if both classes are present in y_true for ROC/PR AUC
    unique_classes = np.unique(y_true_arr)
    if len(unique_classes) >= 2:
        roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr))
        pr_auc = float(average_precision_score(y_true_arr, y_prob_arr))
    else:
        # Fallback if only single class present
        roc_auc = 0.50
        pr_auc = float(np.mean(y_true_arr))

    brier = float(brier_score_loss(y_true_arr, y_prob_arr))

    return EvaluationMetrics(
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        specificity=round(spec, 4),
        f1=round(f1, 4),
        roc_auc=round(roc_auc, 4),
        pr_auc=round(pr_auc, 4),
        brier_score=round(brier, 4),
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
        total_samples=total,
        threshold=threshold,
    )
