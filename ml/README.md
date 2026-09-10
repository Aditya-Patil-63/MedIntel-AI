# Machine Learning Module — MedIntel AI

ML models for medical risk prediction.

## Status

**Current Phase: Phase 7 — ML Risk Models (Step 4: FastAPI ML Integration Complete)** ✅  
- 5-Fold Stratified Cross-Validation on 80% train split completed across 10 candidate architectures per condition.
- Champions deterministically selected using screening-oriented sensitivity hierarchy.
- Champion pipelines refit on 80% train split and evaluated once on untouched 20% held-out test splits.
- External artifacts serialized to `D:\MedIntel-Datasets\ml_models\` with SHA-256 verification.
- Comprehensive Step 3 audit: Zero data leakage, untouched test splits, and CKD performance investigated.
- Step 4 FastAPI ML Integration: Exposes safe, structured REST endpoints for Diabetes, Heart Disease, and CKD risk prediction + ML status endpoint.
- In-memory model caching, SHA-256 integrity checks, user verification gate (`is_user_verified`), zero-imputation policy (`INSUFFICIENT_FEATURES`), and SQLite prediction persistence.
- 48 Phase 7 tests across `tests/test_phase7_ml.py`, `tests/test_phase7_audit.py`, and `tests/test_phase7_api.py`; 213 total regression tests passing.

---

## Technical Documentation & Benchmark Reports

- [docs/PHASE7_ML_ARCHITECTURE.md](../docs/PHASE7_ML_ARCHITECTURE.md) — Pre-training architecture audit, leakage-safe pipeline designs, and data contracts.
- [docs/PHASE7_ML_TRAINING.md](../docs/PHASE7_ML_TRAINING.md) — Full benchmark report, candidate CV tables, held-out test metrics, confusion matrices, and checksums.
- [docs/PHASE7_MODEL_AUDIT.md](../docs/PHASE7_MODEL_AUDIT.md) — Step 3 model audit, robustness verification, CKD deep dive, and artifact validation.
- [docs/PHASE7_API_INTEGRATION.md](../docs/PHASE7_API_INTEGRATION.md) — Step 4 FastAPI integration, REST endpoints, request/response schemas, caching, and safety gates.

---

## Benchmark Summary

### Selected Champion Models & Performance:

| Condition | Selected Champion | Model Family | 5-Fold CV Recall | 5-Fold CV ROC-AUC | Held-Out Test Recall | Held-Out Test ROC-AUC | Held-Out Test Brier |
|---|---|---|---|---|---|---|---|
| **Diabetes** | `RandomForest_d4_s8` | `RandomForestClassifier` | $0.7663 \pm 0.0256$ | $0.8393 \pm 0.0176$ | **0.7963** | **0.8122** | 0.1760 |
| **Heart Disease** | `LogisticRegression_C1.0` | `LogisticRegression` | $0.7965 \pm 0.1349$ | $0.8991 \pm 0.0729$ | **0.7857** | **0.9286** | 0.1081 |
| **Chronic Kidney Disease** | `LogisticRegression_C10.0` | `LogisticRegression` | $1.0000 \pm 0.0000$ | $1.0000 \pm 0.0000$ | **0.9600** | **0.9993** | 0.0127 |

---

## Key Architectural Principles

1. **Strict Train / Val / Test Separation**:
   - 80% Stratified Training Split for 5-fold cross-validation and hyperparameter selection.
   - 20% Held-Out Test Split frozen and completely untouched during development.
2. **Leakage-Safe Preprocessing**:
   - `sklearn.compose.ColumnTransformer` + `sklearn.pipeline.Pipeline` fitted strictly inside training folds.
   - Zero learned transform fitting across folds or on held-out test splits.
3. **Non-Diagnostic Probability Semantics**:
   - Continuous risk probability ($P(\text{target}=1) \in [0.0, 1.0]$).
   - Terminology: "model-estimated risk probability", never "diagnostic certainty".
4. **Class Imbalance Policy**:
   - SMOTE is rejected on small clinical tabular data to prevent impossible synthetic feature combinations.
   - Handled via `class_weight='balanced'` and stratified sampling.
5. **Missing Feature Safety Policy**:
   - Strict `INSUFFICIENT_FEATURES` status returned if any required model predictor is missing.
   - Zero silent imputation or default guessing at inference time.
6. **External Artifact Storage**:
   - Serialized pipelines and JSON metadata stored outside Git in `D:\MedIntel-Datasets\ml_models\`.

---

## Datasets

The following three datasets are used for the risk-prediction tasks:

1. **Diabetes Risk Prediction:**
   - **Dataset:** Pima Indians Diabetes Database
   - **Original Source:** National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)
   - **Target:** `Outcome` (0 = No diabetes, 1 = Diabetes)
   - **Records:** 768 rows, 8 clinical features + 1 target

2. **Heart Disease Risk Prediction:**
   - **Dataset:** UCI Heart Disease Dataset (Cleveland subset, processed)
   - **Source:** UCI Machine Learning Repository (`DOI: 10.24432/C52P4X`)
   - **Target:** `target` (0 = absence, 1 = presence)
   - **Records:** 297 rows, 13 clinical features + 1 target

3. **Kidney Disease Risk Prediction:**
   - **Dataset:** UCI Chronic Kidney Disease Dataset
   - **Source:** UCI Machine Learning Repository (`DOI: 10.24432/C5G020`)
   - **Target:** `classification` (ckd → 1, notckd → 0)
   - **Records:** 400 rows, 24 clinical features + 1 target

> **Important:** Actual dataset files and trained `.joblib` model binaries are strictly kept OUTSIDE the Git repository in `MEDINTEL_DATA_DIR`.

---

## Module Structure

```
ml/
├── common/
│   ├── __init__.py
│   ├── base_model.py            # Abstract BaseRiskModel interface
│   ├── data_loader.py           # Robust dataset loader & schema validator
│   ├── metrics.py               # Discrimination, specificity, and Brier metrics
│   └── schemas.py               # Pydantic schemas (ModelRiskResult, EvaluationMetrics)
├── diabetes/
│   ├── __init__.py
│   ├── features.py              # 8 numeric features, validation rules
│   └── pipeline.py              # StandardScaler ColumnTransformer pipeline
├── heart_disease/
│   ├── __init__.py
│   ├── features.py              # 13 features (cont, bin, cat), validation rules
│   └── pipeline.py              # StandardScaler + OneHotEncoder pipeline
├── kidney_disease/
│   ├── __init__.py
│   ├── features.py              # 24 features (num, cat), validation rules
│   └── pipeline.py              # StandardScaler + OneHotEncoder pipeline
├── training/
│   ├── __init__.py
│   ├── cross_validator.py       # 5-fold Stratified CV runner
│   └── train.py                 # Candidate models & deterministic champion selection
├── evaluation/
│   ├── __init__.py
│   └── evaluate.py              # Test set evaluation & artifact exporter
├── inference/
│   ├── __init__.py
│   └── predictor.py             # Safe RiskPredictor engine with feature validation
├── scripts/
│   ├── data_config.py           # Shared path resolver using MEDINTEL_DATA_DIR
│   ├── inspect_*.py             # Dataset inspection scripts
│   ├── prepare_*.py             # Deterministic data preparation scripts
│   └── train_models.py          # Complete training & evaluation runner
├── data/
│   ├── metadata/
│   ├── DATASET_SOURCES.md
│   ├── DATASET_SETUP.md
│   └── DATA_QUALITY_REPORT.md
└── README.md
```

---

## Running Inspection, Preparation & Training

Ensure `MEDINTEL_DATA_DIR` is set to your external dataset directory:

```bash
# Windows PowerShell example
$env:MEDINTEL_DATA_DIR = "D:\MedIntel-Datasets"

# 1. Run Data Preparation Scripts
python ml/scripts/prepare_diabetes.py
python ml/scripts/prepare_heart_disease.py
python ml/scripts/prepare_kidney_disease.py

# 2. Run Model Training & Evaluation
python ml/scripts/train_models.py

# 3. Run Test Suite
pytest -v tests/test_phase7_ml.py
```
