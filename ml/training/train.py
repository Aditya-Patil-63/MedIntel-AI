"""Model Training and Champion Selection Pipeline for MedIntel AI.

Phase 7: Leakage-safe model selection across classical classifiers:
- LogisticRegression (L2 regularized, balanced)
- RandomForestClassifier (regularized, balanced)
- HistGradientBoostingClassifier (balanced)

Champion is selected deterministically from 5-fold Stratified CV on the training split.
The champion is then refit on the complete 80% training set.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ml.common.data_loader import load_and_validate_dataset
from ml.diabetes import create_diabetes_pipeline
from ml.diabetes.features import FEATURES as DIABETES_FEATURES, TARGET_COLUMN as DIABETES_TARGET
from ml.heart_disease import create_heart_disease_pipeline
from ml.heart_disease.features import FEATURES as HEART_FEATURES, TARGET_COLUMN as HEART_TARGET
from ml.kidney_disease import create_kidney_disease_pipeline
from ml.kidney_disease.features import FEATURES as CKD_FEATURES, TARGET_COLUMN as CKD_TARGET
from ml.training.cross_validator import CrossValidationSummary, run_stratified_cv


def get_candidate_models(random_state: int = 42) -> List[Tuple[str, str, Dict[str, Any], Any]]:
    """Generate the candidate classifiers and their configurations.

    Returns:
        List of tuples: (candidate_name, model_family, hyperparameters_dict, estimator_instance)
    """
    candidates = []

    # 1. Logistic Regression candidates (C in [0.01, 0.1, 1.0, 10.0])
    for c_val in [0.01, 0.1, 1.0, 10.0]:
        name = f"LogisticRegression_C{c_val}"
        params = {
            "C": c_val,
            "penalty": "l2",
            "solver": "lbfgs",
            "class_weight": "balanced",
            "max_iter": 1000,
            "random_state": random_state,
        }
        estimator = LogisticRegression(**params)
        candidates.append((name, "LogisticRegression", params, estimator))

    # 2. Random Forest candidates (max_depth in [4, 6], min_samples_split in [4, 8])
    for max_d in [4, 6]:
        for min_split in [4, 8]:
            name = f"RandomForest_d{max_d}_s{min_split}"
            params = {
                "n_estimators": 100,
                "max_depth": max_d,
                "min_samples_split": min_split,
                "class_weight": "balanced",
                "random_state": random_state,
            }
            estimator = RandomForestClassifier(**params)
            candidates.append((name, "RandomForestClassifier", params, estimator))

    # 3. HistGradientBoosting candidates (learning_rate in [0.05, 0.1], max_depth=3)
    for lr in [0.05, 0.1]:
        name = f"HistGradientBoosting_lr{lr}_d3"
        params = {
            "learning_rate": lr,
            "max_iter": 100,
            "max_depth": 3,
            "class_weight": "balanced",
            "random_state": random_state,
        }
        estimator = HistGradientBoostingClassifier(**params)
        candidates.append((name, "HistGradientBoostingClassifier", params, estimator))

    return candidates


def build_pipeline_for_condition(condition: str, estimator: Any) -> Pipeline:
    """Wrap estimator with condition-specific preprocessing ColumnTransformer.

    Args:
        condition: 'diabetes', 'heart_disease', or 'kidney_disease'
        estimator: Unfitted scikit-learn classifier

    Returns:
        Configured Pipeline
    """
    if condition == "diabetes":
        return create_diabetes_pipeline(estimator)
    elif condition == "heart_disease":
        return create_heart_disease_pipeline(estimator)
    elif condition == "kidney_disease":
        return create_kidney_disease_pipeline(estimator)
    else:
        raise ValueError(f"Unknown medical condition: {condition}")


def select_champion(cv_results: List[CrossValidationSummary]) -> CrossValidationSummary:
    """Deterministically select champion candidate model from CV results.

    Priority:
    1. Highest mean CV recall (screening sensitivity)
    2. Highest mean CV ROC-AUC
    3. Highest mean CV specificity
    4. Lowest mean CV Brier score (lower is better)
    5. Simplest model family (LogisticRegression > RandomForest > HistGradientBoosting)

    Args:
        cv_results: List of CrossValidationSummary objects from CV evaluation.

    Returns:
        The winning CrossValidationSummary.
    """
    if not cv_results:
        raise ValueError("Cannot select champion from empty CV results list.")

    simplicity_order = {
        "LogisticRegression": 3,
        "RandomForestClassifier": 2,
        "HistGradientBoostingClassifier": 1,
    }

    def sort_key(summary: CrossValidationSummary):
        rec = summary.mean_metrics.get("recall", 0.0)
        roc = summary.mean_metrics.get("roc_auc", 0.0)
        spec = summary.mean_metrics.get("specificity", 0.0)
        # Brier is negated so higher sorted key means lower (better) brier score
        neg_brier = -summary.mean_metrics.get("brier_score", 1.0)
        simplicity = simplicity_order.get(summary.model_type, 0)
        return (rec, roc, spec, neg_brier, simplicity)

    sorted_candidates = sorted(cv_results, key=sort_key, reverse=True)
    return sorted_candidates[0]


def split_dataset(
    df: pd.DataFrame,
    feature_columns: List[str],
    target_column: str,
    test_size: float = 0.20,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Perform a stratified 80/20 train/test split.

    Args:
        df: Cleaned dataframe.
        feature_columns: List of predictor feature names.
        target_column: Target column name.
        test_size: Proportion for held-out test set (default 0.20).
        random_state: Random state seed (default 42).

    Returns:
        (X_train, X_test, y_train, y_test)
    """
    X = df[feature_columns]
    y = df[target_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )
    return X_train, X_test, y_train, y_test


def train_condition(
    condition: str,
    data_dir: Optional[str] = None,
    random_state: int = 42,
) -> Tuple[Pipeline, CrossValidationSummary, List[CrossValidationSummary], Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]]:
    """Execute complete leakage-safe CV and champion training for a given condition.

    Args:
        condition: 'diabetes', 'heart_disease', or 'kidney_disease'
        data_dir: Optional external dataset directory.
        random_state: Random state seed (42).

    Returns:
        Tuple of:
        - refit_champion_pipeline (Pipeline fit on 80% train data)
        - champion_cv_summary (CrossValidationSummary of winner)
        - all_cv_summaries (List of CrossValidationSummary for all candidates)
        - split_data tuple: (X_train, X_test, y_train, y_test)
    """
    # 1. Load and strictly validate dataset
    df, features, target_col = load_and_validate_dataset(condition, data_dir=data_dir)

    # 2. Stratified 80/20 split (held-out test set is NEVER used in CV)
    X_train, X_test, y_train, y_test = split_dataset(
        df,
        feature_columns=features,
        target_column=target_col,
        test_size=0.20,
        random_state=random_state,
    )

    # 3. Run Stratified 5-fold CV for all candidate models on training split ONLY
    candidates = get_candidate_models(random_state=random_state)
    all_cv_summaries: List[CrossValidationSummary] = []
    candidate_pipelines: Dict[str, Pipeline] = {}

    for cand_name, model_type, hyperparams, estimator in candidates:
        pipeline = build_pipeline_for_condition(condition, estimator)
        candidate_pipelines[cand_name] = pipeline

        cv_summary = run_stratified_cv(
            pipeline=pipeline,
            X_train=X_train,
            y_train=y_train,
            candidate_name=cand_name,
            model_type=model_type,
            hyperparameters=hyperparams,
            n_splits=5,
            random_state=random_state,
        )
        all_cv_summaries.append(cv_summary)

    # 4. Deterministically select champion from CV metrics
    champion_summary = select_champion(all_cv_summaries)

    # 5. Refit champion pipeline on the ENTIRE 80% training set
    champion_pipeline_template = candidate_pipelines[champion_summary.candidate_name]
    refit_champion = clone(champion_pipeline_template)
    refit_champion.fit(X_train, y_train)

    return refit_champion, champion_summary, all_cv_summaries, (X_train, X_test, y_train, y_test)
