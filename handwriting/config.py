"""
MedIntel AI — Phase 5: Handwriting Recognition Configuration.

Configurable parameters for model architectures, memory-safe training,
aspect-ratio preserving image preprocessing, and external dataset access.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def get_data_dir() -> Path:
    """Resolve the root external dataset directory from MEDINTEL_DATA_DIR."""
    data_dir = os.environ.get("MEDINTEL_DATA_DIR", r"D:\MedIntel-Datasets")
    return Path(data_dir)


def get_phase5_derived_dir() -> Path:
    """Return path to Phase 5 derived dataset directory."""
    return get_data_dir() / "handwriting" / "phase5_derived"


@dataclass
class ModelConfig:
    """TrOCR model architecture configuration.

    Baseline architecture: microsoft/trocr-small-handwritten (~62M parameters).
    Targeted at word/line-level medical prescription recognition.
    """
    model_name_or_path: str = "microsoft/trocr-small-handwritten"
    max_target_length: int = 64
    image_size: int = 384  # Expected input dimension for TrOCR vision encoder
    use_gradient_checkpointing: bool = True  # Critical for 4GB VRAM


@dataclass
class PreprocessingConfig:
    """Configuration for aspect-ratio aware image preprocessing.

    Distinguishes:
    - raw source image dimensions (variable width/height)
    - preprocessing dimensions (aspect-ratio preserved with padding)
    - model input representation (normalized tensor for TrOCR)
    """
    preserve_aspect_ratio: bool = True
    target_height: int = 384
    target_width: int = 384
    pad_color: int = 255  # White background padding for document crops
    resample_filter: str = "BICUBIC"


@dataclass
class TrainingConfig:
    """Memory-safe training parameters for NVIDIA RTX 3050 Laptop GPU (4 GB VRAM).

    Conservative configuration:
    - per_device_train_batch_size: 2
    - gradient_accumulation_steps: 8
    - effective_batch_size: 16
    - fp16 mixed precision when CUDA is available
    - gradient checkpointing enabled

    Can be scaled down to per_device_train_batch_size = 1 without pipeline changes
    if severe memory constraints occur.
    """
    seed: int = 42
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    per_device_eval_batch_size: int = 4
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    num_train_epochs: int = 8
    warmup_ratio: float = 0.1
    fp16: bool = True
    early_stopping_patience: int = 2
    metric_for_best_model: str = "cer"  # Validation Character Error Rate
    greater_is_better: bool = False
    checkpoint_dir: str = "checkpoints/trocr_small"
    output_dir: str = "reports/handwriting"

    @property
    def effective_batch_size(self) -> int:
        """Calculate effective batch size after gradient accumulation."""
        return self.per_device_train_batch_size * self.gradient_accumulation_steps


@dataclass
class EvaluationConfig:
    """Evaluation protocol configuration.

    Metrics (CER, WER, Exact Match) are calculated strictly on decoded text
    predictions against ground-truth transcriptions.
    """
    batch_size: int = 4
    save_predictions: bool = True
    report_raw_metrics: bool = True
    allow_dictionary_correction: bool = False  # Raw metrics must remain untouched
    output_dir: str = "reports/handwriting"


@dataclass
class HandwritingPipelineConfig:
    """Unified configuration for the handwriting recognition pipeline."""
    model: ModelConfig = field(default_factory=ModelConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    phase5_dir: Optional[Path] = None

    def __post_init__(self):
        if self.phase5_dir is None:
            self.phase5_dir = get_phase5_derived_dir()
