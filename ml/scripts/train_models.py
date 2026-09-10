"""MedIntel AI — ML Models Training, Evaluation, and Artifact Serialization Script.

Phase 7: Leakage-Safe Training & Evaluation:
1. 80/20 stratified split (seed=42)
2. 5-fold Stratified CV on 80% training set across 10 candidate configurations
3. Deterministic champion selection based on screening priority:
   Recall -> ROC-AUC -> Specificity -> Brier Score -> Model Simplicity
4. Refit champion on complete 80% training split
5. Single evaluation on untouched 20% held-out test split
6. Export artifacts to external directory: MEDINTEL_DATA_DIR/ml_models/{condition}/
   (pipeline.joblib + model_metadata.json with SHA-256 checksum)
7. Verification and sanity check

Usage:
    python ml/scripts/train_models.py
"""

import os
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.evaluation.evaluate import evaluate_on_test_set, export_model_artifacts
from ml.inference.predictor import RiskPredictor
from ml.training.train import train_condition


CONDITIONS = ["diabetes", "heart_disease", "kidney_disease"]


def run_training():
    """Execute training, evaluation, and serialization across all three conditions."""
    print("=" * 80)
    print("MEDINTEL AI — PHASE 7 ML RISK MODELS TRAINING PIPELINE")
    print("=" * 80)

    results_summary = {}

    for condition in CONDITIONS:
        print("\n" + "#" * 80)
        print(f"CONDITION: {condition.upper()}")
        print("#" * 80)

        # 1. Train and Cross-Validate
        print(f"\n[1/4] Running 5-fold Stratified CV across candidate models on 80% train set...")
        refit_pipeline, champion_cv, all_cv_summaries, split_data = train_condition(
            condition=condition,
            random_state=42,
        )
        X_train, X_test, y_train, y_test = split_data
        print(f"      Train samples: {len(X_train)} | Test samples: {len(X_test)}")
        print(f"      Total candidates evaluated: {len(all_cv_summaries)}")

        # Print CV metrics table
        print("\n[CV RESULTS SUMMARY - 5 Folds]")
        print(f"{'Candidate Name':<32} | {'Recall':<14} | {'ROC-AUC':<14} | {'Specificity':<14} | {'Brier':<14} | {'F1':<14}")
        print("-" * 115)
        for s in all_cv_summaries:
            rec = f"{s.mean_metrics['recall']:.4f}±{s.std_metrics['recall']:.4f}"
            roc = f"{s.mean_metrics['roc_auc']:.4f}±{s.std_metrics['roc_auc']:.4f}"
            spec = f"{s.mean_metrics['specificity']:.4f}±{s.std_metrics['specificity']:.4f}"
            brier = f"{s.mean_metrics['brier_score']:.4f}±{s.std_metrics['brier_score']:.4f}"
            f1 = f"{s.mean_metrics['f1']:.4f}±{s.std_metrics['f1']:.4f}"
            is_champ = " [*CHAMPION*]" if s.candidate_name == champion_cv.candidate_name else ""
            print(f"{s.candidate_name:<32} | {rec:<14} | {roc:<14} | {spec:<14} | {brier:<14} | {f1:<14}{is_champ}")

        print(f"\nSelected Champion: {champion_cv.candidate_name} ({champion_cv.model_type})")
        print(f"Hyperparameters: {champion_cv.hyperparameters}")

        # 2. Evaluate ONCE on untouched 20% held-out test split
        print(f"\n[2/4] Evaluating champion ONCE on untouched 20% held-out test split...")
        test_metrics = evaluate_on_test_set(
            pipeline=refit_pipeline,
            X_test=X_test,
            y_test=y_test,
            threshold=0.50,
        )

        print("\n[HELD-OUT TEST SET METRICS]")
        print(f"  Accuracy:       {test_metrics.accuracy:.4f}")
        print(f"  Precision:      {test_metrics.precision:.4f}")
        print(f"  Recall (Sens):  {test_metrics.recall:.4f}")
        print(f"  Specificity:    {test_metrics.specificity:.4f}")
        print(f"  F1 Score:       {test_metrics.f1:.4f}")
        print(f"  ROC-AUC:        {test_metrics.roc_auc:.4f}")
        print(f"  PR-AUC:         {test_metrics.pr_auc:.4f}")
        print(f"  Brier Score:    {test_metrics.brier_score:.4f}")
        print(f"  Confusion Matrix: TN={test_metrics.true_negatives}, FP={test_metrics.false_positives}, "
              f"FN={test_metrics.false_negatives}, TP={test_metrics.true_positives} (Total={test_metrics.total_samples})")

        # 3. Export Artifacts
        print(f"\n[3/4] Exporting model artifacts to external storage...")
        feature_list = X_train.columns.tolist()
        metadata = export_model_artifacts(
            condition=condition,
            pipeline=refit_pipeline,
            champion_cv=champion_cv,
            test_metrics=test_metrics,
            feature_list=feature_list,
            target_column=y_train.name,
            train_samples=len(X_train),
            test_samples=len(X_test),
        )
        print(f"      Pipeline path:   {metadata['pipeline_path']}")
        print(f"      Pipeline SHA256: {metadata['pipeline_sha256']}")

        # 4. Sanity Check via Predictor
        print(f"\n[4/4] Performing inference sanity check with RiskPredictor...")
        predictor = RiskPredictor(condition=condition)
        predictor.load(verify_sha256=True)

        sample_input = X_test.iloc[0].to_dict()
        pred_result = predictor.predict_risk(sample_input)
        print(f"      Sample Prediction Status:  {pred_result.status}")
        print(f"      Risk Probability:         {pred_result.risk_probability}")
        print(f"      Risk Index:               {pred_result.risk_index}")
        print(f"      Binary Prediction:        {pred_result.binary_prediction}")
        print(f"      Disclaimer Present:       {bool(pred_result.disclaimer)}")

        # Test incomplete input handling
        incomplete_input = {}
        missing_result = predictor.predict_risk(incomplete_input)
        print(f"      Missing Feature Test:     {missing_result.status} (Missing {len(missing_result.missing_features)} features)")
        assert missing_result.status == "INSUFFICIENT_FEATURES"
        assert missing_result.risk_probability is None

        results_summary[condition] = {
            "champion": champion_cv.candidate_name,
            "cv_metrics": champion_cv.mean_metrics,
            "test_metrics": test_metrics.model_dump(),
            "pipeline_sha256": metadata["pipeline_sha256"],
            "pipeline_path": metadata["pipeline_path"],
        }

    print("\n" + "=" * 80)
    print("ALL CONDITIONS SUCCESSFULLY TRAINED, EVALUATED, AND EXPORTED!")
    print("=" * 80)
    return results_summary


if __name__ == "__main__":
    run_training()
