# Phase 7 — ML Risk Models: Training, Cross-Validation & Evaluation Report

> **MedIntel AI — Research Prototype Risk Models**  
> **Status:** Step 2 Complete (Leakage-Safe Training, 5-Fold CV, Champion Selection, and Evaluation)  
> **Mandatory Medical Disclaimer:** These models provide continuous *model-estimated risk probabilities* derived from historical research benchmarks for educational screening prototypes. They do NOT provide a clinical diagnosis, medical prognosis, or treatment recommendation.

---

## 1. Environment & Dependencies

| Package / Runtime | Actual Version Verified | Purpose |
|-------------------|-------------------------|---------|
| **Python** | `3.12.10` (AMD64, Windows 11) | Core runtime |
| **scikit-learn** | `1.9.0` | ML algorithms, preprocessing pipelines, metrics |
| **pandas** | `3.0.5` | Tabular data manipulation & schema validation |
| **numpy** | `2.5.3` | Numerical arrays and matrix operations |
| **joblib** | `1.6.0` | Serialization of trained Pipeline artifacts |
| **scipy** | `1.18.1` | Scientific computing backend for scikit-learn |

---

## 2. Dataset Paths, Shapes & Target Distributions

All datasets were loaded from the external prepared storage (`MEDINTEL_DATA_DIR/processed/`):

| Condition | Prepared CSV Path | Rows | Total Features | Target Column | Positive Class Prevalence |
|---|---|---|---|---|---|
| **Diabetes** | `D:\MedIntel-Datasets\processed\diabetes\diabetes_prepared.csv` | 768 | 8 numeric | `Outcome` | 268 / 768 (34.9%) |
| **Heart Disease** | `D:\MedIntel-Datasets\processed\heart_disease\heart_disease_prepared.csv` | 297 | 13 (5 cont, 3 bin, 5 cat) | `target` | 137 / 297 (46.1%) |
| **Chronic Kidney Disease** | `D:\MedIntel-Datasets\processed\kidney_disease\kidney_disease_prepared.csv` | 400 | 24 (14 num, 10 cat) | `classification` | 250 / 400 (62.5%) |

---

## 3. Preprocessing Architecture & Leakage Prevention

Learned preprocessing operations are encapsulated inside `sklearn.pipeline.Pipeline` with `sklearn.compose.ColumnTransformer`.

### Leakage-Safe Rules:
1. **Zero Data Leakage:** Preprocessing steps (`StandardScaler`, `OneHotEncoder`) are fit strictly on training folds during 5-fold cross-validation.
2. **Untouched Held-Out Test Set:** The 20% test partition is split once (`random_state=42`, stratified) and held completely untouched during CV and model selection.
3. **No SMOTE:** Synthetic sample generation is prohibited on small tabular clinical data; class imbalance is addressed using `class_weight='balanced'` and stratified splitting.
4. **Categorical Handling:** `OneHotEncoder(drop='first', handle_unknown='ignore')` safely handles unknown categorical categories at inference time without throwing exceptions.

### Preprocessing Pipelines:
- **Diabetes:** `StandardScaler` applied to all 8 continuous clinical predictors.
- **Heart Disease:** `StandardScaler` on 5 continuous features (`age`, `trestbps`, `chol`, `thalach`, `oldpeak`), passthrough on 3 binary features (`sex`, `fbs`, `exang`), and `OneHotEncoder(drop='first', handle_unknown='ignore')` on 5 categorical features (`cp`, `restecg`, `slope`, `ca`, `thal`).
- **Chronic Kidney Disease:** `StandardScaler` on 14 numerical features, and `OneHotEncoder(drop='first', handle_unknown='ignore')` on 10 categorical features (`rbc`, `pc`, `pcc`, `ba`, `htn`, `dm`, `cad`, `appet`, `pe`, `ane`).

---

## 4. Candidate Models & Hyperparameter Grids

For each disease condition, 10 candidate models were evaluated under identical 5-fold Stratified CV:

1. **Logistic Regression (4 variants):**
   - Solver: `lbfgs`, penalty: `l2`, `class_weight='balanced'`, `max_iter=1000`, `random_state=42`
   - $C \in \{0.01, 0.1, 1.0, 10.0\}$
2. **Random Forest (4 variants):**
   - Regularized for small sample sizes, `n_estimators=100`, `class_weight='balanced'`, `random_state=42`
   - $\text{max\_depth} \in \{4, 6\}$, $\text{min\_samples\_split} \in \{4, 8\}$
3. **HistGradientBoosting (2 variants):**
   - Depth-constrained, `max_iter=100`, `max_depth=3`, `class_weight='balanced'`, `random_state=42`
   - $\text{learning\_rate} \in \{0.05, 0.1\}$

---

## 5. Cross-Validation Results (5-Fold Stratified CV on 80% Train Split)

### 5.1 Diabetes Risk Models (Train $N=614$)

| Candidate Name | Recall (Sensitivity) | ROC-AUC | Specificity | Brier Score | F1 Score | Status |
|---|---|---|---|---|---|---|
| `LogisticRegression_C0.01` | $0.7103 \pm 0.0375$ | $0.8403 \pm 0.0112$ | $0.7725 \pm 0.0366$ | $0.1733 \pm 0.0075$ | $0.6651 \pm 0.0206$ | Candidate |
| `LogisticRegression_C0.1` | $0.7152 \pm 0.0507$ | $0.8452 \pm 0.0126$ | $0.7925 \pm 0.0302$ | $0.1602 \pm 0.0107$ | $0.6794 \pm 0.0180$ | Candidate |
| `LogisticRegression_C1.0` | $0.7010 \pm 0.0395$ | $0.8441 \pm 0.0164$ | $0.7950 \pm 0.0322$ | $0.1597 \pm 0.0120$ | $0.6724 \pm 0.0133$ | Candidate |
| `LogisticRegression_C10.0` | $0.7010 \pm 0.0395$ | $0.8437 \pm 0.0171$ | $0.7950 \pm 0.0322$ | $0.1598 \pm 0.0122$ | $0.6724 \pm 0.0133$ | Candidate |
| `RandomForest_d4_s4` | $0.7569 \pm 0.0354$ | $0.8383 \pm 0.0167$ | $0.7725 \pm 0.0348$ | $0.1660 \pm 0.0098$ | $0.6939 \pm 0.0247$ | Candidate |
| **`RandomForest_d4_s8`** | $\mathbf{0.7663 \pm 0.0256}$ | $\mathbf{0.8393 \pm 0.0176}$ | $\mathbf{0.7675 \pm 0.0332}$ | $\mathbf{0.1655 \pm 0.0098}$ | $\mathbf{0.6966 \pm 0.0200}$ | **CHAMPION** |
| `RandomForest_d6_s4` | $0.7336 \pm 0.0181$ | $0.8373 \pm 0.0199$ | $0.7725 \pm 0.0278$ | $0.1619 \pm 0.0118$ | $0.6799 \pm 0.0142$ | Candidate |
| `RandomForest_d6_s8` | $0.7383 \pm 0.0172$ | $0.8330 \pm 0.0207$ | $0.7725 \pm 0.0348$ | $0.1634 \pm 0.0114$ | $0.6829 \pm 0.0112$ | Candidate |
| `HistGradientBoosting_lr0.05_d3` | $0.7568 \pm 0.0511$ | $0.8304 \pm 0.0198$ | $0.7675 \pm 0.0392$ | $0.1642 \pm 0.0121$ | $0.6904 \pm 0.0176$ | Candidate |
| `HistGradientBoosting_lr0.1_d3` | $0.7100 \pm 0.0478$ | $0.8141 \pm 0.0183$ | $0.7775 \pm 0.0229$ | $0.1724 \pm 0.0119$ | $0.6674 \pm 0.0272$ | Candidate |

### 5.2 Heart Disease Risk Models (Train $N=237$)

| Candidate Name | Recall (Sensitivity) | ROC-AUC | Specificity | Brier Score | F1 Score | Status |
|---|---|---|---|---|---|---|
| `LogisticRegression_C0.01` | $0.7242 \pm 0.1531$ | $0.8698 \pm 0.0876$ | $0.8277 \pm 0.1020$ | $0.1852 \pm 0.0149$ | $0.7472 \pm 0.0975$ | Candidate |
| `LogisticRegression_C0.1` | $0.7693 \pm 0.1324$ | $0.8918 \pm 0.0719$ | $0.8591 \pm 0.0859$ | $0.1409 \pm 0.0328$ | $0.7921 \pm 0.0846$ | Candidate |
| **`LogisticRegression_C1.0`** | $\mathbf{0.7965 \pm 0.1349}$ | $\mathbf{0.8991 \pm 0.0729}$ | $\mathbf{0.8591 \pm 0.0859}$ | $\mathbf{0.1327 \pm 0.0453}$ | $\mathbf{0.8087 \pm 0.0887}$ | **CHAMPION** |
| `LogisticRegression_C10.0` | $0.7879 \pm 0.1054$ | $0.8977 \pm 0.0705$ | $0.8274 \pm 0.1035$ | $0.1337 \pm 0.0540$ | $0.7919 \pm 0.0807$ | Candidate |
| `RandomForest_d4_s4` | $0.7329 \pm 0.1230$ | $0.8841 \pm 0.0634$ | $0.8434 \pm 0.1171$ | $0.1501 \pm 0.0203$ | $0.7639 \pm 0.0776$ | Candidate |
| `RandomForest_d4_s8` | $0.7238 \pm 0.1280$ | $0.8819 \pm 0.0673$ | $0.8434 \pm 0.1171$ | $0.1516 \pm 0.0222$ | $0.7574 \pm 0.0798$ | Candidate |
| `RandomForest_d6_s4` | $0.7692 \pm 0.1226$ | $0.8806 \pm 0.0742$ | $0.8434 \pm 0.1146$ | $0.1485 \pm 0.0290$ | $0.7864 \pm 0.0769$ | Candidate |
| `RandomForest_d6_s8` | $0.7420 \pm 0.1170$ | $0.8862 \pm 0.0690$ | $0.8280 \pm 0.1325$ | $0.1473 \pm 0.0286$ | $0.7632 \pm 0.0641$ | Candidate |
| `HistGradientBoosting_lr0.05_d3` | $0.7602 \pm 0.1018$ | $0.8896 \pm 0.0441$ | $0.8280 \pm 0.0872$ | $0.1416 \pm 0.0249$ | $0.7729 \pm 0.0450$ | Candidate |
| `HistGradientBoosting_lr0.1_d3` | $0.7515 \pm 0.0961$ | $0.8819 \pm 0.0363$ | $0.7816 \pm 0.0893$ | $0.1464 \pm 0.0229$ | $0.7466 \pm 0.0248$ | Candidate |

### 5.3 Chronic Kidney Disease Risk Models (Train $N=320$)

| Candidate Name | Recall (Sensitivity) | ROC-AUC | Specificity | Brier Score | F1 Score | Status |
|---|---|---|---|---|---|---|
| `LogisticRegression_C0.01` | $0.9400 \pm 0.0255$ | $0.9990 \pm 0.0016$ | $1.0000 \pm 0.0000$ | $0.0738 \pm 0.0048$ | $0.9689 \pm 0.0136$ | Candidate |
| `LogisticRegression_C0.1` | $0.9700 \pm 0.0292$ | $0.9992 \pm 0.0017$ | $1.0000 \pm 0.0000$ | $0.0241 \pm 0.0066$ | $0.9845 \pm 0.0151$ | Candidate |
| `LogisticRegression_C1.0` | $0.9900 \pm 0.0200$ | $0.9998 \pm 0.0004$ | $0.9917 \pm 0.0167$ | $0.0100 \pm 0.0064$ | $0.9924 \pm 0.0102$ | Candidate |
| **`LogisticRegression_C10.0`** | $\mathbf{1.0000 \pm 0.0000}$ | $\mathbf{1.0000 \pm 0.0000}$ | $\mathbf{0.9833 \pm 0.0333}$ | $\mathbf{0.0057 \pm 0.0046}$ | $\mathbf{0.9951 \pm 0.0098}$ | **CHAMPION** |
| `RandomForest_d4_s4` | $1.0000 \pm 0.0000$ | $0.9996 \pm 0.0008$ | $0.9833 \pm 0.0204$ | $0.0132 \pm 0.0041$ | $0.9951 \pm 0.0060$ | Candidate |
| `RandomForest_d4_s8` | $1.0000 \pm 0.0000$ | $0.9996 \pm 0.0008$ | $0.9833 \pm 0.0204$ | $0.0134 \pm 0.0045$ | $0.9951 \pm 0.0060$ | Candidate |
| `RandomForest_d6_s4` | $1.0000 \pm 0.0000$ | $0.9994 \pm 0.0008$ | $0.9833 \pm 0.0204$ | $0.0104 \pm 0.0045$ | $0.9951 \pm 0.0060$ | Candidate |
| `RandomForest_d6_s8` | $0.9950 \pm 0.0100$ | $0.9994 \pm 0.0008$ | $0.9833 \pm 0.0204$ | $0.0111 \pm 0.0048$ | $0.9925 \pm 0.0061$ | Candidate |
| `HistGradientBoosting_lr0.05_d3` | $0.9950 \pm 0.0100$ | $0.9994 \pm 0.0008$ | $0.9917 \pm 0.0167$ | $0.0072 \pm 0.0063$ | $0.9950 \pm 0.0061$ | Candidate |
| `HistGradientBoosting_lr0.1_d3` | $0.9900 \pm 0.0122$ | $0.9996 \pm 0.0008$ | $0.9917 \pm 0.0167$ | $0.0063 \pm 0.0057$ | $0.9925 \pm 0.0062$ | Candidate |

---

## 6. Champion Selection Rationale

The champion model selection is strictly deterministic and adheres to the screening-oriented hierarchy:
1. **Recall / Sensitivity:** Highest priority to minimize missed potential risk indicators.
2. **ROC-AUC:** Second priority for global discrimination across decision boundaries.
3. **Specificity:** Third priority to minimize false alarms.
4. **Brier Score:** Fourth priority to prefer well-calibrated continuous risk scores.
5. **Model Simplicity:** Final tie-breaker (`LogisticRegression` > `RandomForest` > `HistGradientBoosting`).

### Selected Champions:
- **Diabetes:** `RandomForest_d4_s8` achieved the highest mean CV recall ($0.7663$), outperforming Logistic Regression ($0.7010$–$0.7152$) while maintaining balanced specificity ($0.7675$) and low Brier score ($0.1655$).
- **Heart Disease:** `LogisticRegression_C1.0` achieved the highest mean CV recall ($0.7965$) and highest ROC-AUC ($0.8991$), with lowest Brier score ($0.1327$) and superior parsimony.
- **Chronic Kidney Disease:** `LogisticRegression_C10.0` achieved perfect mean CV recall ($1.0000$) and ROC-AUC ($1.0000$), lowest Brier score ($0.0057$), and highest simplicity.

---

## 7. Single Held-Out Test Set Evaluation

Each selected champion was refit on the complete 80% training set and evaluated **exactly once** on the untouched 20% test set:

| Metric | Diabetes (`RandomForest_d4_s8`) | Heart Disease (`LogisticRegression_C1.0`) | CKD (`LogisticRegression_C10.0`) |
|---|---|---|---|
| **Test Set Size ($N$)** | 154 | 60 | 80 |
| **Accuracy** | 0.7468 | 0.8333 | 0.9750 |
| **Precision** | 0.6056 | 0.8462 | 1.0000 |
| **Recall / Sensitivity** | **0.7963** | **0.7857** | **0.9600** |
| **Specificity** | 0.7200 | 0.8750 | 1.0000 |
| **F1 Score** | 0.6880 | 0.8148 | 0.9796 |
| **ROC-AUC** | 0.8122 | 0.9286 | 0.9993 |
| **PR-AUC** | 0.6838 | 0.9153 | 0.9996 |
| **Brier Score** | 0.1760 | 0.1081 | 0.0127 |
| **Decision Threshold** | 0.50 (default) | 0.50 (default) | 0.50 (default) |

### Confusion Matrices (Held-Out Test Set):
- **Diabetes:** $\text{TN}=72, \quad \text{FP}=28, \quad \text{FN}=11, \quad \text{TP}=43$ (Total = 154)
- **Heart Disease:** $\text{TN}=28, \quad \text{FP}=4, \quad \text{FN}=6, \quad \text{TP}=22$ (Total = 60)
- **Chronic Kidney Disease:** $\text{TN}=30, \quad \text{FP}=0, \quad \text{FN}=2, \quad \text{TP}=48$ (Total = 80)

---

## 8. Calibration & Probability Assessment

1. **Probability Distribution:** Continuous positive-class probabilities $P(\text{target}=1)$ are generated natively via `predict_proba()`.
2. **Brier Scores:**
   - Diabetes: $0.1760$ (baseline well below non-informative $0.2500$)
   - Heart Disease: $0.1081$ (strong calibration on test set)
   - Chronic Kidney Disease: $0.0127$ (near-perfect probability separation)
3. **Calibration Policy:** Because the selected regularized champion models produce low Brier score losses without post-hoc scaling, explicit `CalibratedClassifierCV` fitting is deferred pending deployment evidence, avoiding unnecessary sample fragmentation on these small datasets.

---

## 9. External Artifact Storage & Checksums

Trained pipeline objects and metadata are stored strictly outside the Git repository in `MEDINTEL_DATA_DIR/ml_models/{condition}/`:

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

### Artifact SHA-256 Checksums:
- **Diabetes (`pipeline.joblib`):**  
  `ff72a814dc1ab3c6c88d108783577523960a692f4cb2fab5e2c24c2dbcde8a65`
- **Heart Disease (`pipeline.joblib`):**  
  `c904d3b8f8d65a68c3ef07ef42607923fc3d0f6339f8f3a7ab7a6f6ba830e274`
- **Chronic Kidney Disease (`pipeline.joblib`):**  
  `b8bfe429529194c709c92a676f321004e7c66d0dcdc43e85056b4a82db5401a4`

---

## 10. Reproducibility & Test Validation

1. **Training Execution Script:**
   ```bash
   python ml/scripts/train_models.py
   ```
2. **Unit & Regression Testing:**
   - Dedicated Phase 7 test suite: `tests/test_phase7_ml.py` (20 unit tests covering schema, loader, pipeline, CV, metrics, missing feature safety, and unknown categorical tolerance).
   - Full workspace test suite: **185 passed, 2 warnings in 9.28s**.

---

## 11. Known Limitations & Safety Disclaimers

1. **Academic Prototype Datasets:**
   - **Diabetes:** Pima Indians heritage females $\ge 21$ years old; limited diversity.
   - **Heart Disease:** Cleveland Clinic 1980s cohort; single medical center.
   - **Chronic Kidney Disease:** Single hospital cohort in Tamil Nadu, India; synthetic median/mode imputation on missing raw data.
2. **Missing Feature Policy:** The inference engine strictly checks for all required features. If any required feature is missing, it returns `status="INSUFFICIENT_FEATURES"` and `risk_probability=None`. Never guess or impute silently.
3. **Mandatory Non-Diagnostic Disclaimer:**
   > *"This estimated risk score is an educational indicator derived from historical research datasets. It is NOT a medical diagnosis, clinical prognosis, or treatment recommendation. Please consult a qualified healthcare professional for comprehensive medical evaluation."*
