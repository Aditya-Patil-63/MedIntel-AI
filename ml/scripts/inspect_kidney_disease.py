"""
MedIntel AI - Chronic Kidney Disease Dataset Inspection Script.

Reads the UCI Chronic Kidney Disease dataset from the external data
directory (supporting chronic_kidney_disease_full.arff and kidney_disease.csv)
and prints a comprehensive inspection report.

Usage:
    python scripts/inspect_kidney_disease.py

Requires:
    MEDINTEL_DATA_DIR environment variable set.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from data_config import get_raw_path, load_raw_dataset  # noqa: E402

DATASET_NAME = "kidney_disease"
FILENAME = "kidney_disease.csv"
CANDIDATE_FILENAMES = ["chronic_kidney_disease_full.arff", "kidney_disease.csv"]

EXPECTED_FEATURE_COLUMNS = [
    "age", "bp", "sg", "al", "su", "rbc", "pc", "pcc", "ba",
    "bgr", "bu", "sc", "sod", "pot", "hemo", "pcv", "wc", "rc",
    "htn", "dm", "cad", "appet", "pe", "ane",
]

NUMERIC_COLUMNS = [
    "age", "bp", "sg", "al", "su", "bgr", "bu", "sc",
    "sod", "pot", "hemo", "pcv", "wc", "rc",
]

CATEGORICAL_COLUMNS = [
    "rbc", "pc", "pcc", "ba", "htn", "dm", "cad", "appet", "pe", "ane",
]

# Possible target column names across different versions
TARGET_CANDIDATES = ["classification", "class"]


def inspect() -> None:
    """Run full inspection of the UCI Chronic Kidney Disease dataset."""
    print("=" * 60)
    print("UCI CHRONIC KIDNEY DISEASE - INSPECTION REPORT")
    print("=" * 60)

    csv_path = get_raw_path(DATASET_NAME, CANDIDATE_FILENAMES)
    print(f"\nSource file: {csv_path}\n")

    df = load_raw_dataset(csv_path)

    # Normalize UCI ARFF naming variations if present (wbcc -> wc, rbcc -> rc)
    if "wbcc" in df.columns or "rbcc" in df.columns:
        print("Note: Normalizing ARFF feature abbreviations ('wbcc' -> 'wc', 'rbcc' -> 'rc').\n")
        df = df.rename(columns={"wbcc": "wc", "rbcc": "rc"})

    # --- Shape ---
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    # --- Columns ---
    print("Columns:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    print()

    # --- Identify target column ---
    target_col = None
    for candidate in TARGET_CANDIDATES:
        if candidate in df.columns:
            target_col = candidate
            break
    if target_col:
        print(f"Target column identified: '{target_col}'\n")
    else:
        print("WARNING: Target column not found. Checked: " + str(TARGET_CANDIDATES) + "\n")

    # --- Data types ---
    print("Data Types:")
    for col in df.columns:
        print(f"  {col:20s} {df[col].dtype}")
    print()

    # --- Missing values ---
    print("Missing Values:")
    null_counts = df.isnull().sum()
    q_counts = {}
    for col in df.columns:
        if df[col].dtype == object:
            q_count = (df[col].astype(str).str.strip() == "?").sum()
            if q_count > 0:
                q_counts[col] = q_count

    has_missing = False
    for col in df.columns:
        nan_c = null_counts[col]
        q_c = q_counts.get(col, 0)
        total_missing = nan_c + q_c
        if total_missing > 0:
            has_missing = True
            parts = []
            if nan_c > 0:
                parts.append(f"{nan_c} NaN")
            if q_c > 0:
                parts.append(f"{q_c} '?'")
            pct = total_missing / len(df) * 100
            print(f"  {col:20s} {total_missing:5d} ({pct:.1f}%) - {', '.join(parts)}")
    if not has_missing:
        print("  No missing values found.")
    print()

    # --- Duplicate rows ---
    dup_count = df.duplicated().sum()
    print(f"Duplicate Rows: {dup_count}\n")

    # --- Target distribution ---
    if target_col:
        print(f"Target Distribution ('{target_col}'):")
        target_vals = df[target_col].astype(str).str.strip().str.lower()
        vc = target_vals.value_counts()
        for val, count in vc.items():
            pct = count / len(df) * 100
            print(f"  '{val}': {count:5d} ({pct:.1f}%)")
    print()

    # --- Categorical value distributions ---
    print("Categorical Value Distributions:")
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            print(f"\n  {col}:")
            vals = df[col].astype(str).str.strip().value_counts()
            for val, count in vals.items():
                print(f"    '{val}': {count}")
    print()

    # --- Numerical statistics ---
    print("Numerical Statistics:")
    numeric_present = [c for c in NUMERIC_COLUMNS if c in df.columns]
    if numeric_present:
        numeric_df = df[numeric_present].apply(pd.to_numeric, errors="coerce")
        print(numeric_df.describe().to_string())
    print()

    print("=" * 60)
    print("INSPECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    inspect()
