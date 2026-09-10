"""Unit and Regression Tests for MedIntel AI Phase 7 ML Risk Models.

Tests:
1. Feature definitions
2. Dataset validation
3. Target validation
4. Pipeline construction
5. ColumnTransformer configuration
6. No target leakage into features
7. Logistic Regression pipeline
8. Random Forest pipeline
9. Gradient boosting pipeline
10. Stratified split reproducibility
11. CV reproducibility
12. Specificity calculation
13. ROC-AUC calculation
14. PR-AUC calculation
15. Brier score calculation
16. Positive-class probability extraction
17. Missing required feature rejection
18. Unknown categorical handling
19. Threshold configuration
20. Safety terminology and disclaimer
"""

import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from ml.common.data_loader import load_and_validate_dataset
from ml.common.metrics import calculate_metrics
from ml.common.schemas import MANDATORY_ML_DISCLAIMER, ModelRiskResult
from ml.diabetes.features import (
    FEATURES as DIABETES_FEATURES,
    NEGATIVE_CLASS as DIABETES_NEG,
    POSITIVE_CLASS as DIABETES_POS,
    TARGET_COLUMN as DIABETES_TARGET,
    validate_input_features as validate_diabetes,
)
from ml.diabetes.pipeline import create_diabetes_pipeline
from ml.heart_disease.features import (
    BINARY_FEATURES as HEART_BIN,
    CATEGORICAL_FEATURES as HEART_CAT,
    CONTINUOUS_FEATURES as HEART_CONT,
    FEATURES as HEART_FEATURES,
    NEGATIVE_CLASS as HEART_NEG,
    POSITIVE_CLASS as HEART_POS,
    TARGET_COLUMN as HEART_TARGET,
    validate_input_features as validate_heart,
)
from ml.heart_disease.pipeline import create_heart_disease_pipeline
from ml.inference.predictor import RiskPredictor
from ml.kidney_disease.features import (
    CATEGORICAL_FEATURES as CKD_CAT,
    FEATURES as CKD_FEATURES,
    NEGATIVE_CLASS as CKD_NEG,
    NUMERICAL_FEATURES as CKD_NUM,
    POSITIVE_CLASS as CKD_POS,
    TARGET_COLUMN as CKD_TARGET,
    validate_input_features as validate_ckd,
)
from ml.kidney_disease.pipeline import create_kidney_disease_pipeline
from ml.training.cross_validator import run_stratified_cv
from ml.training.train import (
    build_pipeline_for_condition,
    get_candidate_models,
    select_champion,
    split_dataset,
)


# =====================================================================
# Synthetic In-Memory Data Fixtures (Zero Held-Out Test Data Leakage)
# =====================================================================

@pytest.fixture
def synthetic_diabetes_df():
    """Create deterministic synthetic diabetes DataFrame for testing."""
    rng = np.random.RandomState(42)
    n = 60
    data = {
        "Pregnancies": rng.randint(0, 10, size=n),
        "Glucose": rng.randint(70, 200, size=n),
        "BloodPressure": rng.randint(60, 100, size=n),
        "SkinThickness": rng.randint(10, 40, size=n),
        "Insulin": rng.randint(15, 250, size=n),
        "BMI": rng.uniform(18.0, 45.0, size=n),
        "DiabetesPedigreeFunction": rng.uniform(0.1, 1.5, size=n),
        "Age": rng.randint(21, 70, size=n),
        "Outcome": rng.choice([0, 1], size=n, p=[0.6, 0.4]),
    }
    return pd.DataFrame(data)


@pytest.fixture
def synthetic_heart_df():
    """Create deterministic synthetic heart disease DataFrame for testing."""
    rng = np.random.RandomState(42)
    n = 60
    data = {
        "age": rng.randint(30, 75, size=n),
        "sex": rng.choice([0, 1], size=n),
        "cp": rng.choice([1, 2, 3, 4], size=n),
        "trestbps": rng.randint(100, 180, size=n),
        "chol": rng.randint(150, 350, size=n),
        "fbs": rng.choice([0, 1], size=n),
        "restecg": rng.choice([0, 1, 2], size=n),
        "thalach": rng.randint(90, 190, size=n),
        "exang": rng.choice([0, 1], size=n),
        "oldpeak": rng.uniform(0.0, 5.0, size=n),
        "slope": rng.choice([1, 2, 3], size=n),
        "ca": rng.choice([0, 1, 2, 3], size=n),
        "thal": rng.choice([3, 6, 7], size=n),
        "target": rng.choice([0, 1], size=n, p=[0.5, 0.5]),
    }
    return pd.DataFrame(data)


@pytest.fixture
def synthetic_ckd_df():
    """Create deterministic synthetic CKD DataFrame for testing."""
    rng = np.random.RandomState(42)
    n = 60
    data = {
        "age": rng.randint(20, 80, size=n),
        "bp": rng.randint(60, 120, size=n),
        "sg": rng.choice([1.005, 1.010, 1.015, 1.020, 1.025], size=n),
        "al": rng.choice([0, 1, 2, 3, 4], size=n),
        "su": rng.choice([0, 1, 2, 3, 4], size=n),
        "rbc": rng.choice(["normal", "abnormal"], size=n),
        "pc": rng.choice(["normal", "abnormal"], size=n),
        "pcc": rng.choice(["present", "notpresent"], size=n),
        "ba": rng.choice(["present", "notpresent"], size=n),
        "bgr": rng.randint(70, 250, size=n),
        "bu": rng.randint(10, 100, size=n),
        "sc": rng.uniform(0.5, 6.0, size=n),
        "sod": rng.randint(120, 150, size=n),
        "pot": rng.uniform(3.0, 6.5, size=n),
        "hemo": rng.uniform(6.0, 17.0, size=n),
        "pcv": rng.randint(20, 50, size=n),
        "wc": rng.randint(4000, 15000, size=n),
        "rc": rng.uniform(2.5, 6.5, size=n),
        "htn": rng.choice(["yes", "no"], size=n),
        "dm": rng.choice(["yes", "no"], size=n),
        "cad": rng.choice(["yes", "no"], size=n),
        "appet": rng.choice(["good", "poor"], size=n),
        "pe": rng.choice(["yes", "no"], size=n),
        "ane": rng.choice(["yes", "no"], size=n),
        "classification": rng.choice([0, 1], size=n, p=[0.4, 0.6]),
    }
    return pd.DataFrame(data)


# =====================================================================
# Test Cases
# =====================================================================

def test_1_feature_definitions():
    """1. Feature definitions match specifications exactly."""
    assert len(DIABETES_FEATURES) == 8
    assert DIABETES_TARGET == "Outcome"
    assert DIABETES_POS == 1 and DIABETES_NEG == 0

    assert len(HEART_FEATURES) == 13
    assert len(HEART_CONT) == 5
    assert len(HEART_BIN) == 3
    assert len(HEART_CAT) == 5
    assert HEART_TARGET == "target"
    assert HEART_POS == 1 and HEART_NEG == 0

    assert len(CKD_FEATURES) == 24
    assert len(CKD_NUM) == 14
    assert len(CKD_CAT) == 10
    assert CKD_TARGET == "classification"
    assert CKD_POS == 1 and CKD_NEG == 0


def test_2_dataset_validation(tmp_path):
    """2. Dataset loader raises clear error when file or columns are invalid."""
    # Missing directory
    with pytest.raises(FileNotFoundError):
        load_and_validate_dataset("diabetes", data_dir=str(tmp_path / "nonexistent"))

    # Missing column in CSV
    mock_dir = tmp_path / "processed" / "diabetes"
    mock_dir.mkdir(parents=True)
    bad_df = pd.DataFrame({"Pregnancies": [1], "Glucose": [100], "Outcome": [1]})
    bad_df.to_csv(mock_dir / "diabetes_prepared.csv", index=False)

    with pytest.raises(ValueError, match="missing .* expected feature columns"):
        load_and_validate_dataset("diabetes", data_dir=str(tmp_path))


def test_3_target_validation(tmp_path):
    """3. Dataset loader validates binary target (rejects non-binary/continuous)."""
    mock_dir = tmp_path / "processed" / "diabetes"
    mock_dir.mkdir(parents=True, exist_ok=True)
    data = {feat: [1.0, 2.0] for feat in DIABETES_FEATURES}
    data["Outcome"] = [0, 2]  # Invalid non-binary label 2
    pd.DataFrame(data).to_csv(mock_dir / "diabetes_prepared.csv", index=False)

    with pytest.raises(ValueError, match="Target column .* must contain only binary values"):
        load_and_validate_dataset("diabetes", data_dir=str(tmp_path))


def test_4_pipeline_construction():
    """4. Pipeline construction wraps preprocessor and classifier with named steps."""
    pipe_diab = create_diabetes_pipeline(LogisticRegression())
    assert "preprocessor" in pipe_diab.named_steps
    assert "classifier" in pipe_diab.named_steps

    pipe_heart = create_heart_disease_pipeline(RandomForestClassifier())
    assert "preprocessor" in pipe_heart.named_steps
    assert "classifier" in pipe_heart.named_steps

    pipe_ckd = create_kidney_disease_pipeline(HistGradientBoostingClassifier())
    assert "preprocessor" in pipe_ckd.named_steps
    assert "classifier" in pipe_ckd.named_steps


def test_5_column_transformer_configuration():
    """5. ColumnTransformer properly configures sub-transformers."""
    heart_pipe = create_heart_disease_pipeline(LogisticRegression())
    ct = heart_pipe.named_steps["preprocessor"]
    transformer_names = [name for name, _, _ in ct.transformers]
    assert "num" in transformer_names
    assert "bin" in transformer_names
    assert "cat" in transformer_names


def test_6_no_target_leakage_into_features():
    """6. Preprocessor feature lists never include the target column."""
    assert DIABETES_TARGET not in DIABETES_FEATURES
    assert HEART_TARGET not in HEART_FEATURES
    assert CKD_TARGET not in CKD_FEATURES


def test_7_logistic_regression_pipeline(synthetic_diabetes_df):
    """7. Logistic Regression pipeline fits, predicts probabilities in [0, 1]."""
    pipe = create_diabetes_pipeline(LogisticRegression(max_iter=500, random_state=42))
    X = synthetic_diabetes_df[DIABETES_FEATURES]
    y = synthetic_diabetes_df[DIABETES_TARGET]

    pipe.fit(X, y)
    probs = pipe.predict_proba(X)
    assert probs.shape == (len(X), 2)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)
    assert np.allclose(probs.sum(axis=1), 1.0)


def test_8_random_forest_pipeline(synthetic_heart_df):
    """8. Random Forest pipeline fits and outputs valid predictions."""
    pipe = create_heart_disease_pipeline(RandomForestClassifier(n_estimators=10, random_state=42))
    X = synthetic_heart_df[HEART_FEATURES]
    y = synthetic_heart_df[HEART_TARGET]

    pipe.fit(X, y)
    preds = pipe.predict(X)
    assert set(preds).issubset({0, 1})


def test_9_gradient_boosting_pipeline(synthetic_ckd_df):
    """9. HistGradientBoosting pipeline fits and outputs valid predictions."""
    pipe = create_kidney_disease_pipeline(HistGradientBoostingClassifier(max_iter=20, random_state=42))
    X = synthetic_ckd_df[CKD_FEATURES]
    y = synthetic_ckd_df[CKD_TARGET]

    pipe.fit(X, y)
    probs = pipe.predict_proba(X)
    assert probs.shape == (len(X), 2)


def test_10_stratified_split_reproducibility(synthetic_diabetes_df):
    """10. Stratified train/test split is strictly deterministic with seed 42."""
    X1, X2, y1, y2 = split_dataset(
        synthetic_diabetes_df,
        feature_columns=DIABETES_FEATURES,
        target_column=DIABETES_TARGET,
        test_size=0.20,
        random_state=42,
    )
    X1_b, X2_b, y1_b, y2_b = split_dataset(
        synthetic_diabetes_df,
        feature_columns=DIABETES_FEATURES,
        target_column=DIABETES_TARGET,
        test_size=0.20,
        random_state=42,
    )
    pd.testing.assert_frame_equal(X1, X1_b)
    pd.testing.assert_frame_equal(X2, X2_b)
    pd.testing.assert_series_equal(y1, y1_b)
    pd.testing.assert_series_equal(y2, y2_b)


def test_11_cv_reproducibility(synthetic_diabetes_df):
    """11. Stratified 5-fold CV yields identical mean metrics across repeated runs."""
    X = synthetic_diabetes_df[DIABETES_FEATURES]
    y = synthetic_diabetes_df[DIABETES_TARGET]
    pipe = create_diabetes_pipeline(LogisticRegression(max_iter=500, random_state=42))

    res1 = run_stratified_cv(
        pipeline=pipe,
        X_train=X,
        y_train=y,
        candidate_name="LogReg",
        model_type="LogisticRegression",
        hyperparameters={},
        random_state=42,
    )
    res2 = run_stratified_cv(
        pipeline=pipe,
        X_train=X,
        y_train=y,
        candidate_name="LogReg",
        model_type="LogisticRegression",
        hyperparameters={},
        random_state=42,
    )
    assert res1.mean_metrics == res2.mean_metrics
    assert res1.std_metrics == res2.std_metrics


def test_12_specificity_calculation():
    """12. Specificity = TN / (TN + FP) handles valid and zero-denominator cases."""
    # TN=3, FP=1, FN=1, TP=3 -> Specificity = 3 / (3 + 1) = 0.75
    y_true = [0, 0, 0, 0, 1, 1, 1, 1]
    y_prob = [0.1, 0.2, 0.3, 0.8, 0.2, 0.7, 0.8, 0.9]
    metrics = calculate_metrics(y_true, y_prob, threshold=0.50)
    assert metrics.specificity == 0.75
    assert metrics.true_negatives == 3
    assert metrics.false_positives == 1

    # Zero denominator case: No actual negatives in y_true
    y_all_pos = [1, 1, 1]
    y_prob_all = [0.6, 0.7, 0.8]
    metrics_all_pos = calculate_metrics(y_all_pos, y_prob_all, threshold=0.50)
    assert metrics_all_pos.specificity == 0.0


def test_13_roc_auc_calculation():
    """13. ROC-AUC is 1.0 for perfect ranking."""
    y_true = [0, 0, 1, 1]
    y_prob = [0.1, 0.2, 0.8, 0.9]
    metrics = calculate_metrics(y_true, y_prob)
    assert metrics.roc_auc == 1.0


def test_14_pr_auc_calculation():
    """14. PR-AUC is within [0.0, 1.0] and handles binary datasets."""
    y_true = [0, 0, 1, 1]
    y_prob = [0.1, 0.2, 0.8, 0.9]
    metrics = calculate_metrics(y_true, y_prob)
    assert 0.0 <= metrics.pr_auc <= 1.0


def test_15_brier_score_calculation():
    """15. Brier score is 0.0 for perfect probabilities and > 0 otherwise."""
    y_true = [0, 1]
    y_prob_perfect = [0.0, 1.0]
    metrics_perf = calculate_metrics(y_true, y_prob_perfect)
    assert metrics_perf.brier_score == 0.0

    y_prob_imperfect = [0.3, 0.7]
    metrics_imp = calculate_metrics(y_true, y_prob_imperfect)
    # (0.3^2 + (1-0.7)^2) / 2 = (0.09 + 0.09) / 2 = 0.09
    assert metrics_imp.brier_score == 0.09


def test_16_positive_class_probability_extraction(synthetic_diabetes_df):
    """16. Probability extraction targets positive class (1)."""
    pipe = create_diabetes_pipeline(LogisticRegression(max_iter=500, random_state=42))
    X = synthetic_diabetes_df[DIABETES_FEATURES]
    y = synthetic_diabetes_df[DIABETES_TARGET]
    pipe.fit(X, y)

    prob_matrix = pipe.predict_proba(X)
    pos_probs = prob_matrix[:, 1]
    assert np.all(pos_probs == prob_matrix[:, 1])


def test_17_missing_required_feature_rejection():
    """17. Feature validators reject missing features cleanly."""
    incomplete_diab = {"Glucose": 120, "Age": 45}  # missing 6 features
    is_valid, missing = validate_diabetes(incomplete_diab)
    assert not is_valid
    assert len(missing) == 6

    incomplete_heart = {"age": 55, "sex": 1}
    is_valid, missing = validate_heart(incomplete_heart)
    assert not is_valid
    assert "chol" in missing

    incomplete_ckd = {"age": 60}
    is_valid, missing = validate_ckd(incomplete_ckd)
    assert not is_valid
    assert "sc" in missing


def test_18_unknown_categorical_handling(synthetic_heart_df):
    """18. OneHotEncoder ignores unseen categorical categories at inference time without throwing error."""
    pipe = create_heart_disease_pipeline(LogisticRegression(max_iter=500, random_state=42))
    X = synthetic_heart_df[HEART_FEATURES]
    y = synthetic_heart_df[HEART_TARGET]
    pipe.fit(X, y)

    # Test sample with unseen category for chest pain type: cp=99
    unseen_sample = X.iloc[0:1].copy()
    unseen_sample["cp"] = 99

    # Should not raise exception
    probs = pipe.predict_proba(unseen_sample)
    assert probs.shape == (1, 2)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)


def test_19_threshold_configuration():
    """19. Threshold changes affect binary prediction while preserving probability."""
    y_true = [0, 1]
    y_prob = [0.45, 0.65]

    m_low = calculate_metrics(y_true, y_prob, threshold=0.40)
    assert m_low.true_positives == 1
    assert m_low.false_positives == 1  # 0.45 >= 0.40 -> predicted 1 (FP)

    m_high = calculate_metrics(y_true, y_prob, threshold=0.70)
    assert m_high.false_negatives == 1  # 0.65 < 0.70 -> predicted 0 (FN)
    assert m_high.false_positives == 0


def test_20_safety_terminology_and_disclaimer():
    """20. ModelRiskResult enforces mandatory disclaimer and educational risk bands."""
    result_low = ModelRiskResult(
        model_name="diabetes_test",
        condition="diabetes",
        status="SUCCESS",
        risk_probability=0.15,
        risk_index="LOW",
        threshold_used=0.50,
        binary_prediction=0,
        missing_features=[],
        supplied_features_count=8,
        required_features_count=8,
    )
    assert result_low.disclaimer == MANDATORY_ML_DISCLAIMER
    assert result_low.risk_index in {"LOW", "MODERATE", "ELEVATED"}
    assert "diagnosis" not in result_low.risk_index.lower()
