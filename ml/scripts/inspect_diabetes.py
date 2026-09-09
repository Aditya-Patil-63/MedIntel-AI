"""
MedIntel AI - Diabetes Dataset Inspection Script.

Reads the Pima Indians Diabetes Database from the external data
directory (supporting both ARFF and CSV formats) and prints a
comprehensive inspection report.

Usage:
    python scripts/inspect_diabetes.py

Requires:
    MEDINTEL_DATA_DIR environment variable set.
"""

import sys
from pathlib import Path

# Add parent so data_config is importable when running from ml/
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from data_config import get_raw_path, load_raw_dataset  # noqa: E402

DATASET_NAME = "diabetes"
FILENAME = "diabetes.csv"
CANDIDATE_FILENAMES = ["dataset_37_diabetes.arff", "diabetes.csv"]

EXPECTED_COLUMNS = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age", "Outcome",
]

ARFF_COLUMN_MAP = {
    "preg": "Pregnancies",
    "plas": "Glucose",
    "pres": "BloodPressure",
    "skin": "SkinThickness",
    "insu": "Insulin",
    "mass": "BMI",
    "pedi": "DiabetesPedigreeFunction",
    "age": "Age",
    "class": "Outcome",
}

# Columns where zero is physiologically implausible
ZERO_SUSPICIOUS_COLUMNS = [
    "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI",
]


def inspect() -> None:
    """Run full inspection of the Pima Indians Diabetes dataset."""
    print("=" * 60)
    print("PIMA INDIANS DIABETES DATABASE - INSPECTION REPORT")
    print("=" * 60)

    csv_path = get_raw_path(DATASET_NAME, CANDIDATE_FILENAMES)
    print(f"\nSource file: {csv_path}\n")

    df = load_raw_dataset(csv_path)

    # If raw format uses ARFF abbreviations, normalize column names for inspection
    if "preg" in df.columns and "plas" in df.columns:
        print("Note: Detected ARFF feature naming. Mapping to standard clinical feature names.\n")
        df = df.rename(columns=ARFF_COLUMN_MAP)

    # Ensure numeric columns are parsed as numbers
    numeric_cols = [c for c in EXPECTED_COLUMNS if c != "Outcome" and c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Shape ---
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    # --- Columns ---
    print("Columns:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    print()

    # --- Column check ---
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    extra_cols = set(df.columns) - set(EXPECTED_COLUMNS)
    if missing_cols:
        print(f"WARNING: Missing expected columns: {missing_cols}")
    if extra_cols:
        print(f"NOTE: Extra columns found: {extra_cols}")
    if not missing_cols and not extra_cols:
        print("[OK] All expected columns present.\n")

    # --- Data types ---
    print("Data Types:")
    for col in df.columns:
        print(f"  {col:30s} {df[col].dtype}")
    print()

    # --- Missing values ---
    print("Missing Values (NaN):")
    null_counts = df.isnull().sum()
    if null_counts.sum() == 0:
        print("  No NaN values found.")
    else:
        for col in df.columns:
            if null_counts[col] > 0:
                print(f"  {col:30s} {null_counts[col]:5d} ({null_counts[col]/len(df)*100:.1f}%)")
    print()

    # --- Duplicate rows ---
    dup_count = df.duplicated().sum()
    print(f"Duplicate Rows: {dup_count}\n")

    # --- Target distribution ---
    print("Target Distribution (Outcome):")
    if "Outcome" in df.columns:
        vc = df["Outcome"].value_counts().sort_index()
        for val, count in vc.items():
            pct = count / len(df) * 100
            print(f"  {val}: {count:5d} ({pct:.1f}%)")
    else:
        print("  WARNING: 'Outcome' column not found.")
    print()

    # --- Numerical statistics ---
    print("Numerical Statistics:")
    print(df[numeric_cols].describe().to_string())
    print()

    # --- Suspicious zeros ---
    print("Suspicious Zero Values (physiologically implausible):")
    for col in ZERO_SUSPICIOUS_COLUMNS:
        if col in df.columns:
            zero_count = (df[col] == 0).sum()
            pct = zero_count / len(df) * 100
            print(f"  {col:30s} {zero_count:5d} zeros ({pct:.1f}%)")
    print()

    print("=" * 60)
    print("INSPECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    inspect()
