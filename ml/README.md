# Machine Learning Module — MedIntel AI

ML models for medical risk prediction.

## Status

**Current Phase: Phase 3 — Data Collection & Preparation** ✅  
*(ML Model Development is NOT yet started — models are NOT trained in this phase)*

---

## Exact Datasets Selected for the Project

The following **exact three datasets** have been selected and verified for the three ML risk-prediction tasks:

1. **Diabetes Risk Prediction:**
   - **Dataset:** Pima Indians Diabetes Database
   - **Original Source:** National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)
   - **Accessible Sources:** Kaggle / OpenML (Dataset ID: 37)
   - **Target:** `Outcome` (0 = No diabetes, 1 = Diabetes)
   - **Records:** 768 rows, 8 clinical features + 1 target

2. **Heart Disease Risk Prediction:**
   - **Dataset:** UCI Heart Disease Dataset (Cleveland subset, processed)
   - **Source:** UCI Machine Learning Repository
   - **DOI:** `10.24432/C52P4X`
   - **Target:** `num` / `target` normalized to binary classification (0 = absence, 1 = presence)
   - **Records:** 303 rows, 13 clinical features + 1 target

3. **Kidney Disease Risk Prediction:**
   - **Dataset:** UCI Chronic Kidney Disease Dataset
   - **Source:** UCI Machine Learning Repository (Apollo Hospitals, Karaikudi, Tamil Nadu, India)
   - **DOI:** `10.24432/C5G020`
   - **Target:** `class` / `classification` (ckd → 1, notckd → 0)
   - **Records:** 400 rows, 24 clinical features + 1 target

> **Important:** These exact three datasets will be used for the subsequent ML Model Development phase.

---

## Important Data Storage Policy

> **Actual dataset files (CSV, ARFF, etc.) are strictly kept OUTSIDE the Git repository.**
>
> The project repository tracks only documentation, metadata, inspection scripts, and reproducible data preparation scripts.
>
> To configure the external data directory, set the `MEDINTEL_DATA_DIR` environment variable.
> See [data/DATASET_SETUP.md](data/DATASET_SETUP.md) for full setup instructions.

---

## Module Structure

```
ml/
├── data/
│   ├── metadata/
│   │   ├── diabetes/
│   │   │   └── dataset_metadata.md
│   │   ├── heart_disease/
│   │   │   └── dataset_metadata.md
│   │   └── kidney_disease/
│   │       └── dataset_metadata.md
│   ├── DATASET_SOURCES.md       # Comprehensive source, citation, and license info
│   ├── DATASET_SETUP.md         # External data storage and setup instructions
│   ├── DATA_QUALITY_REPORT.md   # Data quality, distributions, and cleaning rules
│   └── README.md
├── scripts/
│   ├── data_config.py           # Shared path resolver using MEDINTEL_DATA_DIR
│   ├── inspect_diabetes.py      # Inspection script for diabetes dataset
│   ├── inspect_heart_disease.py # Inspection script for heart disease dataset
│   ├── inspect_kidney_disease.py# Inspection script for kidney disease dataset
│   ├── prepare_diabetes.py      # Deterministic preparation script for diabetes
│   ├── prepare_heart_disease.py # Deterministic preparation script for heart disease
│   └── prepare_kidney_disease.py# Deterministic preparation script for kidney disease
├── notebooks/
│   └── README.md
└── README.md
```

---

## Running Inspection & Preparation Scripts

Ensure `MEDINTEL_DATA_DIR` is set to your external dataset directory:

```bash
# Set external data location (example)
$env:MEDINTEL_DATA_DIR = "D:\MedIntel-Datasets"  # Windows PowerShell
export MEDINTEL_DATA_DIR=~/medintel-datasets       # Linux / macOS

# Run Inspection Scripts
python ml/scripts/inspect_diabetes.py
python ml/scripts/inspect_heart_disease.py
python ml/scripts/inspect_kidney_disease.py

# Run Preparation Scripts
python ml/scripts/prepare_diabetes.py
python ml/scripts/prepare_heart_disease.py
python ml/scripts/prepare_kidney_disease.py
```

---

## Next Steps (Subsequent Phases)

- **Phase 4:** Handwriting Recognition / OCR
- **Phase 5:** Medical Reference Analysis
- **Phase 6:** ML Model Development (Model training on the prepared datasets using scikit-learn & XGBoost, with strict train/val/test splits to prevent data leakage)
