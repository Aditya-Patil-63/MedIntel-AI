"""
MedIntel AI - Heart Disease Dataset Inspection Script.

Reads the UCI Heart Disease (Cleveland) dataset from the external
data directory (supporting processed.cleveland.data and heart.csv)
and prints a comprehensive inspection report.

Usage:
    python scripts/inspect_heart_disease.py

Requires:
    MEDINTEL_DATA_DIR environment variable set.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from data_config import get_raw_path, load_raw_dataset  # noqa: E402

DATASET_NAME = "heart_disease"
FILENAME = "heart.csv"
CANDIDATE_FILENAMES = ["processed.cleveland.data", "heart.csv"]

EXPECTED_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target",
]

UCI_HEADERLESS_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num",
]

CATEGORICAL_COLUMNS = ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"]


def inspect() -> None:
    """Run full inspection of the UCI Heart Disease (Cleveland) dataset."""
    print("=" * 60)
    print("UCI HEART DISEASE (CLEVELAND) - INSPECTION REPORT")
    print("=" * 60)

    csv_path = get_raw_path(DATASET_NAME, CANDIDATE_FILENAMES)
    print(f"\nSource file: {csv_path}\n")

    df = load_raw_dataset(csv_path, headerless_columns=UCI_HEADERLESS_COLUMNS)

    if "num" in df.columns and "target" not in df.columns:
        print("Note: Detected UCI 'num' target naming. Mapping to 'target'.\n")
        df = df.rename(columns={"num": "target"})

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
        print(f"  {col:15s} {df[col].dtype}")
    print()

    # --- Missing values ---
    print("Missing Values (NaN):")
    null_counts = df.isnull().sum()
    if null_counts.sum() == 0:
        print("  No NaN values found.")
    else:
        for col in df.columns:
            if null_counts[col] > 0:
                print(f"  {col:15s} {null_counts[col]:5d} ({null_counts[col]/len(df)*100:.1f}%)")
    print()

    # --- Check for '?' values (common in original UCI format) ---
    print("String '?' Values (original UCI missing-value marker):")
    q_found = False
    for col in df.columns:
        if df[col].dtype == object:
            q_count = (df[col].astype(str).str.strip() == "?").sum()
            if q_count > 0:
                print(f"  {col:15s} {q_count:5d}")
                q_found = True
    if not q_found:
        print("  None found.")
    print()

    # --- Duplicate rows ---
    dup_count = df.duplicated().sum()
    print(f"Duplicate Rows: {dup_count}\n")

    # --- Target distribution ---
    print("Target Distribution:")
    target_col = "target" if "target" in df.columns else "num"
    if target_col in df.columns:
        vc = df[target_col].value_counts().sort_index()
        for val, count in vc.items():
            pct = count / len(df) * 100
            print(f"  {val}: {count:5d} ({pct:.1f}%)")
    else:
        print("  WARNING: Target column not found.")
    print()

    # --- Categorical value distributions ---
    print("Categorical Value Distributions:")
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            print(f"\n  {col}:")
            for val, count in df[col].value_counts().sort_index().items():
                print(f"    {val}: {count}")
    print()

    # --- Numerical statistics ---
    print("Numerical Statistics:")
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        print(df[numeric_cols].describe().to_string())
    print()

    print("=" * 60)
    print("INSPECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    inspect()
