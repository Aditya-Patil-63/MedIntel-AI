"""
MedIntel AI — Phase 5 Tests: Handwriting Recognition.

Tests verify:
    - Configuration validation (RTX 3050 4GB VRAM memory-safe parameters)
    - Aspect-ratio preserving transforms (raw, preprocessed, and model dimensions)
    - Manifest loading, split filtering, and label loading
    - Missing-file detection and error reporting
    - Dataset-specific split integrity and chinmays18 exclusion
    - Metric calculation (CER, WER, Exact Match on decoded text predictions)
    - Dataset-specific evaluation grouping (RxHandBD, Doctor BD, Combined)
    - Test-set isolation protection (rejection of test splits in training)
    - TrOCREngineAdapter adherence to BaseOCREngine interface
    - Model-derived confidence labeling and safety disclaimers

These tests use synthetic test images and mock predictions.
Zero GPU required. Zero model weight downloads.
"""

import io
import os
import sys
import tempfile
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from PIL import Image

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from handwriting.adapter import TrOCREngineAdapter
from handwriting.config import (
    EvaluationConfig,
    HandwritingPipelineConfig,
    ModelConfig,
    PreprocessingConfig,
    TrainingConfig,
    get_phase5_derived_dir,
)
from handwriting.data.dataset import (
    HandwritingDataset,
    HandwritingManifestLoader,
    ManifestRecord,
)
from handwriting.data.transforms import AspectRatioPreservingResize
from handwriting.evaluation.evaluate import HandwritingEvaluator
from handwriting.evaluation.metrics import (
    character_error_rate,
    compute_handwriting_metrics,
    exact_match_accuracy,
    levenshtein_distance,
    word_error_rate,
)
from handwriting.inference.predictor import HandwritingPrediction, TrOCRPredictor
from handwriting.models.trocr_module import TrOCRModule
from handwriting.training.trainer import TrOCRTrainer
from ocr.ocr_engine import BaseOCREngine, OCREngineUnavailableError


# ===================================================================
# Fixtures & Helpers
# ===================================================================

@pytest.fixture
def synthetic_narrow_crop() -> Image.Image:
    """Create a synthetic narrow word crop (300 width x 50 height)."""
    return Image.new("RGB", (300, 50), color=(240, 240, 240))


@pytest.fixture
def synthetic_tall_crop() -> Image.Image:
    """Create a synthetic tall crop (60 width x 300 height)."""
    return Image.new("RGB", (60, 300), color=(240, 240, 240))


@pytest.fixture
def temp_manifest_env(tmp_path: Path):
    """Create a temporary mock Phase 5 derived directory structure."""
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True)
    images_dir = tmp_path / "images"
    images_dir.mkdir(parents=True)

    # Create 3 synthetic images
    img1 = images_dir / "crop1.jpg"
    img2 = images_dir / "crop2.jpg"
    img3 = images_dir / "crop3.jpg"

    for img_path in [img1, img2, img3]:
        Image.new("RGB", (100, 40), color=(255, 255, 255)).save(img_path)

    # Create mock combined manifest
    data = [
        {
            "dataset": "rxhandbd",
            "derived_image_path": str(img1),
            "split": "train",
            "image_filename": "crop1.jpg",
            "transcription": "Paracetamol 500mg",
        },
        {
            "dataset": "rxhandbd",
            "derived_image_path": str(img2),
            "split": "val",
            "image_filename": "crop2.jpg",
            "transcription": "Amoxicillin 250mg",
        },
        {
            "dataset": "doctor_prescription_bd",
            "derived_image_path": str(img3),
            "split": "test",
            "image_filename": "crop3.jpg",
            "transcription": "Metformin 500mg",
        },
    ]
    df = pd.DataFrame(data)
    manifest_csv = manifests_dir / "combined_clean_manifest.csv"
    df.to_csv(manifest_csv, index=False)

    return tmp_path


# ===================================================================
# 1. Configuration Validation Tests
# ===================================================================

class TestConfigurationValidation:
    """Verify hardware safety and architectural constraints in configs."""

    def test_model_baseline_is_trocr_small(self):
        config = ModelConfig()
        assert config.model_name_or_path == "microsoft/trocr-small-handwritten"
        assert config.use_gradient_checkpointing is True

    def test_training_config_memory_safe_parameters(self):
        config = TrainingConfig()
        # Conservative batch size for RTX 3050 4GB VRAM
        assert config.per_device_train_batch_size == 2
        assert config.gradient_accumulation_steps == 8
        assert config.effective_batch_size == 16
        assert config.seed == 42
        assert config.metric_for_best_model == "cer"

    def test_batch_size_can_scale_down_to_one(self):
        config = TrainingConfig(per_device_train_batch_size=1, gradient_accumulation_steps=16)
        assert config.per_device_train_batch_size == 1
        assert config.effective_batch_size == 16


# ===================================================================
# 2. Aspect-Ratio Preserving Preprocessing Tests
# ===================================================================

class TestAspectRatioPreprocessing:
    """Verify aspect-ratio preserving resizing for word crops."""

    def test_narrow_crop_preserves_aspect_ratio(self, synthetic_narrow_crop):
        transform = AspectRatioPreservingResize(
            PreprocessingConfig(target_width=384, target_height=384, pad_color=255)
        )
        canvas, meta = transform.preprocess(synthetic_narrow_crop)

        assert canvas.size == (384, 384)
        assert meta["raw_dimensions"] == (300, 50)
        # Scaled width should hit 384, height proportional: 50 * (384/300) = 64
        assert meta["scaled_dimensions"] == (384, 64)
        assert meta["aspect_ratio_preserved"] is True
        # Top padding should be (384 - 64) // 2 = 160
        assert meta["padding"][1] == 160

    def test_tall_crop_preserves_aspect_ratio(self, synthetic_tall_crop):
        transform = AspectRatioPreservingResize(
            PreprocessingConfig(target_width=384, target_height=384, pad_color=255)
        )
        canvas, meta = transform.preprocess(synthetic_tall_crop)

        assert canvas.size == (384, 384)
        assert meta["raw_dimensions"] == (60, 300)
        # Scaled height hits 384, width proportional: 60 * (384/300) = 77
        assert meta["scaled_dimensions"] == (77, 384)
        assert meta["aspect_ratio_preserved"] is True


# ===================================================================
# 3. Manifest Loading & Dataset Tests
# ===================================================================

class TestManifestLoading:
    """Verify manifest loading, split filtering, and data integrity."""

    def test_manifest_loader_splits(self, temp_manifest_env):
        loader = HandwritingManifestLoader(phase5_dir=temp_manifest_env)

        train_records = loader.load_records("combined", split="train")
        val_records = loader.load_records("combined", split="val")
        test_records = loader.load_records("combined", split="test")

        assert len(train_records) == 1
        assert train_records[0].transcription == "Paracetamol 500mg"
        assert len(val_records) == 1
        assert len(test_records) == 1
        assert test_records[0].transcription == "Metformin 500mg"

    def test_missing_image_file_detection(self, temp_manifest_env):
        loader = HandwritingManifestLoader(phase5_dir=temp_manifest_env)
        # Point to nonexistent image in manifest
        manifest_path = temp_manifest_env / "manifests" / "combined_clean_manifest.csv"
        df = pd.read_csv(manifest_path)
        df.loc[0, "derived_image_path"] = str(temp_manifest_env / "images" / "nonexistent.jpg")
        df.to_csv(manifest_path, index=False)

        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load_records("combined", verify_files_exist=True)
        assert "missing image files" in str(exc_info.value)

    def test_real_external_manifest_counts_if_present(self):
        phase5_dir = get_phase5_derived_dir()
        if not (phase5_dir / "manifests" / "combined_clean_manifest.csv").is_file():
            pytest.skip("External phase5_derived dataset not present on current system.")

        loader = HandwritingManifestLoader(phase5_dir=phase5_dir)
        train_records = loader.load_records("combined", split="train")
        val_records = loader.load_records("combined", split="val")
        test_records = loader.load_records("combined", split="test")

        assert len(train_records) == 7101
        assert len(val_records) == 1107
        assert len(test_records) == 1776

        # Verify chinmays18 is NOT present
        datasets = {r.dataset.lower() for r in train_records}
        assert "chinmays18" not in datasets


# ===================================================================
# 4. Metric Calculations on Decoded Text Strings
# ===================================================================

class TestMetricCalculation:
    """Verify CER, WER, and Exact Match on decoded text predictions."""

    def test_levenshtein_distance(self):
        assert levenshtein_distance("kitten", "sitting") == 3
        assert levenshtein_distance("", "abc") == 3
        assert levenshtein_distance("same", "same") == 0

    def test_perfect_match_metrics(self):
        preds = ["Paracetamol 500mg", "Amoxicillin 250mg"]
        refs = ["Paracetamol 500mg", "Amoxicillin 250mg"]

        metrics = compute_handwriting_metrics(preds, refs)
        assert metrics["cer"] == 0.0
        assert metrics["wer"] == 0.0
        assert metrics["exact_match"] == 1.0
        assert metrics["exact_match_case_sensitive"] == 1.0

    def test_character_error_rate_calculation(self):
        # 1 insertion in 17-char string
        preds = ["Paracetamoll 500mg"]
        refs = ["Paracetamol 500mg"]

        cer = character_error_rate(preds, refs)
        expected = round(1 / 17, 4)
        assert cer == expected

    def test_word_error_rate_calculation(self):
        preds = ["Paracetamol 650mg"]
        refs = ["Paracetamol 500mg"]

        wer = word_error_rate(preds, refs)
        # 1 word wrong out of 2 = 0.5
        assert wer == 0.5

    def test_case_insensitive_exact_match(self):
        preds = ["paracetamol"]
        refs = ["PARACETAMOL"]

        metrics = compute_handwriting_metrics(preds, refs)
        assert metrics["exact_match"] == 1.0
        assert metrics["exact_match_case_sensitive"] == 0.0


# ===================================================================
# 5. Dataset-Specific Evaluation Grouping
# ===================================================================

class TestEvaluationGrouping:
    """Verify disaggregated evaluation across RxHandBD, Doctor BD, and Combined."""

    def test_evaluation_disaggregation(self, temp_manifest_env):
        evaluator = HandwritingEvaluator(phase5_dir=temp_manifest_env)

        # Mock predictor function returning constant text
        mock_pred_fn = lambda img: "Paracetamol 500mg"

        # Mock separate manifests for each benchmark
        manifests_dir = temp_manifest_env / "manifests"
        df_rx = pd.DataFrame([{
            "dataset": "rxhandbd",
            "derived_image_path": str(temp_manifest_env / "images" / "crop1.jpg"),
            "split": "test",
            "image_filename": "crop1.jpg",
            "transcription": "Paracetamol 500mg",
        }])
        df_rx.to_csv(manifests_dir / "rxhandbd_clean_manifest.csv", index=False)

        df_doc = pd.DataFrame([{
            "dataset": "doctor_prescription_bd",
            "derived_image_path": str(temp_manifest_env / "images" / "crop2.jpg"),
            "split": "test",
            "image_filename": "crop2.jpg",
            "transcription": "Amoxicillin 250mg",
        }])
        df_doc.to_csv(manifests_dir / "doctor_bd_clean_manifest.csv", index=False)

        report = evaluator.run_full_benchmark(mock_pred_fn)

        assert "rxhandbd_test" in report["benchmarks"]
        assert "doctor_bd_test" in report["benchmarks"]
        assert "combined_test" in report["benchmarks"]
        assert "This is not a medical diagnosis" in report["disclaimer"]


# ===================================================================
# 6. Test-Set Protection in Trainer
# ===================================================================

class TestTrainerTestSetProtection:
    """Verify trainer prevents test-set contamination."""

    def test_test_split_raises_error(self):
        trainer = TrOCRTrainer(HandwritingPipelineConfig())
        with pytest.raises(ValueError) as exc_info:
            trainer.validate_split_isolation(train_split="train", val_split="test")
        assert "SECURITY VIOLATION" in str(exc_info.value)


# ===================================================================
# 7. Adapter Interface & Confidence Labeling
# ===================================================================

class TestTrOCRAdapterAndInference:
    """Verify BaseOCREngine compliance and non-clinical confidence labeling."""

    def test_adapter_engine_name(self):
        adapter = TrOCREngineAdapter()
        assert adapter.get_engine_name() == "trocr_handwritten"
        assert isinstance(adapter, BaseOCREngine)

    def test_adapter_unavailable_raises_clean_error(self):
        adapter = TrOCREngineAdapter()
        with patch("handwriting.models.trocr_module.TrOCRModule.is_available", return_value=False):
            with pytest.raises(OCREngineUnavailableError) as exc_info:
                adapter.extract_from_image(b"fake_image")
            assert "TrOCR handwriting engine is not available" in str(exc_info.value)

    def test_confidence_labeled_as_model_derived_not_clinical(self):
        prediction = HandwritingPrediction(
            transcription="Azithromycin 500mg",
            confidence_score=0.92,
            confidence_label="Model-derived heuristic confidence score for verification purposes only.",
            raw_dimensions=(250, 40),
            preprocessed_dimensions=(384, 61),
        )
        assert "Model-derived" in prediction.confidence_label
        assert "not a medical diagnosis" in prediction.disclaimer.lower()
