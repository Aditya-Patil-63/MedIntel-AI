# Phase 7: Machine Learning Risk Models — Architecture & Design Document

> MedIntel AI — Intelligent Medical Report Analyzer
>
> Phase 7: ML Risk Models (Step 1: Dataset Audit & Architecture Design)

---

## 1. Executive Summary

Phase 7 designs and implements **machine learning risk-estimation models** for MedIntel AI. The models evaluate multi-feature patient risk profiles for three prevalent chronic health conditions:
1. **Diabetes Risk** (Pima Indians Diabetes Database)
2. **Heart Disease Risk** (UCI Cleveland Heart Disease Dataset)
3. **Chronic Kidney Disease (CKD) Risk** (UCI Chronic Kidney Disease Dataset)

### Core Non-Diagnostic Safety Boundary
- **Educational Risk Indicator Only**: ML models output a continuous **model-estimated risk probability** ($P(\text{target}=1) \in [0.0, 1.0]$) and an associated qualitative risk index (Low / Moderate / Elevated).
- **Strict Non-Diagnostic Constraint**: Models do **NOT** diagnose medical conditions (e.g., *"Patient has stage 3 chronic kidney disease"* or *"Diabetes confirmed"*).
- **Mandatory Medical Disclaimer**: Every prediction artifact, schema, and API response must include:
  > *"This estimated risk score is an educational indicator derived from historical research datasets. It is NOT a medical diagnosis, clinical prognosis, or treatment recommendation. Please consult a qualified healthcare professional for comprehensive medical evaluation."*
- **Deterministic Separation**: High/Critical test values are classified deterministically via the Phase 6 Reference Engine. ML models provide supplementary multivariate risk indicators, never overriding laboratory reference ranges.

---

## 2. Dataset Audit & Provenance (External Storage)

All datasets are stored strictly outside the Git repository under `D:\MedIntel-Datasets\processed\` as prepared in Phase 3.

```
D:\MedIntel-Datasets\
├── raw/                      # Original immutable data downloads
└── processed/                # Phase 3 prepared datasets
    ├── diabetes/
    │   └── diabetes_prepared.csv
    ├── heart_disease/
    │   └── heart_disease_prepared.csv
    └── kidney_disease/
        └── kidney_disease_prepared.csv
```

### 2.1 Diabetes Dataset (Pima Indians Diabetes Database)
- **Source**: National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK) / UCI Machine Learning Repository (DOI: `10.24432/C58K5K`).
- **File**: `D:\MedIntel-Datasets\processed\diabetes\diabetes_prepared.csv`
- **Dimensions**: 768 rows, 9 columns (8 predictors + 1 target).
- **Target**: `Outcome` (integer: `0` = negative class in dataset, `1` = positive class in dataset).
- **Class Balance**:
  - Class `0`: 500 records (65.10%)
  - Class `1`: 268 records (34.90%)
  - Imbalance Ratio: ~1.87 : 1 (mild imbalance).
- **Missing Values**: 0 (no NaN values).
- **Duplicate Rows**: 0.
- **Phase 3 Preprocessing**:
  - Identified physiologically implausible zeros in `Glucose` (5 zeros), `BloodPressure` (35 zeros), `SkinThickness` (227 zeros), `Insulin` (374 zeros), and `BMI` (11 zeros).
  - Replaced implausible zeros with column medians during Phase 3 preparation.
- **Feature Matrix**:
  | # | Feature Name | Data Type | Min | Median | Max | Mean | Std | Clinical Significance |
  |---|---|---|---|---|---|---|---|---|
  | 1 | `Pregnancies` | `int64` | 0 | 3.0 | 17 | 3.85 | 3.37 | Obstetric history |
  | 2 | `Glucose` | `float64` | 44.0 | 117.0 | 199.0 | 121.66 | 30.44 | 2h oral glucose tolerance |
  | 3 | `BloodPressure` | `float64` | 24.0 | 72.0 | 122.0 | 72.39 | 12.10 | Diastolic blood pressure (mm Hg) |
  | 4 | `SkinThickness` | `float64` | 7.0 | 29.0 | 99.0 | 29.11 | 8.79 | Triceps skinfold thickness (mm) |
  | 5 | `Insulin` | `float64` | 14.0 | 125.0 | 846.0 | 140.67 | 86.38 | 2-hour serum insulin ($\mu$U/mL) |
  | 6 | `BMI` | `float64` | 18.2 | 32.3 | 67.1 | 32.46 | 6.88 | Body mass index ($kg/m^2$) |
  | 7 | `DiabetesPedigreeFunction` | `float64` | 0.078 | 0.3725 | 2.42 | 0.472 | 0.331 | Genetic predisposition score |
  | 8 | `Age` | `int64` | 21 | 29.0 | 81 | 33.24 | 11.76 | Patient age in years |

### 2.2 Heart Disease Dataset (UCI Cleveland Processed)
- **Source**: Cleveland Clinic Foundation / UCI ML Repository (DOI: `10.24432/C52P4X`).
- **File**: `D:\MedIntel-Datasets\processed\heart_disease\heart_disease_prepared.csv`
- **Dimensions**: 297 rows, 14 columns (13 predictors + 1 target).
- **Target**: `target` (integer: `0` = absence / negative, `1` = presence / positive).
- **Class Balance**:
  - Class `0`: 160 records (53.87%)
  - Class `1`: 137 records (46.13%)
  - Imbalance Ratio: ~1.17 : 1 (well-balanced).
- **Missing Values**: 0.
- **Duplicate Rows**: 0.
- **Phase 3 Preprocessing**:
  - Removed 6 rows containing missing values (`?` in `ca` or `thal` in raw 303 rows), yielding 297 clean records.
  - Binarized original `num` target ($0 \to 0$; $1, 2, 3, 4 \to 1$).
- **Feature Matrix & Encoding Strategy**:
  | # | Feature | Type | Range / Domain | Representation | Clinical Description |
  |---|---|---|---|---|---|
  | 1 | `age` | Continuous | 29.0 – 77.0 (mean: 54.5) | StandardScaler | Age in years |
  | 2 | `sex` | Binary | 0.0 (F), 1.0 (M) | Passthrough | Biological sex |
  | 3 | `cp` | Categorical | 1.0, 2.0, 3.0, 4.0 | OneHotEncoder | Chest pain type (1: typical, 2: atypical, 3: non-anginal, 4: asymptomatic) |
  | 4 | `trestbps` | Continuous | 94.0 – 200.0 (mean: 131.7) | StandardScaler | Resting systolic blood pressure (mm Hg) |
  | 5 | `chol` | Continuous | 126.0 – 564.0 (mean: 247.4) | StandardScaler | Serum total cholesterol (mg/dL) |
  | 6 | `fbs` | Binary | 0.0 ($< 120$), 1.0 ($> 120$) | Passthrough | Fasting blood sugar $> 120$ mg/dL |
  | 7 | `restecg` | Categorical | 0.0, 1.0, 2.0 | OneHotEncoder | Resting ECG (0: normal, 1: ST-T wave abn, 2: LVH) |
  | 8 | `thalach` | Continuous | 71.0 – 202.0 (mean: 149.6) | StandardScaler | Maximum heart rate achieved during exercise |
  | 9 | `exang` | Binary | 0.0 (no), 1.0 (yes) | Passthrough | Exercise-induced angina |
  | 10 | `oldpeak` | Continuous | 0.0 – 6.2 (mean: 1.06) | StandardScaler | ST depression induced by exercise relative to rest |
  | 11 | `slope` | Categorical | 1.0, 2.0, 3.0 | OneHotEncoder | Peak exercise ST segment slope (1: up, 2: flat, 3: down) |
  | 12 | `ca` | Count/Discrete | 0.0, 1.0, 2.0, 3.0 | OneHotEncoder / Count | Number of major vessels colored by fluoroscopy |
  | 13 | `thal` | Categorical | 3.0, 6.0, 7.0 | OneHotEncoder | Thallium stress scintigraphy (3: normal, 6: fixed, 7: reversible) |

### 2.3 Chronic Kidney Disease Dataset (UCI CKD)
- **Source**: Apollo Hospitals, Karaikudi, Tamil Nadu, India / UCI ML Repository (DOI: `10.24432/C5G020`).
- **File**: `D:\MedIntel-Datasets\processed\kidney_disease\kidney_disease_prepared.csv`
- **Dimensions**: 400 rows, 25 columns (24 predictors + 1 target).
- **Target**: `classification` (integer: `1` = CKD, `0` = Not CKD).
- **Class Balance**:
  - Class `1`: 250 records (62.50%)
  - Class `0`: 150 records (37.50%)
  - Imbalance Ratio: ~1.67 : 1 (mild imbalance).
- **Missing Values**: 0.
- **Duplicate Rows**: 0.
- **Phase 3 Preprocessing**:
  - Dropped raw patient identifier (`id`).
  - Cleaned textual inconsistencies and whitespace.
  - Imputed numeric columns using column medians, and categorical columns using modes.
- **Feature Matrix**:
  - **14 Numerical Features**:
    - `age` (2.0 – 90.0, median: 55.0)
    - `bp` (blood pressure: 50.0 – 180.0 mm Hg, median: 80.0)
    - `sg` (specific gravity: 1.005 – 1.025, median: 1.020)
    - `al` (albumin dipstick: 0.0 – 5.0, median: 0.0)
    - `su` (sugar dipstick: 0.0 – 5.0, median: 0.0)
    - `bgr` (blood glucose random: 22.0 – 490.0 mg/dL, median: 121.0)
    - `bu` (blood urea: 1.5 – 391.0 mg/dL, median: 42.0)
    - `sc` (serum creatinine: 0.4 – 76.0 mg/dL, median: 1.30)
    - `sod` (serum sodium: 4.5 – 163.0 mEq/L, median: 138.0) *[Note: 4.5 is a historical UCI data entry artifact]*
    - `pot` (serum potassium: 2.5 – 47.0 mEq/L, median: 4.40) *[Note: 47.0 is a historical UCI data entry artifact]*
    - `hemo` (hemoglobin: 3.1 – 17.8 g/dL, median: 12.65)
    - `pcv` (packed cell volume: 9.0 – 54.0 %, median: 40.0)
    - `wc` (white blood cell count: 2,200 – 26,400 cells/$\mu$L, median: 8,000)
    - `rc` (red blood cell count: 2.1 – 8.0 $10^6/\mu$L, median: 4.80)
  - **10 Categorical / Binary Features**:
    - `rbc` (`normal`, `abnormal`)
    - `pc` (`normal`, `abnormal`)
    - `pcc` (`notpresent`, `present`)
    - `ba` (`notpresent`, `present`)
    - `htn` (`yes`, `no`)
    - `dm` (`yes`, `no`)
    - `cad` (`no`, `yes`)
    - `appet` (`good`, `poor`)
    - `pe` (`no`, `yes`)
    - `ane` (`no`, `yes`)

---

## 3. Data Leakage Audit & Prevention Strategy

### 3.1 Investigation Findings
1. **Target-Derived Columns**: Audited all feature sets to ensure no feature was computed from or directly encodes the target column. In Heart Disease, original multiclass `num` is dropped; in CKD, original `class` string is replaced by binary `classification`.
2. **Identifier Columns**: Patient `id` was stripped in Phase 3. No record numbers, row indices, or hospital patient IDs remain.
3. **Phase 3 Global Imputation Consideration**:
   - In Phase 3, dataset preparation was completed prior to splitting into train/test splits.
   - For Phase 7, the prepared files are treated as immutable benchmark inputs.
   - **Downstream Mitigation**: To guarantee strict isolation in Phase 7, **any new learned preprocessing** (e.g., standard scaling, one-hot encoding, feature normalization) **MUST be fitted exclusively on the training folds** of `X_train`. The test set will be transformed using the pre-fitted transformer, with zero fitting on test or cross-validation holdouts.

---

## 4. Evaluation Strategy: Stratified CV + One-Time Held-Out Test Split

Due to relatively small sample sizes (Diabetes: 768, Heart: 297, CKD: 400), evaluation must maximize statistical power while rigorously guarding the held-out test split against data snooping.

```
Full Prepared Dataset
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 80% Training Split (Stratified, Seed=42)               │
│                                                        │
│  5-Fold Stratified Cross-Validation                    │
│  ├── Fold 1: Train on 4 folds, validate on 1 fold      │
│  ├── Fold 2: Train on 4 folds, validate on 1 fold      │
│  ├── Fold 3: Train on 4 folds, validate on 1 fold      │
│  ├── Fold 4: Train on 4 folds, validate on 1 fold      │
│  └── Fold 5: Train on 4 folds, validate on 1 fold      │
│                                                        │
│  → Preprocessing fit strictly inside training folds    │
│  → Model comparison & hyperparameter tuning on CV      │
│  → Selection of champion model architecture            │
│  → Fit final Pipeline on entire 80% Training Split     │
└────────────────────────────────────────────────────────┘
         │
         ▼ [ONE-TIME FINAL EVALUATION ONLY]
┌────────────────────────────────────────────────────────┐
│ 20% Held-Out Test Split (Stratified, Seed=42)          │
│                                                        │
│  → Frozen and completely untouched during development   │
│  → Zero tuning, zero threshold adjustment              │
│  → Evaluates final out-of-sample generalization        │
└────────────────────────────────────────────────────────┘
```

### Dataset Split Sizes

| Dataset | Total Samples | 80% Train Set (CV) | 20% Held-Out Test Set | Stratification Variable |
|---|---|---|---|---|
| **Diabetes** | 768 | 614 samples (400 neg / 214 pos) | 154 samples (100 neg / 54 pos) | `Outcome` |
| **Heart Disease** | 297 | 237 samples (128 neg / 109 pos) | 60 samples (32 neg / 28 pos) | `target` |
| **Chronic Kidney Disease** | 400 | 320 samples (120 neg / 200 pos) | 80 samples (30 neg / 50 pos) | `classification` |

---

## 5. Model Candidates for Evaluation

For each condition, two to three structurally diverse model families will be systematically evaluated:

1. **Logistic Regression (L2 Regularization)**:
   - **Rationale**: Highly interpretable, well-calibrated baseline probabilities, robust against overfitting on small $N$.
   - **Hyperparameters**: Regularization strength $C \in [0.01, 0.1, 1.0, 10.0]$, solver `lbfgs`, `class_weight='balanced'`.
2. **Random Forest Classifier**:
   - **Rationale**: Captures non-linear clinical interactions without requiring linear feature assumptions; provides out-of-bag estimates and feature importance.
   - **Hyperparameters**: `n_estimators=100`, `max_depth` restricted ($\le 6$) to prevent overfitting on small tabular samples, `min_samples_split \ge 4`, `class_weight='balanced'`.
3. **Gradient Boosting Classifier (`HistGradientBoostingClassifier` / `GradientBoostingClassifier`)**:
   - **Rationale**: State-of-the-art tabular performance; handles mixed continuous and categorical feature distributions effectively.
   - **Hyperparameters**: `learning_rate \in [0.05, 0.1]`, `max_iter=100`, `max_depth=3`.

*Selection Rule*: The champion model is selected based on a balanced assessment of cross-validated **ROC-AUC**, **Recall / Sensitivity**, and **Brier Score** (calibration), never raw accuracy alone.

---

## 6. Preprocessing Architecture: `ColumnTransformer` + `Pipeline`

All preprocessing and model weights will be encapsulated into a single unified `sklearn.pipeline.Pipeline` object to ensure zero train/inference drift.

```python
Pipeline([
    ("preprocessor", ColumnTransformer([
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), categorical_features)
    ])),
    ("classifier", ChampionModel(random_state=42))
])
```

- **Diabetes**: All 8 features are continuous numeric $\to$ `StandardScaler()`.
- **Heart Disease**:
  - Continuous (`age`, `trestbps`, `chol`, `thalach`, `oldpeak`) $\to$ `StandardScaler()`.
  - Binary (`sex`, `fbs`, `exang`) $\to$ passthrough.
  - Multi-class categorical (`cp`, `restecg`, `slope`, `ca`, `thal`) $\to$ `OneHotEncoder(drop="first", handle_unknown="ignore")`.
- **CKD**:
  - 14 numeric features $\to$ `StandardScaler()`.
  - 10 categorical features $\to$ `OneHotEncoder(drop="first", handle_unknown="ignore")`.

---

## 7. Class Imbalance Handling

- **Diabetes**: 34.9% positive (1.87:1 ratio) — mild.
- **Heart Disease**: 46.1% positive (1.17:1 ratio) — balanced.
- **CKD**: 62.5% positive (1.67:1 ratio) — mild (positive class is majority).
- **Decision**:
  - **SMOTE is REJECTED**: In small clinical tabular datasets ($N < 1000$) with discrete laboratory cutoffs, synthetic k-NN interpolation frequently generates clinically impossible combinations (e.g. impossible combinations of urine specific gravity and serum creatinine).
  - **Method**: Use `class_weight='balanced'` in estimators and enforce `StratifiedKFold` across all splits.

---

## 8. Evaluation Metrics

Because MedIntel AI provides **risk screening indicators** rather than confirmatory diagnostics, evaluation must reflect clinical risk tradeoffs:

1. **Recall / Sensitivity ($TPR = \frac{TP}{TP + FN}$)**: Primary metric. False negatives (missing a high-risk individual) carry high potential clinical cost.
2. **Specificity ($TNR = \frac{TN}{TN + FP}$)**: Essential to guard against alert fatigue and unnecessary anxiety from excessive false positives.
3. **Precision / PPV ($PPV = \frac{TP}{TP + FP}$)**: Assesses the reliability of a positive risk alert.
4. **F1-Score**: Harmonic mean of precision and recall.
5. **ROC-AUC**: Discriminative power across all possible decision thresholds.
6. **Brier Score ($Brier = \frac{1}{N}\sum (p_i - y_i)^2$)**: Evaluates probability calibration accuracy. Lower is better ($0.0$ is perfect probability forecast).

---

## 9. Probability / Risk Semantics

- **Model Output**: $P(\text{Risk} = 1) = \text{pipeline.predict\_proba}(X)[:, 1]$.
- **Calibration Check**: If tree ensembles exhibit sigmoid distortion, probability calibration will be evaluated using `CalibratedClassifierCV(method='sigmoid', cv='prefit')` fitted exclusively on training validation folds.
- **Categorization for Educational Display**:
  - **Low Risk Indicator**: $P < 0.30$
  - **Moderate Risk Indicator**: $0.30 \le P < 0.70$
  - **Elevated Risk Indicator**: $P \ge 0.70$

---

## 10. Feature Mapping: Phase 6 Reference Engine $\to$ Phase 7 ML Models

A routine medical lab report contains only laboratory test results. Many ML features in academic datasets represent clinical questionnaire items or specialized diagnostic procedures.

### 10.1 Diabetes Risk Model (8 Features)
| ML Feature | Type | Phase 6 Canonical Analytes / Extraction Source | Extractability Status |
|---|---|---|---|
| `Glucose` | Numeric | `Fasting Blood Glucose` | **DIRECTLY EXTRACTABLE** |
| `BloodPressure` | Numeric | Systolic/Diastolic blood pressure from vitals text | **POTENTIALLY EXTRACTABLE** |
| `BMI` | Numeric | Body Mass Index from vitals header or calculated | **POTENTIALLY EXTRACTABLE** |
| `Insulin` | Numeric | Fasting Serum Insulin | **POTENTIALLY EXTRACTABLE** |
| `Age` | Demographic | Patient demographic context (`PatientContext.age`) | **QUESTIONNAIRE / CONTEXT** |
| `Pregnancies` | Demographic | Self-reported obstetric history | **QUESTIONNAIRE / DEMOGRAPHIC** |
| `DiabetesPedigreeFunction` | Score | Calculated family history pedigree score | **QUESTIONNAIRE / DEMOGRAPHIC** |
| `SkinThickness` | Physical Exam | Triceps skinfold measurement with calipers | **NOT CURRENTLY SUPPORTED** |

### 10.2 Heart Disease Risk Model (13 Features)
| ML Feature | Type | Phase 6 Canonical Analytes / Extraction Source | Extractability Status |
|---|---|---|---|
| `chol` | Numeric | `Total Cholesterol` | **DIRECTLY EXTRACTABLE** |
| `fbs` | Binary | Derived from `Fasting Blood Glucose` ($> 120 \to 1$) | **DIRECTLY EXTRACTABLE** |
| `trestbps` | Numeric | Resting systolic blood pressure from vitals | **POTENTIALLY EXTRACTABLE** |
| `age` | Demographic | `PatientContext.age` | **QUESTIONNAIRE / CONTEXT** |
| `sex` | Demographic | `PatientContext.sex` ($M \to 1, F \to 0$) | **QUESTIONNAIRE / CONTEXT** |
| `cp` | Clinical | Chest pain type (typical, atypical, non-anginal, none) | **QUESTIONNAIRE / CLINICAL SYMPTOM** |
| `exang` | Clinical | Exercise-induced angina | **QUESTIONNAIRE / CLINICAL SYMPTOM** |
| `thalach` | Diagnostic | Max heart rate during treadmill stress test | **POTENTIALLY EXTRACTABLE / STRESS TEST** |
| `restecg` | Diagnostic | Resting 12-lead ECG findings | **NOT CURRENTLY SUPPORTED / ECG** |
| `oldpeak` | Diagnostic | Exercise-induced ST depression | **NOT CURRENTLY SUPPORTED / STRESS ECG** |
| `slope` | Diagnostic | Peak exercise ST segment slope | **NOT CURRENTLY SUPPORTED / STRESS ECG** |
| `ca` | Diagnostic | Fluoroscopy major vessel count | **NOT CURRENTLY SUPPORTED / IMAGING** |
| `thal` | Diagnostic | Thallium nuclear scintigraphy result | **NOT CURRENTLY SUPPORTED / NUCLEAR IMAGING** |

### 10.3 Chronic Kidney Disease Risk Model (24 Features)
| ML Feature | Type | Phase 6 Canonical Analytes / Extraction Source | Extractability Status |
|---|---|---|---|
| `bgr` | Numeric | `Fasting Blood Glucose` / Random Blood Glucose | **DIRECTLY EXTRACTABLE** |
| `bu` | Numeric | `Blood Urea Nitrogen` | **DIRECTLY EXTRACTABLE** |
| `sc` | Numeric | `Serum Creatinine` | **DIRECTLY EXTRACTABLE** |
| `sod` | Numeric | `Serum Sodium` | **DIRECTLY EXTRACTABLE** |
| `pot` | Numeric | `Serum Potassium` | **DIRECTLY EXTRACTABLE** |
| `hemo` | Numeric | `Hemoglobin` | **DIRECTLY EXTRACTABLE** |
| `wc` | Numeric | `White Blood Cell Count` | **DIRECTLY EXTRACTABLE** |
| `bp` | Numeric | Blood pressure from vitals | **POTENTIALLY EXTRACTABLE** |
| `sg` | Numeric | Urine specific gravity | **POTENTIALLY EXTRACTABLE** |
| `al` | Numeric | Urine albumin dipstick | **POTENTIALLY EXTRACTABLE** |
| `su` | Numeric | Urine sugar dipstick | **POTENTIALLY EXTRACTABLE** |
| `pcv` | Numeric | Packed cell volume / Hematocrit | **POTENTIALLY EXTRACTABLE** |
| `rc` | Numeric | Red blood cell count | **POTENTIALLY EXTRACTABLE** |
| `rbc` | Categorical | Urine red blood cells (normal/abnormal) | **POTENTIALLY EXTRACTABLE** |
| `pc` | Categorical | Urine pus cells (normal/abnormal) | **POTENTIALLY EXTRACTABLE** |
| `pcc` | Categorical | Pus cell clumps in urine | **POTENTIALLY EXTRACTABLE** |
| `ba` | Categorical | Bacteria in urine | **POTENTIALLY EXTRACTABLE** |
| `age` | Demographic | `PatientContext.age` | **QUESTIONNAIRE / CONTEXT** |
| `htn` | History | History of hypertension | **QUESTIONNAIRE / CLINICAL HISTORY** |
| `dm` | History | History of diabetes | **QUESTIONNAIRE / CLINICAL HISTORY** |
| `cad` | History | History of coronary artery disease | **QUESTIONNAIRE / CLINICAL HISTORY** |
| `appet` | Symptom | Appetite (good/poor) | **QUESTIONNAIRE / SYMPTOM** |
| `pe` | Sign | Pedal edema (present/absent) | **QUESTIONNAIRE / CLINICAL SIGN** |
| `ane` | Sign | Anemia diagnosis/sign | **QUESTIONNAIRE / CLINICAL SIGN** |

---

## 11. Missing Feature Policy: `INSUFFICIENT_FEATURES`

The system must never guess or fabricate missing data during model inference.

### Rules:
1. If a caller requests a risk estimation without supplying all required features for that model:
   - The engine returns `status = "INSUFFICIENT_FEATURES"`.
   - The engine returns `risk_score = None`.
   - The engine returns an informative payload listing `missing_features`, `supplied_features_count`, and `required_features_count`.
2. Silent zero-imputation, mean imputation, or arbitrary default assignment at inference time is **strictly prohibited**.

---

## 12. External Artifact Storage Specification

Trained models and evaluation metadata will reside outside Git:

```
D:\MedIntel-Datasets\ml_models\
├── diabetes\
│   ├── pipeline.joblib
│   └── model_metadata.json
├── heart_disease\
│   ├── pipeline.joblib
│   └── model_metadata.json
└── kidney_disease\
    ├── pipeline.joblib
    └── model_metadata.json
```

### Metadata Schema (`model_metadata.json`)
```json
{
  "model_name": "diabetes_risk_estimator",
  "condition": "diabetes",
  "model_type": "LogisticRegression",
  "dataset_provenance": {
    "source": "Pima Indians Diabetes Database",
    "doi": "10.24432/C58K5K",
    "total_rows": 768,
    "sha256": "..."
  },
  "random_seed": 42,
  "features": [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
  ],
  "environment": {
    "python_version": "3.12.10",
    "scikit_learn_version": "...",
    "numpy_version": "2.5.3",
    "pandas_version": "3.0.5"
  },
  "cross_validation_metrics": {
    "accuracy_mean": 0.0,
    "recall_mean": 0.0,
    "specificity_mean": 0.0,
    "f1_mean": 0.0,
    "roc_auc_mean": 0.0,
    "brier_score_mean": 0.0
  },
  "held_out_test_metrics": {
    "accuracy": 0.0,
    "recall": 0.0,
    "specificity": 0.0,
    "f1": 0.0,
    "roc_auc": 0.0,
    "brier_score": 0.0
  },
  "training_timestamp": "2026-09-10T...",
  "artifact_sha256": "...",
  "disclaimer": "This estimated risk score is an educational indicator derived from historical research datasets. It is NOT a medical diagnosis, clinical prognosis, or treatment recommendation. Please consult a qualified healthcare professional for comprehensive medical evaluation."
}
```

---

## 13. ML Module Directory Layout

```
ml/
├── __init__.py
├── common/
│   ├── __init__.py
│   ├── base_model.py         # Abstract base class for risk estimators
│   ├── metrics.py            # Comprehensive evaluation metric calculation
│   └── schemas.py            # Pydantic schemas for risk prediction input/output
├── diabetes/
│   ├── __init__.py
│   ├── features.py           # Feature definitions and validator
│   └── pipeline.py           # Pipeline factory
├── heart_disease/
│   ├── __init__.py
│   ├── features.py
│   └── pipeline.py
├── kidney_disease/
│   ├── __init__.py
│   ├── features.py
│   └── pipeline.py
├── training/
│   ├── __init__.py
│   ├── cross_validator.py    # Stratified K-fold runner
│   └── train.py              # Main training script (Phase 7 Step 2)
├── evaluation/
│   ├── __init__.py
│   └── evaluate.py           # Test set evaluation and calibration runner
├── inference/
│   ├── __init__.py
│   └── predictor.py          # Unified inference interface with missing-feature enforcement
├── data/                     # Phase 3 documentation and metadata
├── scripts/                  # Phase 3 data preparation scripts
└── README.md
```

---

## 14. Reproducibility Configuration

- **Operating System**: Windows 11 (10.0.26200-SP0)
- **Python Runtime**: Python 3.12.10 (64-bit AMD64)
- **Execution Target**: CPU (classical tabular models require zero GPU acceleration)
- **Random Seed**: Fixed `RANDOM_SEED = 42` across all splits, cross-validation folds, and stochastic estimators.
- **Package Versions**:
  - `pandas`: 3.0.5
  - `numpy`: 2.5.3
  - `scikit-learn`: to be installed in `backend/venv` for Phase 7 Step 2.
