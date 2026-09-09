"""
Evaluation runner for handwriting recognition across distinct test sets.

Evaluates:
1. RxHandBD Test Split (1,115 images — official benchmark)
2. Doctor's Handwritten Prescription BD Test Split (661 images — deduplicated benchmark)
3. Combined Test Split (1,776 images — total real-world evaluation)

Strictly enforces:
- Metrics computed on DECODED TEXT PREDICTIONS against ground-truth references.
- No dictionary modification or vocabulary filtering on raw metrics.
- Test sets are evaluated in read-only mode and are never accessed during training.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from PIL import Image

from handwriting.config import EvaluationConfig, get_phase5_derived_dir
from handwriting.data.dataset import HandwritingManifestLoader
from handwriting.evaluation.metrics import compute_handwriting_metrics


class HandwritingEvaluator:
    """Orchestrates disaggregated evaluation across Phase 5 test sets."""

    def __init__(
        self,
        config: Optional[EvaluationConfig] = None,
        phase5_dir: Optional[Path] = None,
    ):
        self.config = config or EvaluationConfig()
        self.phase5_dir = phase5_dir or get_phase5_derived_dir()
        self.manifest_loader = HandwritingManifestLoader(phase5_dir=self.phase5_dir)

    def evaluate_split(
        self,
        predict_fn: Callable[[Image.Image], str],
        manifest_name: str = "combined",
        split: str = "test",
        max_samples: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Evaluate a prediction function on a specific manifest and split.

        Args:
            predict_fn: Callable that accepts a PIL Image and returns a decoded string prediction.
            manifest_name: 'combined', 'rxhandbd', or 'doctor_bd'.
            split: Split to evaluate (must be 'test' for benchmark evaluation).
            max_samples: Optional sample cap for smoke testing.

        Returns:
            Dictionary containing computed metrics and sample metadata.
        """
        records = self.manifest_loader.load_records(
            manifest_identifier=manifest_name,
            split=split,
        )

        if max_samples:
            records = records[:max_samples]

        predictions: List[str] = []
        references: List[str] = []
        sample_results: List[Dict[str, Any]] = []

        for record in records:
            ref_text = record.transcription
            try:
                with Image.open(record.image_path) as img:
                    img_rgb = img.convert("RGB")
                    # predict_fn MUST output a decoded text string
                    pred_text = predict_fn(img_rgb)
            except Exception as e:
                pred_text = ""

            predictions.append(pred_text)
            references.append(ref_text)

            if self.config.save_predictions:
                sample_results.append({
                    "image_filename": record.image_filename,
                    "dataset": record.dataset,
                    "reference": ref_text,
                    "prediction": pred_text,
                })

        metrics = compute_handwriting_metrics(predictions, references)

        return {
            "manifest": manifest_name,
            "split": split,
            "total_evaluated": len(records),
            "metrics": metrics,
            "samples": sample_results if self.config.save_predictions else [],
        }

    def run_full_benchmark(
        self,
        predict_fn: Callable[[Image.Image], str],
        model_name: str = "microsoft/trocr-small-handwritten",
        max_samples_per_split: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run standard Phase 5 benchmark across RxHandBD, Doctor BD, and Combined test splits.

        Args:
            predict_fn: Callable accepting PIL Image -> decoded string prediction.
            model_name: Model identifier for report logging.
            max_samples_per_split: Optional limit for fast test runs.

        Returns:
            Consolidated benchmark dictionary with separate results per test set.
        """
        rxhandbd_res = self.evaluate_split(
            predict_fn=predict_fn,
            manifest_name="rxhandbd",
            split="test",
            max_samples=max_samples_per_split,
        )

        doctor_bd_res = self.evaluate_split(
            predict_fn=predict_fn,
            manifest_name="doctor_bd",
            split="test",
            max_samples=max_samples_per_split,
        )

        combined_res = self.evaluate_split(
            predict_fn=predict_fn,
            manifest_name="combined",
            split="test",
            max_samples=max_samples_per_split,
        )

        report = {
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            "model_name": model_name,
            "metric_protocol": (
                "Decoded string predictions compared against ground-truth references. "
                "Raw metrics without medicine dictionary modification or post-hoc corrections."
            ),
            "benchmarks": {
                "rxhandbd_test": {
                    "expected_samples": 1115,
                    "evaluated_samples": rxhandbd_res["total_evaluated"],
                    "metrics": rxhandbd_res["metrics"],
                },
                "doctor_bd_test": {
                    "expected_samples": 661,
                    "evaluated_samples": doctor_bd_res["total_evaluated"],
                    "metrics": doctor_bd_res["metrics"],
                },
                "combined_test": {
                    "expected_samples": 1776,
                    "evaluated_samples": combined_res["total_evaluated"],
                    "metrics": combined_res["metrics"],
                },
            },
            "disclaimer": (
                "This is not a medical diagnosis. Please consult a qualified healthcare professional."
            ),
        }
        return report

    def save_benchmark_report(
        self,
        report: Dict[str, Any],
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Save benchmark report to JSON artifact."""
        out_dir = Path(output_dir or self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        report_file = out_dir / "phase5_trocr_evaluation_report.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report_file
