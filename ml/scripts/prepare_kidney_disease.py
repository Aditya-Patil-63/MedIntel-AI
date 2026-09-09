"""
MedIntel AI - Chronic Kidney Disease Dataset Preparation Script.

Reads the raw UCI Chronic Kidney Disease dataset (supporting both
chronic_kidney_disease_full.arff and kidney_disease.csv), applies documented
deterministic cleaning, and saves the prepared output to the external
processed-data directory.

Cleaning rules:
    1. Support both ARFF and CSV formats.
    2. Normalize feature names ('wbcc' -> 'wc', 'rbcc' -> 'rc').
    3. Strip whitespace from all string values.
    4. Normalize target: 'ckd' -> 1, 'notckd' -> 0 (renamed to 'classification').
    5. Normalize categorical values (yes/no, present/notpresent, good/poor).
    6. Convert numeric columns to proper types.
    7. Fill numeric NaN with column median.
    8. Fill categorical NaN with column mode.
    9. Drop 'id' column if present.
    10. Remove exact duplicate rows.
    11. Save prepared CSV to the processed directory.

The raw dataset is NEVER overwritten.

Usage:
    python scripts/prepare_kidney_disease.py

Requires:
    MEDINTEL_DATA_DIR environment variable set.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402
import numpy as np  # noqa: E402

from data_config import get_raw_path, get_processed_dir, load_raw_dataset  # noqa: E402

DATASET_NAME = "kidney_disease"
FILENAME = "kidney_disease.csv"
CANDIDATE_FILENAMES = ["chronic_kidney_disease_full.arff", "kidney_disease.csv"]
OUTPUT_FILENAME = "kidney_disease_prepared.csv"

EXPECTED_FEATURE_COLUMNS = [
    "age", "bp", "sg", "al", "su", "rbc", "pc", "pcc", "ba",
    "bgr", "bu", "sc", "sod", "pot", "hemo", "pcv", "wc", "rc",
    "htn", "dm", "cad", "appet", "pe", "ane",
]

TARGET_CANDIDATES = ["classification", "class"]
TARGET_OUTPUT_COLUMN = "classification"

NUMERIC_COLUMNS = [
    "age", "bp", "sg", "al", "su", "bgr", "bu", "sc",
    "sod", "pot", "hemo", "pcv", "wc", "rc",
]

BINARY_CATEGORICAL_COLUMNS = {
    "rbc": {"normal": "normal", "abnormal": "abnormal"},
    "pc": {"normal": "normal", "abnormal": "abnormal"},
    "pcc": {"present": "present", "notpresent": "notpresent"},
    "ba": {"present": "present", "notpresent": "notpresent"},
    "htn": {"yes": "yes", "no": "no"},
    "dm": {"yes": "yes", "no": "no"},
    "cad": {"yes": "yes", "no": "no"},
    "appet": {"good": "good", "poor": "poor"},
    "pe": {"yes": "yes", "no": "no"},
    "ane": {"yes": "yes", "no": "no"},
}


def prepare() -> None:
    """Run deterministic preparation of the kidney disease dataset."""
    print("=" * 60)
    print("UCI CHRONIC KIDNEY DISEASE - PREPARATION")
    print("=" * 60)

    raw_path = get_raw_path(DATASET_NAME, CANDIDATE_FILENAMES)
    raw_mtime_before = raw_path.stat().st_mtime
    raw_size_before = raw_path.stat().st_size
    print(f"\nReading raw dataset: {raw_path}")

    df = load_raw_dataset(raw_path)
    print(f"Raw shape: {df.shape[0]} rows x {df.shape[1]} columns")

    # Normalize UCI ARFF naming variations if present
    if "wbcc" in df.columns or "rbcc" in df.columns:
        print("  Note: Normalizing ARFF feature abbreviations ('wbcc' -> 'wc', 'rbcc' -> 'rc').")
        df = df.rename(columns={"wbcc": "wc", "rbcc": "rc"})

    # --- Step 1: Identify target column ---
    print("\n[Step 1] Identifying target column...")
    target_col = None
    for candidate in TARGET_CANDIDATES:
        if candidate in df.columns:
            target_col = candidate
            break
    if not target_col:
        print(f"ERROR: Target column not found. Checked: {TARGET_CANDIDATES}", file=sys.stderr)
        sys.exit(1)
    print(f"  Found target column: '{target_col}'")

    # --- Step 2: Strip whitespace from all string columns ---
    print("\n[Step 2] Stripping whitespace from all string values...")
    str_cols = df.select_dtypes(include=["object", "string", "str"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan, "?": np.nan})
    print(f"  Processed {len(str_cols)} string columns.")

    # --- Step 3: Normalize target ---
    print("\n[Step 3] Normalizing target column...")
    df[target_col] = df[target_col].astype(str).str.strip().str.lower()
    df[target_col] = df[target_col].replace({
        "ckd": 1,
        "notckd": 0,
        "ckd\t": 1,
        "notckd\t": 0,
        "1": 1,
        "0": 0,
    })
    df[target_col] = pd.to_numeric(df[target_col], errors="coerce")

    if target_col != TARGET_OUTPUT_COLUMN:
        df = df.rename(columns={target_col: TARGET_OUTPUT_COLUMN})
        target_col = TARGET_OUTPUT_COLUMN

    target_dist = df[target_col].value_counts().sort_index()
    for val, count in target_dist.items():
        pct = count / len(df) * 100
        label = "CKD" if val == 1 else "Not CKD"
        print(f"  {int(val)} ({label}): {count} ({pct:.1f}%)")

    # --- Step 4: Normalize categorical values ---
    print("\n[Step 4] Normalizing categorical values...")
    for col, valid_map in BINARY_CATEGORICAL_COLUMNS.items():
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
            df[col] = df[col].replace({"nan": np.nan, "none": np.nan, "?": np.nan})
            normalized = df[col].map(lambda x: valid_map.get(x, np.nan) if pd.notna(x) else np.nan)
            changed = (df[col] != normalized).sum()
            df[col] = normalized
            if changed > 0:
                print(f"  {col}: Normalized {changed} values.")

    # --- Step 5: Convert numeric columns ---
    print("\n[Step 5] Converting numeric columns...")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Step 6: Fill numeric NaN with median ---
    print("\n[Step 6] Filling numeric NaN with column median...")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                print(f"  {col}: {nan_count} NaN filled with median={median_val:.2f}")

    # --- Step 7: Fill categorical NaN with mode ---
    print("\n[Step 7] Filling categorical NaN with column mode...")
    for col in BINARY_CATEGORICAL_COLUMNS:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val.iloc[0])
                    print(f"  {col}: {nan_count} NaN filled with mode='{mode_val.iloc[0]}'")

    # --- Step 8: Drop 'id' column if present ---
    print("\n[Step 8] Dropping non-feature columns...")
    if "id" in df.columns:
        df = df.drop(columns=["id"])
        print("  Dropped 'id' column.")
    else:
        print("  No 'id' column found.")

    # --- Step 9: Remove duplicates ---
    print("\n[Step 9] Removing exact duplicates...")
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    print(f"  Removed {removed} duplicate rows.")

    # --- Step 10: Save prepared dataset ---
    print("\n[Step 10] Saving prepared dataset...")
    output_dir = get_processed_dir(DATASET_NAME)
    output_path = output_dir / OUTPUT_FILENAME
    # Reorder columns: 24 features + classification
    final_columns = EXPECTED_FEATURE_COLUMNS + [TARGET_OUTPUT_COLUMN]
    df = df[final_columns]
    df.to_csv(output_path, index=False)
    print(f"  Saved to: {output_path}")
    print(f"  Final shape: {df.shape[0]} rows x {df.shape[1]} columns")

    # --- Step 11: Verify raw file was untouched ---
    print("\n[Verification] Raw file was untouched:")
    assert raw_path.stat().st_mtime == raw_mtime_before, "Raw file mtime changed!"
    assert raw_path.stat().st_size == raw_size_before, "Raw file size changed!"
    print(f"  Raw file size ({raw_size_before} bytes) and mtime verified unchanged.")

    print("\n" + "=" * 60)
    print("PREPARATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    prepare()
