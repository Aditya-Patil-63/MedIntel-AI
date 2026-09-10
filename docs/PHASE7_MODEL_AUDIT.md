# Phase 7 — ML Risk Models: Step 3 Model Audit & Robustness Verification Report

> **MedIntel AI — Model Audit, Robustness Checks & Artifact Validation**  
> **Status:** Step 3 Complete (Artifact, Preprocessing, Schema, Leakage, CKD Deep-Dive, and Semantics Audited)  
> **Mandatory Medical Disclaimer:** These models provide continuous *model-estimated risk probabilities* derived from historical research benchmarks for educational screening prototypes. They do NOT provide a clinical diagnosis, medical prognosis, or treatment recommendation.

---

## 1. Artifact Integrity Verification

External serialized model files under `D:\MedIntel-Datasets\ml_models\` were independently verified for existence, readability, joblib deserialization, and SHA-256 hash match against `model_metadata.json`:

| Model Condition | Pipeline Path | File Size | Re-computed SHA-256 | Metadata SHA-256 | Integrity Status |
|---|---|---|---|---|---|
| **Diabetes** | `.../diabetes/pipeline.joblib` | 257,522 bytes | `ff72a814dc1ab3c6c88d108783577523960a692f4cb2fab5e2c24c2dbcde8a65` | `ff72a814dc1ab3c6c88d108783577523960a692f4cb2fab5e2c24c2dbcde8a65` | **MATCH (VERIFIED)** |
| **Heart Disease** | `.../heart_disease/pipeline.joblib` | 4,721 bytes | `c904d3b8f8d65a68c3ef07ef42607923fc3d0f6339f8f3a7ab7a6f6ba830e274` | `c904d3b8f8d65a68c3ef07ef42607923fc3d0f6339f8f3a7ab7a6f6ba830e274` | **MATCH (VERIFIED)** |
| **Chronic Kidney Disease** | `.../kidney_disease/pipeline.joblib` | 6,337 bytes | `b8bfe429529194c709c92a676f321004e7c66d0dcdc43e85056b4a82db5401a4` | `b8bfe429529194c709c92a676f321004e7c66d0dcdc43e85056b4a82db5401a4` | **MATCH (VERIFIED)** |

---

## 2. Feature Schema Verification

Each pipeline's preprocessor was inspected to verify that expected input features match the Phase 7 Step 1 specifications exactly:

- **Diabetes (8 features):** `Pregnancies`, `Glucose`, `BloodPressure`, `SkinThickness`, `Insulin`, `BMI`, `DiabetesPedigreeFunction`, `Age`. Target: `Outcome`.
- **Heart Disease (13 features):** `age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`, `oldpeak`, `slope`, `ca`, `thal`. Target: `target`.
- **Chronic Kidney Disease (24 features):** 14 numerical (`age`, `bp`, `sg`, `al`, `su`, `bgr`, `bu`, `sc`, `sod`, `pot`, `hemo`, `pcv`, `wc`, `rc`) and 10 categorical (`rbc`, `pc`, `pcc`, `ba`, `htn`, `dm`, `cad`, `appet`, `pe`, `ane`). Target: `classification`.

**Audit Findings:**
- Target columns (`Outcome`, `target`, `classification`) are strictly excluded from preprocessors and input features.
- In inference mode, extra unknown dictionary keys are safely disregarded without mutating input frames.
- No required feature is silently dropped or defaulted.

---

## 3. Preprocessing Verification

Inspection of fitted `ColumnTransformer` objects confirmed:
- **Diabetes:**
  - `num`: `StandardScaler(with_mean=True, with_std=True)` on all 8 numeric features.
  - `remainder`: `drop`.
- **Heart Disease:**
  - `num`: `StandardScaler` on 5 continuous features.
  - `bin`: `FunctionTransformer(passthrough)` on 3 binary features.
  - `cat`: `OneHotEncoder(drop='first', handle_unknown='ignore')` on 5 categorical features.
  - `remainder`: `drop`.
- **Chronic Kidney Disease:**
  - `num`: `StandardScaler` on 14 numerical features.
  - `cat`: `OneHotEncoder(drop='first', handle_unknown='ignore')` on 10 categorical features.
  - `remainder`: `drop`.

**Leakage Audit on Preprocessing:** No preprocessor transformer contains or transforms the target column.

---

## 4. Champion Configuration Verification

Inspection of fitted estimator attributes confirmed exact alignment with documented champion configurations:
- **Diabetes:** `RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_split=8, class_weight='balanced', random_state=42)`
- **Heart Disease:** `LogisticRegression(C=1.0, penalty='l2', solver='lbfgs', class_weight='balanced', max_iter=1000, random_state=42)`
- **Chronic Kidney Disease:** `LogisticRegression(C=10.0, penalty='l2', solver='lbfgs', class_weight='balanced', max_iter=1000, random_state=42)`

---

## 5. Chronic Kidney Disease (CKD) High-Performance Audit

The CKD champion achieved unusually high discrimination metrics ($CV \text{ ROC-AUC} = 1.0000$, $\text{Test ROC-AUC} = 0.9993$). A required root-cause investigation was performed across 6 dimensions:

### A. Feature-Target Association Analysis (Univariate Breakdown)
Univariate distributions across 400 records (150 NotCKD controls vs. 250 CKD cases) reveal extraordinarily pronounced biological separation in multiple individual biomarkers:
- **Hemoglobin (`hemo`):** NotCKD mean = $15.09 \pm 1.35$ g/dL vs. CKD mean = $11.02 \pm 2.12$ g/dL. **Univariate ROC-AUC = 0.9671**.
- **Packed Cell Volume (`pcv`):** NotCKD mean = $46.17 \pm 4.21\%$ vs. CKD mean = $34.83 \pm 6.91\%$. **Univariate ROC-AUC = 0.9524**.
- **Serum Creatinine (`sc`):** NotCKD mean = $0.88 \pm 0.26$ mg/dL vs. CKD mean = $4.27 \pm 6.81$ mg/dL. **Univariate ROC-AUC = 0.9215**.
- **Specific Gravity (`sg`):** NotCKD mean = $1.020$ vs. CKD mean = $1.010$. **Univariate ROC-AUC = 0.8884**.
- **Albumin (`al`):** In NotCKD controls, 100% of samples (150/150) have `al = 0.0` (zero albuminuria).
- **Categorical Comorbidities:** In the NotCKD control cohort, 100% of patients have `htn='no'`, `dm='no'`, `cad='no'`, `pe='no'`, and `ane='no'`.

### B. Target Encoding & Derivation Audit
- `classification` is the only target column.
- No feature is a proxy, derivative, or disguised version of `classification`.
- No feature column was created post-split or derived from labels.

### C. Patient Identifier Audit
- No `id`, `patient_id`, or row-index column exists in the prepared dataset.

### D. Duplicate Audit
- Exact duplicate rows in prepared CSV: **0**. No duplicate records found.

### E. Preprocessing & Split Audit
- Scalers and encoders were fit strictly inside training folds.
- The 20% test split ($N=80$) was frozen before any model training or selection.

### F. Finding & Statement
> **The unusually high CKD benchmark performance was investigated and no implementation-level target leakage was identified.**  
> The near-perfect discrimination is a documented characteristic of the UCI Chronic Kidney Disease benchmark dataset, which contrasts healthy controls (normal labs, no comorbidities) against hospitalized nephrology patients with advanced renal dysfunction. External clinical validation across broader, ambulatory cohorts is required before any clinical interpretation.

---

## 6. Train / Test Reproducibility Audit

Review of metadata and training configurations confirmed:
- `random_seed`: `42` across all splits, folds, and estimators.
- `train_test_split`: Stratified 80/20 partition ($N_{\text{train}}=614/237/320$, $N_{\text{test}}=154/60/80$).
- `cross_validation`: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
- Champion selection occurred strictly from CV metrics prior to refitting and test set evaluation.

---

## 7. Probability Semantics Audit

All three loaded pipelines were inspected for prediction mechanics:
- `classifier.classes_`: Strictly `[0, 1]` for all models.
- Positive class index: Mapped explicitly to index 1 (`probs[:, 1]`).
- Probabilities: Strictly bounded in $[0.0, 1.0]$, summing to $1.0$, with zero NaN or Inf values.

---

## 8. Inference Validation Audit

The `RiskPredictor` runtime engine was evaluated against edge cases:
1. **Complete Valid Input:** Successfully returns continuous `risk_probability`, categorical `risk_index`, and `status="SUCCESS"`.
2. **Missing Feature Input:** If any required predictor is missing or `None`, immediately returns `status="INSUFFICIENT_FEATURES"` and `risk_probability=None` with the exact list of missing features.
3. **Extra Unsupported Features:** Extra dictionary keys are disregarded safely; only registered model features are parsed into the inference DataFrame.
4. **Invalid Data Types:** Non-numeric strings in numeric feature fields are rejected with clear typing exceptions.
5. **Unknown Categorical Values:** Handled safely via `handle_unknown='ignore'`; one-hot columns for unseen categories evaluate to zeros without crashing.
6. **No Silent Imputation:** Population means or medians are never silently substituted during inference.

---

## 9. Metadata Completeness Audit

All `model_metadata.json` files contain all 16 mandatory top-level keys:
- `dataset_name`, `target_column`, `positive_class`, `negative_class`, `feature_list`, `model_type`, `hyperparameters`, `random_seed`, `train_test_split`, `cv_summary`, `test_metrics`, `environment_versions`, `pipeline_description`, `timestamp`, `pipeline_sha256`, `disclaimer`.

---

## 10. Test-Set Isolation Audit

Code paths in `ml/training/train.py`, `ml/training/cross_validator.py`, and `ml/scripts/train_models.py` were audited:
- Test partitions (`X_test`, `y_test`) were never passed into cross-validation loops, GridSearches, or preprocessor `.fit()` calls.
- Decision thresholds were kept fixed at default $0.50$ (no post-hoc threshold tuning on test splits).
- Zero test-set leakage or premature evaluation detected.

---

## 11. Probability Calibration Review

- **Observed Test Brier Scores:** Diabetes ($0.1760$), Heart Disease ($0.1081$), CKD ($0.0127$).
- **Review Finding:** While low Brier scores demonstrate consistent ranking and sharp probability separation on these specific benchmark datasets, they do not constitute proof of clinical calibration across diverse real-world patient distributions. Post-hoc calibration remains deferred pending real-world validation data.

---

## 12. Risk-Band Limitations

Educational display bands are defined as:
- **LOW:** $P < 0.30$
- **MODERATE:** $0.30 \le P < 0.70$
- **ELEVATED:** $P \ge 0.70$

These bands are display heuristics for research prototypes. They are NOT clinically validated diagnostic thresholds.

---

## 13. Safety Terminology Audit

Grep audits confirmed:
- Zero occurrences of prohibited claims ("diagnosis", "confirmed disease", "medical certainty", "clinically proven", "doctor-level accuracy") in user-facing code or model descriptions.
- All outputs contain the mandatory non-diagnostic disclaimer.

---

## 14. Test Suite Summary

- **Phase 7 Step 2 unit tests:** 20 passed ([`tests/test_phase7_ml.py`](file:///d:/MedIntel%20AI/tests/test_phase7_ml.py))
- **Phase 7 Step 3 audit tests:** 8 passed ([`tests/test_phase7_audit.py`](file:///d:/MedIntel%20AI/tests/test_phase7_audit.py))
- **Workspace regression suite:** **193 passed, 3 warnings in 10.12s** (165 Phase 1–6 tests + 28 Phase 7 tests). Zero regressions.

---

## 15. Final Audit Conclusion

The Phase 7 ML risk estimation infrastructure, pipelines, models, and external artifacts are verified to be robust, reproducible, and strictly free of target leakage, test-set contamination, or schema mismatches. The system is ready for Phase 7 FastAPI integration in subsequent steps.
