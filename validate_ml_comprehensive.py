"""
MedIntel AI — Comprehensive Trained Model Validation and Prediction Consistency Suite.

Validates the three statistical disease risk models against original datasets:
1. Diabetes Risk Prediction (Pima Indians Diabetes, 768 records)
2. Heart Disease Risk Prediction (UCI Cleveland, 297 records)
3. Chronic Kidney Disease Risk Prediction (UCI CKD, 400 records)

Produces full evaluation metrics, confusion matrices, calibration data,
metamorphic robustness checks, and pipeline-to-API consistency verification.
"""

import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple
import urllib.request
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

# Add project root and backend to sys.path
REPO_ROOT = Path("d:/MedIntel AI").resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.common.data_loader import load_and_validate_dataset
from ml.inference.predictor import RiskPredictor

DATA_DIR = Path(r"D:\MedIntel-Datasets")
MODELS_DIR = DATA_DIR / "ml_models"
API_BASE_URL = "http://127.0.0.1:8000"


def evaluate_model_on_dataset(condition: str) -> Dict[str, Any]:
    """Evaluate a trained model pipeline against its original prepared dataset."""
    print(f"\n=======================================================")
    print(f"VALIDATING MODEL: {condition.upper()}")
    print(f"=======================================================")

    predictor = RiskPredictor(condition=condition, models_base_dir=str(MODELS_DIR))
    predictor.load(verify_sha256=True)

    df, features, target_col = load_and_validate_dataset(condition, data_dir=DATA_DIR)
    total_samples = len(df)
    positive_count = int(df[target_col].sum())
    negative_count = total_samples - positive_count

    print(f"Dataset: {condition} ({total_samples} rows, {len(features)} features)")
    print(f"Class Balance: {positive_count} Positive ({positive_count/total_samples*100:.1f}%), {negative_count} Negative ({negative_count/total_samples*100:.1f}%)")

    # 1. Full Dataset Evaluation
    X_full = df[features]
    y_full = df[target_col].values

    y_prob_full = predictor.pipeline.predict_proba(X_full)[:, 1]
    y_pred_full = (y_prob_full >= 0.5).astype(int)

    tn_full, fp_full, fn_full, tp_full = confusion_matrix(y_full, y_pred_full).ravel()
    metrics_full = {
        "total_samples": total_samples,
        "true_positives": int(tp_full),
        "false_positives": int(fp_full),
        "true_negatives": int(tn_full),
        "false_negatives": int(fn_full),
        "accuracy": round(float(accuracy_score(y_full, y_pred_full)), 4),
        "precision": round(float(precision_score(y_full, y_pred_full, zero_division=0)), 4),
        "recall": round(float(recall_score(y_full, y_pred_full, zero_division=0)), 4),
        "specificity": round(float(tn_full / (tn_full + fp_full)), 4),
        "f1": round(float(f1_score(y_full, y_pred_full, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_full, y_prob_full)), 4),
        "brier_score": round(float(brier_score_loss(y_full, y_prob_full)), 4),
    }

    print(f"Full Dataset Performance: Acc={metrics_full['accuracy']}, Sens={metrics_full['recall']}, Spec={metrics_full['specificity']}, ROC-AUC={metrics_full['roc_auc']}")

    # 2. Stratified 80/20 Train/Test Split Evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X_full, y_full, test_size=0.2, random_state=42, stratify=y_full
    )

    y_prob_test = predictor.pipeline.predict_proba(X_test)[:, 1]
    y_pred_test = (y_prob_test >= 0.5).astype(int)
    tn_test, fp_test, fn_test, tp_test = confusion_matrix(y_test, y_pred_test).ravel()
    metrics_test = {
        "total_samples": len(y_test),
        "true_positives": int(tp_test),
        "false_positives": int(fp_test),
        "true_negatives": int(tn_test),
        "false_negatives": int(fn_test),
        "accuracy": round(float(accuracy_score(y_test, y_pred_test)), 4),
        "precision": round(float(precision_score(y_test, y_pred_test, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_test, zero_division=0)), 4),
        "specificity": round(float(tn_test / (tn_test + fp_test)), 4),
        "f1": round(float(f1_score(y_test, y_pred_test, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob_test)), 4),
        "brier_score": round(float(brier_score_loss(y_test, y_prob_test)), 4),
    }

    print(f"Held-Out Test Set (20%): Acc={metrics_test['accuracy']}, Sens={metrics_test['recall']}, Spec={metrics_test['specificity']}, ROC-AUC={metrics_test['roc_auc']}")

    # 3. Calibration Analysis (Probability Deciles)
    calibration_bins = []
    bins = np.linspace(0.0, 1.0, 6)  # 5 bins: [0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0]
    for i in range(len(bins) - 1):
        low, high = bins[i], bins[i + 1]
        mask = (y_prob_full >= low) & (y_prob_full <= high if i == len(bins) - 2 else y_prob_full < high)
        bin_count = int(mask.sum())
        if bin_count > 0:
            bin_pred_mean = round(float(y_prob_full[mask].mean()), 4)
            bin_true_rate = round(float(y_full[mask].mean()), 4)
        else:
            bin_pred_mean = round((low + high) / 2.0, 4)
            bin_true_rate = 0.0
        calibration_bins.append({
            "range": f"[{low:.1f}, {high:.1f}]",
            "count": bin_count,
            "mean_predicted_prob": bin_pred_mean,
            "observed_positive_rate": bin_true_rate,
        })

    # 4. Metamorphic Robustness & Repeatability
    sample_row = df.iloc[0][features].to_dict()
    # 100-run Determinism test
    rep_probs = []
    for _ in range(100):
        res = predictor.predict_risk(sample_row)
        rep_probs.append(res.risk_probability)
    is_strictly_deterministic = len(set(rep_probs)) == 1

    # Permutation Invariance (reversing dict keys)
    reversed_keys = list(reversed(list(sample_row.keys())))
    scrambled_row = {k: sample_row[k] for k in reversed_keys}
    res_scrambled = predictor.predict_risk(scrambled_row)
    permutation_invariant = (res_scrambled.risk_probability == rep_probs[0])

    # Missing Feature Rejection (drop one feature at a time)
    missing_rejected_count = 0
    for feat in features:
        incomplete_input = sample_row.copy()
        incomplete_input.pop(feat)
        res_missing = predictor.predict_risk(incomplete_input)
        if res_missing.status == "INSUFFICIENT_FEATURES" and feat in res_missing.missing_features:
            missing_rejected_count += 1
    missing_feature_safe = (missing_rejected_count == len(features))

    print(f"Robustness Checks: 100x Deterministic={is_strictly_deterministic}, Permutation Invariant={permutation_invariant}, Missing Features Safe={missing_feature_safe}")

    # 5. Pipeline-to-API-to-UI Consistency
    api_endpoint = f"/api/v1/ml/predict/{'diabetes' if condition == 'diabetes' else ('heart-disease' if condition == 'heart_disease' else 'kidney-disease')}"
    req_body = sample_row.copy()
    req_body["is_user_verified"] = True
    
    url = f"{API_BASE_URL}{api_endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    api_res = {}
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            api_res = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] API call failed for {api_endpoint}: {e}")

    raw_prob = rep_probs[0]
    api_prob = api_res.get("risk_probability")
    api_band = api_res.get("risk_band")
    expected_band = "LOW" if raw_prob < 0.30 else ("MODERATE" if raw_prob < 0.70 else "ELEVATED")

    api_consistent = (
        api_prob is not None and
        abs(api_prob - raw_prob) < 1e-3 and
        api_band == expected_band
    )

    print(f"API Consistency ({api_endpoint}): Raw={raw_prob}, API={api_prob}, Band={api_band} (Match={api_consistent})")

    # 6. Error Analysis: Top false positives and false negatives
    fp_indices = np.where((y_full == 0) & (y_pred_full == 1))[0]
    fn_indices = np.where((y_full == 1) & (y_pred_full == 0))[0]

    sample_errors = {
        "false_positives_count": len(fp_indices),
        "false_negatives_count": len(fn_indices),
        "fp_sample_features": [df.iloc[idx][features].to_dict() for idx in fp_indices[:3]],
        "fn_sample_features": [df.iloc[idx][features].to_dict() for idx in fn_indices[:3]],
    }

    return {
        "condition": condition,
        "candidate_name": predictor.metadata.get("candidate_name"),
        "model_type": predictor.metadata.get("model_type"),
        "pipeline_sha256": predictor.metadata.get("pipeline_sha256"),
        "features": features,
        "metrics_full": metrics_full,
        "metrics_held_out": metrics_test,
        "calibration_bins": calibration_bins,
        "robustness": {
            "deterministic_100_runs": is_strictly_deterministic,
            "permutation_invariant": permutation_invariant,
            "missing_feature_safe": missing_feature_safe,
            "all_features_rejected_when_missing": f"{missing_rejected_count}/{len(features)}",
        },
        "api_consistency": {
            "endpoint": api_endpoint,
            "raw_prob": raw_prob,
            "api_prob": api_prob,
            "api_band": api_band,
            "consistent": api_consistent,
        },
        "sample_errors": sample_errors,
    }


def run_full_validation():
    print("=" * 70)
    print("MEDINTEL AI — COMPREHENSIVE TRAINED MODEL VALIDATION SUITE")
    print("=" * 70)

    results = {}
    for condition in ["diabetes", "heart_disease", "kidney_disease"]:
        try:
            results[condition] = evaluate_model_on_dataset(condition)
        except Exception as e:
            print(f"[-] Validation failed for {condition}: {e}")
            import traceback
            traceback.print_exc()

    # Save validation summary
    output_path = Path("ml_validation_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Validation results saved to {output_path.resolve()}")
    return results


if __name__ == "__main__":
    run_full_validation()
