"""
MedIntel AI — Phase 5: Handwriting Recognition.

Modular pipeline for handwritten medical prescription recognition using
Microsoft TrOCR (microsoft/trocr-small-handwritten).
"""

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
    word_error_rate,
)
from handwriting.inference.predictor import HandwritingPrediction, TrOCRPredictor
from handwriting.models.trocr_module import TrOCRModule
from handwriting.training.trainer import TrOCRTrainer

__all__ = [
    "get_phase5_derived_dir",
    "ModelConfig",
    "PreprocessingConfig",
    "TrainingConfig",
    "EvaluationConfig",
    "HandwritingPipelineConfig",
    "ManifestRecord",
    "HandwritingManifestLoader",
    "HandwritingDataset",
    "AspectRatioPreservingResize",
    "character_error_rate",
    "word_error_rate",
    "exact_match_accuracy",
    "compute_handwriting_metrics",
    "HandwritingEvaluator",
    "TrOCRModule",
    "TrOCRTrainer",
    "HandwritingPrediction",
    "TrOCRPredictor",
    "TrOCREngineAdapter",
]
