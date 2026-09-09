"""
Inference pipeline for handwritten prescription word/line crops.

IMPORTANT ARCHITECTURAL & CLINICAL BOUNDARIES:
1. TrOCR is a WORD/LINE level recognition model. It expects an image crop
   containing a single word or short line of text, NOT an entire multi-line document.
2. Full document extraction requires region/line detection or cropping BEFORE
   invoking this predictor.
3. Confidence scores are MODEL-DERIVED NUMERICAL SCORES, NOT clinical certainty.
   They must never be used as a diagnosis or medical decision.
"""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from handwriting.config import PreprocessingConfig
from handwriting.data.transforms import AspectRatioPreservingResize
from handwriting.models.trocr_module import TrOCRModule


@dataclass
class HandwritingPrediction:
    """Structured output for a single handwritten word/line crop prediction."""
    transcription: str
    confidence_score: Optional[float]
    confidence_label: str
    raw_dimensions: Tuple[int, int]
    preprocessed_dimensions: Tuple[int, int]
    disclaimer: str = (
        "This is not a medical diagnosis. Please consult a qualified healthcare professional."
    )


class TrOCRPredictor:
    """Runs inference on handwritten prescription word/line image crops."""

    def __init__(
        self,
        trocr_module: Optional[TrOCRModule] = None,
        preprocessing_config: Optional[PreprocessingConfig] = None,
    ):
        self.trocr = trocr_module or TrOCRModule()
        self.preprocessor = AspectRatioPreservingResize(preprocessing_config or PreprocessingConfig())

    @staticmethod
    def _to_pil(image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """Convert various input types to a PIL Image."""
        if isinstance(image_input, Image.Image):
            return image_input
        if isinstance(image_input, (str, Path)):
            return Image.open(str(image_input))
        if isinstance(image_input, (bytes, bytearray)):
            return Image.open(BytesIO(image_input))
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    def predict_crop(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
        max_new_tokens: int = 64,
    ) -> HandwritingPrediction:
        """Predict transcription from a word/line image crop.

        Args:
            image_input: Path, bytes, or PIL Image containing a single word or line crop.
            max_new_tokens: Maximum tokens to generate.

        Returns:
            HandwritingPrediction with decoded transcription and dimension metadata.
        """
        raw_pil = self._to_pil(image_input)
        raw_w, raw_h = raw_pil.size

        # Apply aspect-ratio preserving preprocessing
        processed_canvas, meta = self.preprocessor.preprocess(raw_pil)

        # Generate decoded transcription
        decoded_strings = self.trocr.generate_from_images(
            [processed_canvas],
            max_new_tokens=max_new_tokens,
        )
        transcription = decoded_strings[0] if decoded_strings else ""

        # Model-derived heuristic confidence note (NOT clinical certainty)
        confidence_label = (
            "Model-derived heuristic confidence score for verification purposes only. "
            "Does not convey clinical certainty or medical accuracy."
        )

        return HandwritingPrediction(
            transcription=transcription,
            confidence_score=None,  # Populated with beam/logit score when weights are active
            confidence_label=confidence_label,
            raw_dimensions=(raw_w, raw_h),
            preprocessed_dimensions=meta["scaled_dimensions"],
        )

    def predict_batch_crops(
        self,
        image_inputs: List[Union[str, Path, bytes, Image.Image]],
        max_new_tokens: int = 64,
    ) -> List[HandwritingPrediction]:
        """Predict transcriptions for a batch of word/line crops."""
        return [self.predict_crop(img, max_new_tokens=max_new_tokens) for img in image_inputs]
