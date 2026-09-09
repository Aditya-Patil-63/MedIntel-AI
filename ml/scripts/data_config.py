"""
MedIntel AI - ML Scripts Data Configuration.

Provides a centralised way for all inspection and preparation scripts
to locate the external dataset directory via the MEDINTEL_DATA_DIR
environment variable, and utility functions to load datasets in CSV,
ARFF, and headerless data formats without external ARFF dependencies.
No machine-specific paths are hard-coded.
"""

import os
import sys
from pathlib import Path
from typing import Union, List, Optional

import pandas as pd


def get_data_dir() -> Path:
    """Return the root external data directory.

    Reads from the ``MEDINTEL_DATA_DIR`` environment variable.

    Returns:
        Path: Absolute path to the external data directory.

    Raises:
        SystemExit: If the environment variable is not set.
    """
    data_dir = os.environ.get("MEDINTEL_DATA_DIR")
    if not data_dir:
        print(
            "ERROR: MEDINTEL_DATA_DIR environment variable is not set.\n"
            "\n"
            "The actual dataset files are stored OUTSIDE the Git repository.\n"
            "Please set MEDINTEL_DATA_DIR to your external dataset directory.\n"
            "\n"
            "Example (Windows PowerShell):\n"
            '  $env:MEDINTEL_DATA_DIR = "D:\\MedIntel-Datasets"\n'
            "\n"
            "Example (macOS / Linux):\n"
            "  export MEDINTEL_DATA_DIR=~/medintel-datasets\n"
            "\n"
            "See ml/data/DATASET_SETUP.md for full instructions.",
            file=sys.stderr,
        )
        sys.exit(1)

    path = Path(data_dir)
    if not path.is_dir():
        print(
            f"ERROR: MEDINTEL_DATA_DIR points to a directory that does not exist:\n"
            f"  {path}\n"
            f"\n"
            f"Please create this directory and download the datasets into it.\n"
            f"See ml/data/DATASET_SETUP.md for full instructions.",
            file=sys.stderr,
        )
        sys.exit(1)

    return path


def get_raw_path(dataset_name: str, filename: Union[str, List[str]]) -> Path:
    """Return the path to a raw dataset file, supporting fallback candidates.

    Args:
        dataset_name: Subdirectory name (e.g. 'diabetes', 'heart_disease').
        filename: Expected filename or list of candidate filenames.

    Returns:
        Path: Absolute path to the existing raw dataset file.

    Raises:
        SystemExit: If no matching file exists, with helpful instructions.
    """
    raw_dir = get_data_dir() / "raw" / dataset_name
    candidates = [filename] if isinstance(filename, str) else filename

    for fname in candidates:
        candidate_path = raw_dir / fname
        if candidate_path.is_file():
            return candidate_path

    # If none found, show error and exit
    expected = ", ".join(candidates)
    print(
        f"ERROR: Dataset file not found in {raw_dir}.\n"
        f"  Looked for: {expected}\n"
        f"\n"
        f"Please download the dataset and place it at the path above.\n"
        f"See ml/data/DATASET_SETUP.md for download instructions.",
        file=sys.stderr,
    )
    sys.exit(1)


def get_processed_dir(dataset_name: str) -> Path:
    """Return (and create) the processed-output directory for a dataset.

    Args:
        dataset_name: Subdirectory name (e.g. 'diabetes').

    Returns:
        Path: Absolute path to the processed output directory.
    """
    processed_dir = get_data_dir() / "processed" / dataset_name
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir


def load_raw_dataset(file_path: Path, headerless_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Load a raw dataset file supporting CSV, ARFF, and headerless data formats.

    Args:
        file_path: Absolute path to the raw dataset file.
        headerless_columns: Column names to apply if the file is headerless.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".arff":
        # Pure-python ARFF parser without external dependencies
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        attributes = []
        data_start_idx = None
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str or line_str.startswith("%"):
                continue
            if line_str.lower().startswith("@attribute"):
                parts = line_str.split()
                attr_name = parts[1].strip("'\"")
                attributes.append(attr_name)
            elif line_str.lower().startswith("@data"):
                data_start_idx = idx + 1
                break

        if data_start_idx is None:
            raise ValueError(f"No @data section found in ARFF file: {file_path}")

        rows = []
        for line in lines[data_start_idx:]:
            line_clean = line.strip()
            if not line_clean or line_clean.startswith("%"):
                continue
            # Handle trailing comma if present (e.g., in UCI CKD dataset)
            if line_clean.endswith(","):
                line_clean = line_clean[:-1].strip()
            tokens = [t.strip().strip("'\"") for t in line_clean.split(",")]
            # Handle double comma accidental empty token (e.g., line 369 in UCI CKD)
            if len(tokens) == len(attributes) + 1 and "" in tokens:
                tokens = [t for t in tokens if t != ""]
            rows.append(tokens)

        df = pd.DataFrame(rows, columns=attributes)
        df = df.replace("?", None)
        return df

    elif suffix in (".data", ".txt") or (suffix == ".csv" and headerless_columns is not None):
        # Check if the file has headers or is headerless
        df_peek = pd.read_csv(file_path, nrows=5, na_values=["?"])
        # If columns look numeric/float, it is headerless
        if headerless_columns and df_peek.shape[1] == len(headerless_columns):
            is_headerless = False
            try:
                # If first column name is convertible to float, it is headerless data
                float(df_peek.columns[0])
                is_headerless = True
            except ValueError:
                is_headerless = False

            if is_headerless:
                return pd.read_csv(file_path, header=None, names=headerless_columns, na_values=["?"])

        return pd.read_csv(file_path, na_values=["?"])

    else:
        return pd.read_csv(file_path, na_values=["?"])
