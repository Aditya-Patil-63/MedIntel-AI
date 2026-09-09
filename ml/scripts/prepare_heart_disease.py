"""
MedIntel AI - Heart Disease Dataset Preparation Script.

Reads the raw UCI Heart Disease (Cleveland) dataset (supporting both
processed.cleveland.data and heart.csv), applies documented deterministic
cleaning, and saves the prepared output to the external processed-data
directory.

Cleaning rules:
    1. Support both headerless UCI data and headered CSV formats.
    2. Handle missing values ('?' -> NaN -> drop affected rows).
    3. Normalize target to binary: 0 = absence, 1 = presence (original 1-4 -> 1).
    4. Convert numeric columns to proper types.
    5. Remove exact duplicate rows.
    6. Save prepared CSV to the processed directory.

The raw dataset is NEVER overwritten.

Usage:
    python scripts/prepare_heart_disease.py

Requires:
    MEDINTEL_DATA_DIR environment variable set.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402
import numpy as np  # noqa: E402

from data_config import get_raw_path, get_processed_dir, load_raw_dataset  # noqa: E402

DATASET_NAME = "heart_disease"
FILENAME = "heart.csv"
CANDIDATE_FILENAMES = ["processed.cleveland.data", "heart.csv"]
OUTPUT_FILENAME = "heart_disease_prepared.csv"

EXPECTED_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target",
]

UCI_HEADERLESS_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num",
]

NUMERIC_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal",
]

TARGET_COLUMN = "target"


def prepare() -> None:
    """Run deterministic preparation of the heart disease dataset."""
    print("=" * 60)
    print("UCI HEART DISEASE (CLEVELAND) - PREPARATION")
    print("=" * 60)

    raw_path = get_raw_path(DATASET_NAME, CANDIDATE_FILENAMES)
    raw_mtime_before = raw_path.stat().st_mtime
    raw_size_before = raw_path.stat().st_size
    print(f"\nReading raw dataset: {raw_path}")

    df = load_raw_dataset(raw_path, headerless_columns=UCI_HEADERLESS_COLUMNS)

    # Handle original UCI format ('num' as target)
    if "num" in df.columns and TARGET_COLUMN not in df.columns:
        df = df.rename(columns={"num": TARGET_COLUMN})
        print("  Renamed 'num' column to 'target'.")

    print(f"Raw shape: {df.shape[0]} rows x {df.shape[1]} columns")

    # --- Step 1: Validate columns ---
    print("\n[Step 1] Validating columns...")
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_cols:
        print(f"WARNING: Missing columns: {missing_cols}")
    else:
        print("  [OK] All expected columns present.")

    # --- Step 2: Handle missing values ---
    print("\n[Step 2] Handling missing values...")
    # Replace '?' with NaN if string
    df = df.replace("?", np.nan)
    null_counts = df.isnull().sum()
    total_null = null_counts.sum()
    if total_null > 0:
        for col in df.columns:
            if null_counts[col] > 0:
                print(f"  {col}: {null_counts[col]} missing values")
        before = len(df)
        df = df.dropna()
        print(f"  Dropped {before - len(df)} rows with missing values.")
    else:
        print("  No missing values found.")

    # --- Step 3: Normalize target to binary ---
    print("\n[Step 3] Normalizing target to binary (0 = absence, 1 = presence)...")
    original_dist = df[TARGET_COLUMN].value_counts().sort_index()
    print("  Original distribution:")
    for val, count in original_dist.items():
        print(f"    {val}: {count}")

    # Map: 0 stays 0, anything 1-4 becomes 1
    df[TARGET_COLUMN] = (pd.to_numeric(df[TARGET_COLUMN]) > 0).astype(int)

    binary_dist = df[TARGET_COLUMN].value_counts().sort_index()
    print("  Binary distribution:")
    for val, count in binary_dist.items():
        pct = count / len(df) * 100
        print(f"    {val}: {count} ({pct:.1f}%)")

    # --- Step 4: Convert numeric types ---
    print("\n[Step 4] Converting numeric types...")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Drop any rows that became NaN from type conversion
    conversion_nulls = df[NUMERIC_COLUMNS].isnull().sum().sum()
    if conversion_nulls > 0:
        before = len(df)
        df = df.dropna(subset=NUMERIC_COLUMNS)
        print(f"  Dropped {before - len(df)} rows from type conversion errors.")
    else:
        print("  [OK] All numeric conversions successful.")

    # --- Step 5: Remove duplicates ---
    print("\n[Step 5] Removing exact duplicates...")
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    print(f"  Removed {removed} duplicate rows.")

    # --- Step 6: Save prepared dataset ---
    print("\n[Step 6] Saving prepared dataset...")
    output_dir = get_processed_dir(DATASET_NAME)
    output_path = output_dir / OUTPUT_FILENAME
    # Reorder columns to expected order
    df = df[EXPECTED_COLUMNS]
    df.to_csv(output_path, index=False)
    print(f"  Saved to: {output_path}")
    print(f"  Final shape: {df.shape[0]} rows x {df.shape[1]} columns")

    # --- Step 7: Verify raw file was untouched ---
    print("\n[Verification] Raw file was untouched:")
    assert raw_path.stat().st_mtime == raw_mtime_before, "Raw file mtime changed!"
    assert raw_path.stat().st_size == raw_size_before, "Raw file size changed!"
    print(f"  Raw file size ({raw_size_before} bytes) and mtime verified unchanged.")

    print("\n" + "=" * 60)
    print("PREPARATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    prepare()
