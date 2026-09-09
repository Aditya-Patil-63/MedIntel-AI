"""
EasyOCR Adapter.

Pluggable adapter for EasyOCR with lazy loading to avoid requiring PyTorch at startup.
MedIntel AI — Phase 4: PDF & OCR Pipeline
"""

from pathlib import Path
from typing import List, Optional, Union
from PIL import Image

from ocr.models import PageExtraction
from ocr.ocr_engine import BaseOCREngine, OCREngineUnavailableError, OCRError


class EasyOCRAdapter(BaseOCREngine):
    """OCR Engine implementation using EasyOCR with lazy loading."""

    def __init__(self, languages: Optional[List[str]] = None, use_gpu: bool = False):
        """
        Initialize EasyOCRAdapter.

        Args:
            languages: List of language codes, defaults to ['en'].
            use_gpu: Whether to enable GPU acceleration in EasyOCR.
        """
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu
        self._reader = None

    def is_available(self) -> bool:
        """Check if easyocr library is importable and functional."""
        try:
            import easyocr  # noqa: F401
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def _get_reader(self):
        """Lazy-load the EasyOCR Reader instance."""
        if self._reader is not None:
            return self._reader

        if not self.is_available():
            raise OCREngineUnavailableError(
                "EasyOCR is not available. To use EasyOCR, install PyTorch and easyocr "
                "via `pip install torch easyocr`."
            )

        try:
            import easyocr
            self._reader = easyocr.Reader(self.languages, gpu=self.use_gpu)
            return self._reader
        except Exception as e:
            raise OCREngineUnavailableError(f"Failed to initialize EasyOCR Reader: {str(e)}") from e

    def get_engine_name(self) -> str:
        return "easyocr"

    def extract_from_image(
        self,
        image: Union[Path, str, bytes, Image.Image],
        page_number: int = 1,
    ) -> PageExtraction:
        """
        Extract text from an image using EasyOCR.

        Args:
            image: Image path, bytes, or PIL Image.
            page_number: 1-based page index.

        Returns:
            PageExtraction containing extracted text and average confidence.
        """
        reader = self._get_reader()

        try:
            import numpy as np

            pil_img = self.to_pil_image(image)
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            img_np = np.array(pil_img)
            results = reader.readtext(img_np)

            text_segments = []
            confidences = []

            for item in results:
                # EasyOCR returns (bbox, text, conf)
                if len(item) >= 3:
                    _, text, conf = item[:3]
                    text_clean = str(text).strip()
                    if text_clean:
                        text_segments.append(text_clean)
                        confidences.append(float(conf))

            full_text = "\n".join(text_segments)

            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                avg_confidence = max(0.0, min(1.0, avg_confidence))
            else:
                avg_confidence = 1.0 if not full_text else 0.5

            return PageExtraction(
                page_number=page_number,
                text=full_text,
                confidence=round(avg_confidence, 4),
                char_count=len(full_text),
                word_count=len(full_text.split()),
            )
        except OCREngineUnavailableError:
            raise
        except Exception as e:
            raise OCRError(f"EasyOCR extraction failed: {str(e)}") from e
