"""
OCR Adapter for TrOCR Handwriting Recognition.

Integrates the TrOCR word/line model into the BaseOCREngine architecture.

ARCHITECTURAL BOUNDARY:
- TrOCR is designed specifically for handwritten word and line crops.
- It does NOT perform full-page document layout analysis or segmentation.
- Document extraction pipeline flow:
    Full document/page
            ↓
    Line/word region cropping
            ↓
    TrOCREngineAdapter (this adapter)
            ↓
    Candidate transcription
            ↓
    User verification
"""

from pathlib import Path
from typing import Optional, Union
from PIL import Image

from handwriting.inference.predictor import TrOCRPredictor
from handwriting.models.trocr_module import TrOCRModule
from ocr.models import PageExtraction
from ocr.ocr_engine import BaseOCREngine, OCREngineUnavailableError, OCRError


class TrOCREngineAdapter(BaseOCREngine):
    """Adapter exposing TrOCR handwriting model through the BaseOCREngine interface."""

    def __init__(
        self,
        predictor: Optional[TrOCRPredictor] = None,
        model_name: str = "microsoft/trocr-small-handwritten",
    ):
        self.model_name = model_name
        self.predictor = predictor or TrOCRPredictor()

    def is_available(self) -> bool:
        """Check whether TrOCR dependencies (torch, transformers) are installed."""
        return TrOCRModule.is_available()

    def get_engine_name(self) -> str:
        return "trocr_handwritten"

    def extract_from_image(
        self,
        image: Union[Path, str, bytes, Image.Image],
        page_number: int = 1,
    ) -> PageExtraction:
        """Extract text from a handwritten word/line crop using TrOCR.

        Args:
            image: Image crop of a handwritten word or line.
            page_number: Page or line sequence index.

        Returns:
            PageExtraction containing candidate transcription and character/word counts.

        Raises:
            OCREngineUnavailableError: If PyTorch/Transformers dependencies are not installed.
            OCRError: If model inference fails.
        """
        if not self.is_available():
            raise OCREngineUnavailableError(
                "TrOCR handwriting engine is not available. Please install dependencies: "
                "`pip install -r handwriting/requirements.txt`."
            )

        try:
            prediction = self.predictor.predict_crop(image)
            text = prediction.transcription.strip()

            return PageExtraction(
                page_number=page_number,
                text=text,
                confidence=1.0 if text else 0.0,
                char_count=len(text),
                word_count=len(text.split()),
            )
        except OCREngineUnavailableError:
            raise
        except Exception as e:
            raise OCRError(f"TrOCR handwriting extraction failed: {str(e)}") from e
