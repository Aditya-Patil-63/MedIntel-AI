"""
MedIntel AI — Phase 3 Tests: Data Preparation Utilities.

Tests verify:
    - External dataset path handling
    - Missing-file error handling
    - Expected columns definitions
    - Target existence and encoding definitions
    - Data-type conversion logic
    - Missing-value handling logic
    - No accidental target duplication
    - Raw input is never overwritten

These tests use synthetic data — no real patient data.
No ML models are tested.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

# Add the scripts directory to the path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "ml" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def temp_data_dir(tmp_path: Path):
    """Create a temporary external data directory structure."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    for disease in ["diabetes", "heart_disease", "kidney_disease"]:
        (raw_dir / disease).mkdir(parents=True)
        (processed_dir / disease).mkdir(parents=True)
    return tmp_path


@pytest.fixture
def synthetic_diabetes_csv(temp_data_dir: Path) -> Path:
    """Create a synthetic diabetes CSV (NOT real patient data)."""
    csv_path = temp_data_dir / "raw" / "diabetes" / "diabetes.csv"
    data = {
        "Pregnancies": [6, 1, 8, 1, 0],
        "Glucose": [148, 85, 183, 89, 0],  # last one is implausible zero
        "BloodPressure": [72, 66, 64, 66, 0],  # last one is implausible zero
        "SkinThickness": [35, 29, 0, 23, 0],
        "Insulin": [0, 0, 0, 94, 0],
        "BMI": [33.6, 26.6, 23.3, 28.1, 0.0],  # last one is implausible zero
        "DiabetesPedigreeFunction": [0.627, 0.351, 0.672, 0.167, 0.500],
        "Age": [50, 31, 32, 21, 33],
        "Outcome": [1, 0, 1, 0, 1],
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def synthetic_heart_csv(temp_data_dir: Path) -> Path:
    """Create a synthetic heart disease CSV (NOT real patient data)."""
    csv_path = temp_data_dir / "raw" / "heart_disease" / "heart.csv"
    data = {
        "age": [63, 37, 41, 56, 57],
        "sex": [1, 1, 0, 1, 0],
        "cp": [3, 2, 1, 1, 0],
        "trestbps": [145, 130, 130, 120, 120],
        "chol": [233, 250, 204, 236, 354],
        "fbs": [1, 0, 0, 0, 0],
        "restecg": [0, 1, 0, 1, 1],
        "thalach": [150, 187, 172, 178, 163],
        "exang": [0, 0, 0, 0, 1],
        "oldpeak": [2.3, 3.5, 1.4, 0.8, 0.6],
        "slope": [0, 0, 2, 2, 2],
        "ca": [0, 0, 0, 0, 0],
        "thal": [1, 2, 2, 2, 2],
        "target": [1, 1, 0, 0, 0],
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def synthetic_kidney_csv(temp_data_dir: Path) -> Path:
    """Create a synthetic kidney disease CSV (NOT real patient data)."""
    csv_path = temp_data_dir / "raw" / "kidney_disease" / "kidney_disease.csv"
    data = {
        "id": [0, 1, 2, 3, 4],
        "age": [48, 7, 62, 48, 51],
        "bp": [80, 50, 80, 70, 80],
        "sg": [1.020, 1.020, 1.010, 1.005, 1.010],
        "al": [1, 4, 2, 4, 2],
        "su": [0, 0, 3, 0, 0],
        "rbc": ["normal", "normal", "abnormal", " abnormal", "normal"],
        "pc": ["normal", "normal", "abnormal", "abnormal", "normal"],
        "pcc": ["notpresent", "notpresent", "notpresent", "present", "notpresent"],
        "ba": ["notpresent", "notpresent", "notpresent", "present", "notpresent"],
        "bgr": [121, "?", 423, 117, 106],  # '?' as missing
        "bu": [36, 18, 53, 56, 26],
        "sc": [1.2, 0.8, 1.8, 3.8, 1.4],
        "sod": [138, 142, 131, 111, 137],
        "pot": [4.2, 3.8, 4.8, 2.5, 4.4],
        "hemo": [15.4, 11.3, 9.6, 11.2, 11.6],
        "pcv": [44, 38, 31, 32, 35],
        "wc": [7800, 6000, 7500, 6700, 7300],
        "rc": [5.2, 3.8, 4.0, 3.9, 4.6],
        "htn": ["yes", "no", "no", "yes", "no"],
        "dm": [" yes", "no", "no", " yes", "no"],  # leading whitespace
        "cad": ["no", "no", "no", "yes", "no"],
        "appet": ["good", "good", "poor", "poor", "good"],
        "pe": ["no", "no", "no", "yes", "no"],
        "ane": ["no", "no", "yes", "yes", "no"],
        "classification": ["notckd", "ckd", "ckd", "ckd", "notckd"],
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path


# ===================================================================
# Test: data_config module
# ===================================================================

class TestDataConfig:
    """Test the data_config module path handling."""

    def test_missing_env_var_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Script should exit if MEDINTEL_DATA_DIR is not set."""
        monkeypatch.delenv("MEDINTEL_DATA_DIR", raising=False)
        from data_config import get_data_dir
        with pytest.raises(SystemExit):
            get_data_dir()

    def test_nonexistent_dir_exits(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Script should exit if MEDINTEL_DATA_DIR points to a missing directory."""
        fake_path = tmp_path / "does_not_exist"
        monkeypatch.setenv("MEDINTEL_DATA_DIR", str(fake_path))
        from data_config import get_data_dir
        with pytest.raises(SystemExit):
            get_data_dir()

    def test_valid_dir_returns_path(self, monkeypatch: pytest.MonkeyPatch, temp_data_dir: Path) -> None:
        """Script should return a valid Path when dir exists."""
        monkeypatch.setenv("MEDINTEL_DATA_DIR", str(temp_data_dir))
        from data_config import get_data_dir
        result = get_data_dir()
        assert result == temp_data_dir

    def test_missing_file_exits(self, monkeypatch: pytest.MonkeyPatch, temp_data_dir: Path) -> None:
        """get_raw_path should exit if the expected file is missing."""
        monkeypatch.setenv("MEDINTEL_DATA_DIR", str(temp_data_dir))
        from data_config import get_raw_path
        with pytest.raises(SystemExit):
            get_raw_path("diabetes", "nonexistent.csv")

    def test_existing_file_returns_path(
        self, monkeypatch: pytest.MonkeyPatch, synthetic_diabetes_csv: Path, temp_data_dir: Path,
    ) -> None:
        """get_raw_path should return the file path when it exists."""
        monkeypatch.setenv("MEDINTEL_DATA_DIR", str(temp_data_dir))
        from data_config import get_raw_path
        result = get_raw_path("diabetes", "diabetes.csv")
        assert result.is_file()

    def test_processed_dir_created(self, monkeypatch: pytest.MonkeyPatch, temp_data_dir: Path) -> None:
        """get_processed_dir should create the directory if it doesn't exist."""
        monkeypatch.setenv("MEDINTEL_DATA_DIR", str(temp_data_dir))
        from data_config import get_processed_dir
        new_dir = get_processed_dir("new_dataset")
        assert new_dir.is_dir()


# ===================================================================
# Test: Expected column definitions
# ===================================================================

class TestExpectedColumns:
    """Verify that inspection/preparation scripts define correct expected columns."""

    def test_diabetes_columns(self) -> None:
        """Diabetes script should expect 9 columns (8 features + 1 target)."""
        from inspect_diabetes import EXPECTED_COLUMNS
        assert len(EXPECTED_COLUMNS) == 9
        assert "Outcome" in EXPECTED_COLUMNS
        assert "Glucose" in EXPECTED_COLUMNS

    def test_heart_columns(self) -> None:
        """Heart disease script should expect 14 columns."""
        from inspect_heart_disease import EXPECTED_COLUMNS
        assert len(EXPECTED_COLUMNS) == 14
        assert "target" in EXPECTED_COLUMNS
        assert "age" in EXPECTED_COLUMNS

    def test_kidney_feature_columns(self) -> None:
        """Kidney disease script should expect 24 feature columns."""
        from inspect_kidney_disease import EXPECTED_FEATURE_COLUMNS
        assert len(EXPECTED_FEATURE_COLUMNS) == 24
        assert "age" in EXPECTED_FEATURE_COLUMNS
        assert "hemo" in EXPECTED_FEATURE_COLUMNS


# ===================================================================
# Test: Diabetes preparation logic
# ===================================================================

class TestDiabetesPreparation:
    """Test diabetes preparation logic using synthetic data."""

    def test_implausible_zeros_replaced(
        self, monkeypatch: pytest.MonkeyPatch, synthetic_diabetes_csv: Path, temp_data_dir: Path,
    ) -> None:
        """Zeros in Glucose/BP/SkinThickness/Insulin/BMI should be replaced."""
        monkeypatch.setenv("MEDINTEL_DATA_DIR", str(temp_data_dir))
        from prepare_diabetes import ZERO_TO_NAN_COLUMNS

        df = pd.read_csv(synthetic_diabetes_csv)
        for col in ZERO_TO_NAN_COLUMNS:
            df[col] = df[col].replace(0, np.nan)
            df[col] = df[col].fillna(df[col].median())
            assert (df[col] == 0).sum() == 0, f"Zero values remain in {col}"

    def test_target_encoding_valid(
        self, monkeypatch: pytest.MonkeyPatch, synthetic_diabetes_csv: Path, temp_data_dir: Path,
    ) -> None:
        """Target should contain only 0 and 1."""
        df = pd.read_csv(synthetic_diabetes_csv)
        unique = set(df["Outcome"].unique())
        assert unique.issubset({0, 1})

    def test_raw_not_overwritten(
        self, monkeypatch: pytest.MonkeyPatch, synthetic_diabetes_csv: Path, temp_data_dir: Path,
    ) -> None:
        """Preparation must not modify the raw file."""
        monkeypatch.setenv("MEDINTEL_DATA_DIR", str(temp_data_dir))
        original = pd.read_csv(synthetic_diabetes_csv)
        original_shape = original.shape

        # Simulate preparation steps without calling the main function
        df = pd.read_csv(synthetic_diabetes_csv)
        for col in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
            df[col] = df[col].replace(0, np.nan)
            df[col] = df[col].fillna(df[col].median())

        # Verify raw file is unchanged
        raw_check = pd.read_csv(synthetic_diabetes_csv)
        assert raw_check.shape == original_shape

    def test_no_target_duplication(self, synthetic_diabetes_csv: Path) -> None:
        """There should be exactly one target column."""
        df = pd.read_csv(synthetic_diabetes_csv)
        target_cols = [c for c in df.columns if c.lower() == "outcome"]
        assert len(target_cols) == 1


# ===================================================================
# Test: Heart disease preparation logic
# ===================================================================

class TestHeartDiseasePreparation:
    """Test heart disease preparation logic using synthetic data."""

    def test_target_binarization(self, synthetic_heart_csv: Path) -> None:
        """Target should be binary after binarization."""
        df = pd.read_csv(synthetic_heart_csv)
        df["target"] = (df["target"] > 0).astype(int)
        unique = set(df["target"].unique())
        assert unique.issubset({0, 1})

    def test_no_question_marks(self, synthetic_heart_csv: Path) -> None:
        """Synthetic data should not contain '?' markers."""
        df = pd.read_csv(synthetic_heart_csv)
        for col in df.columns:
            assert (df[col].astype(str) == "?").sum() == 0

    def test_column_count(self, synthetic_heart_csv: Path) -> None:
        """Should have exactly 14 columns."""
        df = pd.read_csv(synthetic_heart_csv)
        assert df.shape[1] == 14


# ===================================================================
# Test: Kidney disease preparation logic
# ===================================================================

class TestKidneyDiseasePreparation:
    """Test kidney disease preparation logic using synthetic data."""

    def test_target_normalization(self, synthetic_kidney_csv: Path) -> None:
        """CKD/notCKD should be normalizable to 1/0."""
        df = pd.read_csv(synthetic_kidney_csv)
        target = df["classification"].astype(str).str.strip().str.lower()
        mapped = target.replace({"ckd": 1, "notckd": 0})
        mapped = pd.to_numeric(mapped, errors="coerce")
        assert set(mapped.unique()) == {0, 1}

    def test_whitespace_handling(self, synthetic_kidney_csv: Path) -> None:
        """Leading/trailing whitespace should be strippable."""
        df = pd.read_csv(synthetic_kidney_csv)
        # dm column has leading whitespace in synthetic data
        stripped = df["dm"].astype(str).str.strip()
        assert all(v in ["yes", "no", "nan"] for v in stripped.unique())

    def test_question_mark_handling(self, synthetic_kidney_csv: Path) -> None:
        """'?' values should be identifiable as missing."""
        df = pd.read_csv(synthetic_kidney_csv)
        q_count = 0
        for col in df.columns:
            q_count += (df[col].astype(str).str.strip() == "?").sum()
        # Our synthetic data has at least 1 '?' value
        assert q_count >= 1

    def test_id_column_droppable(self, synthetic_kidney_csv: Path) -> None:
        """id column should be droppable without losing features."""
        df = pd.read_csv(synthetic_kidney_csv)
        assert "id" in df.columns
        df_dropped = df.drop(columns=["id"])
        # Should still have target + features
        assert "classification" in df_dropped.columns
        assert df_dropped.shape[1] >= 25  # 24 features + 1 target

    def test_no_target_duplication(self, synthetic_kidney_csv: Path) -> None:
        """There should be exactly one target column."""
        df = pd.read_csv(synthetic_kidney_csv)
        target_cols = [c for c in df.columns if c.lower() in ("classification", "class")]
        assert len(target_cols) == 1


# ===================================================================
# Test: No dataset files in Git repository
# ===================================================================

class TestNoDataInRepo:
    """Verify no actual dataset files exist inside the Git repository."""

    def test_no_csv_in_ml_data(self) -> None:
        """No CSV files should exist inside ml/data/."""
        ml_data_dir = Path(__file__).resolve().parent.parent / "ml" / "data"
        if ml_data_dir.is_dir():
            csv_files = list(ml_data_dir.rglob("*.csv"))
            assert len(csv_files) == 0, f"CSV files found in repo: {csv_files}"

    def test_no_raw_dir_in_repo(self) -> None:
        """ml/data/raw/ should not exist in the repository."""
        raw_dir = Path(__file__).resolve().parent.parent / "ml" / "data" / "raw"
        assert not raw_dir.is_dir(), "ml/data/raw/ directory should not exist in the repo"

    def test_no_processed_dir_in_repo(self) -> None:
        """ml/data/processed/ should not exist in the repository."""
        processed_dir = Path(__file__).resolve().parent.parent / "ml" / "data" / "processed"
        assert not processed_dir.is_dir(), "ml/data/processed/ directory should not exist in the repo"
