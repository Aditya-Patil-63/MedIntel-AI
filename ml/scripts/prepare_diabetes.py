"""
MedIntel AI - Diabetes Dataset Preparation Script.

Reads the raw Pima Indians Diabetes Database (supporting both ARFF
and CSV formats), applies documented deterministic cleaning, and saves
the prepared output to the external processed-data directory.

Cleaning rules:
    1. Support both ARFF format (dataset_37_diabetes.arff) and CSV.
    2. Normalize column names to standard clinical names.
    3. Normalize target encoding to binary: 0 = No diabetes, 1 = Diabetes.
    4. Replace physiologically implausible zero values with NaN
       in: Glucose, BloodPressure, SkinThickness, Insulin, BMI.
    5. Fill NaN values with the column median.
    6. Validate target encoding (0 and 1 only).
    7. Remove exact duplicate rows.
    8. Save prepared CSV to the processed directory.

The raw dataset is NEVER overwritten.

Usage:
    python scripts/prepare_diabetes.py

Requires:
    MEDINTEL_DATA_DIR environment variable set.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402
import numpy as np  # noqa: E402

from data_config import get_raw_path, get_processed_dir, load_raw_dataset  # noqa: E402

DATASET_NAME = "diabetes"
FILENAME = "diabetes.csv"
CANDIDATE_FILENAMES = ["dataset_37_diabetes.arff", "diabetes.csv"]
OUTPUT_FILENAME = "diabetes_prepared.csv"

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

NUMERIC_COLUMNS = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
]

# Columns where zero is physiologically implausible
ZERO_TO_NAN_COLUMNS = [
    "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI",
]

TARGET_COLUMN = "Outcome"
VALID_TARGET_VALUES = {0, 1}


def prepare() -> None:
    """Run deterministic preparation of the diabetes dataset."""
    print("=" * 60)
    print("DIABETES DATASET - PREPARATION")
    print("=" * 60)

    # --- Load raw data ---
    raw_path = get_raw_path(DATASET_NAME, CANDIDATE_FILENAMES)
    raw_mtime_before = raw_path.stat().st_mtime
    raw_size_before = raw_path.stat().st_size
    print(f"\nReading raw dataset: {raw_path}")

    df = load_raw_dataset(raw_path)
    print(f"Raw shape: {df.shape[0]} rows x {df.shape[1]} columns")

    # If raw format uses ARFF abbreviations, normalize column names
    if "preg" in df.columns and "plas" in df.columns:
        print("  Note: Detected ARFF feature naming. Mapping to standard clinical feature names.")
        df = df.rename(columns=ARFF_COLUMN_MAP)

    # --- Step 1: Validate columns ---
    print("\n[Step 1] Validating columns...")
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_cols:
        print(f"ERROR: Missing columns: {missing_cols}", file=sys.stderr)
        sys.exit(1)
    print("  [OK] All expected columns present.")

    # --- Step 2: Normalize data types and target ---
    print("\n[Step 2] Normalizing data types and target encoding...")
    # Normalize target (handle tested_positive/tested_negative strings or 0/1)
    target_str = df[TARGET_COLUMN].astype(str).str.strip().str.lower()
    df[TARGET_COLUMN] = target_str.replace({
        "tested_positive": 1,
        "tested_negative": 0,
        "1": 1,
        "0": 0,
    })
    df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce").astype(int)

    # Convert numeric feature columns
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Step 3: Replace implausible zeros with NaN ---
    print("\n[Step 3] Replacing implausible zero values with NaN...")
    for col in ZERO_TO_NAN_COLUMNS:
        zero_count = (df[col] == 0).sum()
        if zero_count > 0:
            df[col] = df[col].replace(0, np.nan)
            print(f"  {col}: {zero_count} zeros -> NaN")

    # --- Step 4: Fill NaN with median ---
    print("\n[Step 4] Filling NaN with column median...")
    for col in ZERO_TO_NAN_COLUMNS:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print(f"  {col}: {nan_count} NaN filled with median={median_val:.1f}")

    # --- Step 5: Validate target ---
    print("\n[Step 5] Validating target column...")
    if TARGET_COLUMN not in df.columns:
        print(f"ERROR: Target column '{TARGET_COLUMN}' not found.", file=sys.stderr)
        sys.exit(1)
    unique_targets = set(df[TARGET_COLUMN].unique())
    if not unique_targets.issubset(VALID_TARGET_VALUES):
        print(f"ERROR: Unexpected target values: {unique_targets}", file=sys.stderr)
        sys.exit(1)
    target_dist = df[TARGET_COLUMN].value_counts().sort_index()
    for val, count in target_dist.items():
        pct = count / len(df) * 100
        print(f"  {val}: {count} ({pct:.1f}%)")

    # --- Step 6: Remove duplicates ---
    print("\n[Step 6] Removing exact duplicates...")
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    print(f"  Removed {removed} duplicate rows.")

    # --- Step 7: Save prepared dataset ---
    print("\n[Step 7] Saving prepared dataset...")
    output_dir = get_processed_dir(DATASET_NAME)
    output_path = output_dir / OUTPUT_FILENAME
    # Reorder columns to expected order
    df = df[EXPECTED_COLUMNS]
    df.to_csv(output_path, index=False)
    print(f"  Saved to: {output_path}")
    print(f"  Final shape: {df.shape[0]} rows x {df.shape[1]} columns")

    # --- Step 8: Verify raw file was untouched ---
    print("\n[Verification] Raw file was untouched:")
    assert raw_path.stat().st_mtime == raw_mtime_before, "Raw file mtime changed!"
    assert raw_path.stat().st_size == raw_size_before, "Raw file size changed!"
    print(f"  Raw file size ({raw_size_before} bytes) and mtime verified unchanged.")

    print("\n" + "=" * 60)
    print("PREPARATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    prepare()
