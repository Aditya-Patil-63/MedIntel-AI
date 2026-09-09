# MedIntel AI — Dataset Setup Guide

> Phase 3: Data Collection & Preparation

---

## Important: Datasets Are NOT Stored in the Git Repository

The actual dataset files (CSV, ARFF, etc.) are intentionally **excluded from the GitHub repository** to:

1. **Respect licensing**: Ensure proper dataset usage according to their respective licenses.
2. **Keep the repository lightweight**: Datasets can be large and do not belong in version control.
3. **Prevent accidental data exposure**: No real or research patient data should be committed.
4. **Ensure reproducibility**: Each developer downloads directly from the official source.

The repository contains **only**:
- Dataset documentation and metadata
- Preprocessing scripts
- Inspection scripts
- Data quality reports

---

## Step 1: Create the External Data Directory

Create a directory **outside** the MedIntel AI repository to store datasets.

Example structure:

```
MEDINTEL_DATA_DIR/
├── raw/
│   ├── diabetes/
│   │   └── diabetes.csv
│   ├── heart_disease/
│   │   └── heart.csv
│   └── kidney_disease/
│       └── kidney_disease.csv
└── processed/
    ├── diabetes/
    ├── heart_disease/
    └── kidney_disease/
```

The path can be anywhere on your system, for example:
- Windows: `D:\MedIntel-Datasets\`
- macOS/Linux: `~/medintel-datasets/`

> **Do NOT place this inside `D:\MedIntel AI\` or any directory tracked by Git.**

---

## Step 2: Set the Environment Variable

All scripts use the `MEDINTEL_DATA_DIR` environment variable to locate datasets.

### Windows (PowerShell)

```powershell
$env:MEDINTEL_DATA_DIR = "D:\MedIntel-Datasets"
```

To set permanently:
```powershell
[System.Environment]::SetEnvironmentVariable("MEDINTEL_DATA_DIR", "D:\MedIntel-Datasets", "User")
```

### Windows (Command Prompt)

```cmd
set MEDINTEL_DATA_DIR=D:\MedIntel-Datasets
```

### macOS / Linux

```bash
export MEDINTEL_DATA_DIR=~/medintel-datasets
```

Add to `~/.bashrc` or `~/.zshrc` for persistence.

---

## Step 3: Download Each Dataset

### 3.1 Diabetes — Pima Indians Diabetes Database

**Primary Source**: https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database  
**Alternative Source**: OpenML Dataset ID 37 (https://www.openml.org/d/37)

1. Download `diabetes.csv` from the Kaggle page above (or export from OpenML).
2. Place it at: `MEDINTEL_DATA_DIR/raw/diabetes/diabetes.csv`

**Expected file**: `dataset_37_diabetes.arff` (OpenML) or `diabetes.csv` (Kaggle)
**Expected columns**: Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age, Outcome
**Expected rows**: 768

### 3.2 Heart Disease — UCI Cleveland Processed

**Source**: https://archive.ics.uci.edu/dataset/45/heart+disease
**Alternative**: https://www.kaggle.com/datasets/redwankarimsony/heart-disease-data

1. Download the Cleveland processed dataset (`processed.cleveland.data` or `heart.csv`).
2. Place it at: `MEDINTEL_DATA_DIR/raw/heart_disease/processed.cleveland.data` (or `heart.csv`)

**Expected file**: `processed.cleveland.data` (UCI) or `heart.csv`
**Expected columns**: age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, target
**Expected rows**: 303

> Note: The original UCI file `processed.cleveland.data` has no header row and uses `?` for missing values. The inspection and preparation scripts automatically detect and parse this format.

### 3.3 Kidney Disease — UCI Chronic Kidney Disease

**Source**: https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease
**Alternative**: https://www.kaggle.com/datasets/mansoordaku/ckdisease

1. Download `chronic_kidney_disease_full.arff` (or `kidney_disease.csv`).
2. Place it at: `MEDINTEL_DATA_DIR/raw/kidney_disease/chronic_kidney_disease_full.arff` (or `kidney_disease.csv`)

**Expected file**: `chronic_kidney_disease_full.arff` (UCI) or `kidney_disease.csv`
**Expected columns**: age, bp, sg, al, su, rbc, pc, pcc, ba, bgr, bu, sc, sod, pot, hemo, pcv, wc (or wbcc), rc (or rbcc), htn, dm, cad, appet, pe, ane, classification (or class)
**Expected rows**: 400

> Note: The inspection and preparation scripts support both the original UCI ARFF format and cleaned CSV format.

---

## Step 4: Verify Setup

Run the inspection scripts from the `ml/` directory:

```bash
cd ml
python scripts/inspect_diabetes.py
python scripts/inspect_heart_disease.py
python scripts/inspect_kidney_disease.py
```

Each script will:
- Check that `MEDINTEL_DATA_DIR` is set
- Check that the expected file exists
- Print dataset statistics
- Report any issues

If a dataset is missing, the script will print a clear error with download instructions.

---

## Step 5: Run Preparation Scripts

```bash
python scripts/prepare_diabetes.py
python scripts/prepare_heart_disease.py
python scripts/prepare_kidney_disease.py
```

Each preparation script will:
- Read from `MEDINTEL_DATA_DIR/raw/<dataset>/`
- Apply documented deterministic cleaning
- Save prepared output to `MEDINTEL_DATA_DIR/processed/<dataset>/`
- **Never** overwrite the original raw files

---

## How Scripts Locate Datasets

```python
import os

data_dir = os.environ.get("MEDINTEL_DATA_DIR")
if not data_dir:
    raise EnvironmentError(
        "MEDINTEL_DATA_DIR environment variable is not set. "
        "Please set it to your external dataset directory. "
        "See ml/data/DATASET_SETUP.md for instructions."
    )

raw_path = os.path.join(data_dir, "raw", "diabetes", "diabetes.csv")
processed_dir = os.path.join(data_dir, "processed", "diabetes")
```

No machine-specific paths are hardcoded in any script.

---

## Reproducing the Setup on Another Machine

1. Clone the MedIntel AI repository.
2. Create an external data directory anywhere on your system.
3. Set `MEDINTEL_DATA_DIR` to that directory.
4. Download each dataset from the documented sources.
5. Place files in the expected directory structure.
6. Run inspection scripts to verify.
7. Run preparation scripts to generate processed data.

---

## Why Raw Datasets Are Excluded from GitHub

1. **License compliance**: Datasets have their own licenses and redistribution terms.
2. **Repository size**: CSV and ARFF files would bloat the Git history.
3. **Privacy**: Even public medical datasets should be handled carefully.
4. **Reproducibility**: Downloading from the source ensures the latest/correct version.
5. **Academic integrity**: Proper attribution requires documenting the source, not bundling the data.
