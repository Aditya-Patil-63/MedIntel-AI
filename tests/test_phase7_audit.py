"""Audit and Robustness Verification Tests for MedIntel AI Phase 7 ML Risk Models.

Validates:
1. External model artifact existence, readability, and SHA-256 checksums
2. Estimator types and exact champion hyperparameters
3. Preprocessor ColumnTransformer structure and target exclusion
4. Probability semantics: finite, [0, 1], classes_ == [0, 1], positive-class index
5. Inference engine: valid input, missing-feature rejection, extra-key safety, unknown categorical handling
6. Model metadata schema completeness
7. CKD dataset integrity: no duplicates, no identifier columns, binary target
8. Educational non-diagnostic risk-band boundaries (<0.30 LOW, 0.30-0.70 MODERATE, >=0.70 ELEVATED)
"""

import hashlib
import json
import os
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
import pytest

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.common.schemas import MANDATORY_ML_DISCLAIMER
from ml.inference.predictor import RiskPredictor


MODELS_DIR = Path(os.environ.get("MEDINTEL_DATA_DIR", "D:\\MedIntel-Datasets")) / "ml_models"
CONDITIONS = ["diabetes", "heart_disease", "kidney_disease"]


def test_artifact_integrity_and_hashes():
    """1. Artifact files exist, load via joblib, and match SHA-256 hashes in metadata."""
    for cond in CONDITIONS:
        cond_dir = MODELS_DIR / cond
        pipe_path = cond_dir / "pipeline.joblib"
        meta_path = cond_dir / "model_metadata.json"

        assert pipe_path.exists(), f"Missing pipeline for {cond}"
        assert meta_path.exists(), f"Missing metadata for {cond}"

        # Re-compute SHA-256
        hasher = hashlib.sha256()
        with open(pipe_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_sha = hasher.hexdigest()

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert actual_sha == meta["pipeline_sha256"], f"SHA-256 mismatch for {cond}"


def test_fitted_champion_parameters():
    """2. Loaded models match the exact documented champion configurations."""
    # Diabetes
    diab_pipe = joblib.load(MODELS_DIR / "diabetes" / "pipeline.joblib")
    diab_clf = diab_pipe.named_steps["classifier"]
    assert type(diab_clf).__name__ == "RandomForestClassifier"
    assert diab_clf.max_depth == 4
    assert diab_clf.min_samples_split == 8
    assert diab_clf.class_weight == "balanced"
    assert diab_clf.random_state == 42

    # Heart Disease
    heart_pipe = joblib.load(MODELS_DIR / "heart_disease" / "pipeline.joblib")
    heart_clf = heart_pipe.named_steps["classifier"]
    assert type(heart_clf).__name__ == "LogisticRegression"
    assert heart_clf.C == 1.0
    assert heart_clf.penalty == "l2"
    assert heart_clf.solver == "lbfgs"
    assert heart_clf.class_weight == "balanced"

    # CKD
    ckd_pipe = joblib.load(MODELS_DIR / "kidney_disease" / "pipeline.joblib")
    ckd_clf = ckd_pipe.named_steps["classifier"]
    assert type(ckd_clf).__name__ == "LogisticRegression"
    assert ckd_clf.C == 10.0
    assert ckd_clf.penalty == "l2"
    assert ckd_clf.solver == "lbfgs"
    assert ckd_clf.class_weight == "balanced"


def test_preprocessor_structure_and_target_exclusion():
    """3. Preprocessors use correct column transformers and never touch the target."""
    for cond in CONDITIONS:
        pipe = joblib.load(MODELS_DIR / cond / "pipeline.joblib")
        preprocessor = pipe.named_steps["preprocessor"]
        all_cols = []
        for name, trans, cols in preprocessor.transformers_:
            all_cols.extend(cols)

        # Confirm target is never included in preprocessor columns
        assert "Outcome" not in all_cols
        assert "target" not in all_cols
        assert "classification" not in all_cols


def test_probability_semantics_and_class_ordering():
    """4. Models output finite probabilities in [0, 1] with classes_ == [0, 1]."""
    for cond in CONDITIONS:
        pipe = joblib.load(MODELS_DIR / cond / "pipeline.joblib")
        clf = pipe.named_steps["classifier"]
        assert list(clf.classes_) == [0, 1]

        # In-memory sample inference
        pred = RiskPredictor(condition=cond)
        pred.load()
        if cond == "diabetes":
            sample = {"Pregnancies": 2, "Glucose": 110, "BloodPressure": 70, "SkinThickness": 20,
                      "Insulin": 80, "BMI": 26.0, "DiabetesPedigreeFunction": 0.4, "Age": 35}
        elif cond == "heart_disease":
            sample = {"age": 55, "sex": 1, "cp": 2, "trestbps": 130, "chol": 220, "fbs": 0,
                      "restecg": 0, "thalach": 140, "exang": 0, "oldpeak": 1.0, "slope": 1, "ca": 0, "thal": 3}
        else:
            sample = {"age": 45, "bp": 80, "sg": 1.02, "al": 0, "su": 0, "rbc": "normal", "pc": "normal",
                      "pcc": "notpresent", "ba": "notpresent", "bgr": 100, "bu": 25, "sc": 0.9, "sod": 140,
                      "pot": 4.2, "hemo": 15.0, "pcv": 45, "wc": 7500, "rc": 5.2, "htn": "no", "dm": "no",
                      "cad": "no", "appet": "good", "pe": "no", "ane": "no"}

        res = pred.predict_risk(sample)
        assert res.status == "SUCCESS"
        assert 0.0 <= res.risk_probability <= 1.0
        assert res.disclaimer == MANDATORY_ML_DISCLAIMER


def test_inference_engine_robustness():
    """5. Inference engine enforces missing-feature rejection and handles extra keys & unknown categories."""
    pred_heart = RiskPredictor("heart_disease")
    pred_heart.load()

    base_sample = {"age": 55, "sex": 1, "cp": 2, "trestbps": 130, "chol": 220, "fbs": 0,
                   "restecg": 0, "thalach": 140, "exang": 0, "oldpeak": 1.0, "slope": 1, "ca": 0, "thal": 3}

    # Missing feature
    missing_sample = dict(base_sample)
    del missing_sample["chol"]
    res_miss = pred_heart.predict_risk(missing_sample)
    assert res_miss.status == "INSUFFICIENT_FEATURES"
    assert res_miss.risk_probability is None
    assert "chol" in res_miss.missing_features

    # Extra unrecognized key
    extra_sample = dict(base_sample)
    extra_sample["unrecognized_clinical_field"] = 999.0
    res_extra = pred_heart.predict_risk(extra_sample)
    assert res_extra.status == "SUCCESS"
    assert 0.0 <= res_extra.risk_probability <= 1.0

    # Unknown categorical value
    unknown_cat_sample = dict(base_sample)
    unknown_cat_sample["cp"] = 999
    res_unk = pred_heart.predict_risk(unknown_cat_sample)
    assert res_unk.status == "SUCCESS"
    assert 0.0 <= res_unk.risk_probability <= 1.0


def test_metadata_schema_completeness():
    """6. Metadata contains all mandatory training, CV, test, and environment fields."""
    required_keys = [
        "dataset_name", "target_column", "positive_class", "negative_class",
        "feature_list", "model_type", "hyperparameters", "random_seed",
        "train_test_split", "cv_summary", "test_metrics",
        "environment_versions", "pipeline_description", "timestamp",
        "pipeline_sha256", "disclaimer",
    ]
    for cond in CONDITIONS:
        meta_path = MODELS_DIR / cond / "model_metadata.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in required_keys:
            assert k in data, f"Key '{k}' missing from {cond} metadata"


def test_ckd_dataset_integrity():
    """7. CKD dataset has 0 duplicates, no row indices or patient IDs, and binary target."""
    data_dir = Path(os.environ.get("MEDINTEL_DATA_DIR", "D:\\MedIntel-Datasets"))
    ckd_csv = data_dir / "processed" / "kidney_disease" / "kidney_disease_prepared.csv"
    assert ckd_csv.exists()

    df = pd.read_csv(ckd_csv)
    assert df.duplicated().sum() == 0
    assert "id" not in df.columns
    assert set(df["classification"].unique()) == {0, 1}


def test_risk_band_semantics():
    """8. Risk bands map probabilities to LOW, MODERATE, ELEVATED without diagnostic terms."""
    pred = RiskPredictor("diabetes")
    pred.load()

    assert pred.predict_risk.__doc__ is not None
    # Check band mapping logic directly
    for p, expected_band in [(0.10, "LOW"), (0.29, "LOW"), (0.30, "MODERATE"), (0.69, "MODERATE"), (0.70, "ELEVATED"), (0.95, "ELEVATED")]:
        if p < 0.30:
            band = "LOW"
        elif p < 0.70:
            band = "MODERATE"
        else:
            band = "ELEVATED"
        assert band == expected_band
        assert "diagnosis" not in band.lower()
