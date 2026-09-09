"""
Tesseract OCR Adapter.

Wraps pytesseract with availability checking and confidence calculation.
MedIntel AI — Phase 4: PDF & OCR Pipeline
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Union
from PIL import Image

try:
    import pytesseract
    from pytesseract import Output
    PYTESSERACT_INSTALLED = True
except ImportError:
    PYTESSERACT_INSTALLED = False

from ocr.models import PageExtraction
from ocr.ocr_engine import BaseOCREngine, OCREngineUnavailableError, OCRError


class TesseractAdapter(BaseOCREngine):
    """OCR Engine implementation using Tesseract OCR via pytesseract."""

    COMMON_WINDOWS_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize TesseractAdapter.

        Args:
            tesseract_cmd: Optional explicit path to the tesseract executable.
        """
        self._custom_cmd = tesseract_cmd
        if tesseract_cmd and PYTESSERACT_INSTALLED:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def _resolve_tesseract_binary(self) -> Optional[str]:
        """Locate tesseract binary on PATH or standard install directories."""
        if self._custom_cmd and os.path.isfile(self._custom_cmd):
            return self._custom_cmd

        which_path = shutil.which("tesseract")
        if which_path:
            return which_path

        for win_path in self.COMMON_WINDOWS_PATHS:
            if os.path.isfile(win_path):
                return win_path

        return None

    def is_available(self) -> bool:
        """Check if pytesseract is installed and the tesseract binary is executable."""
        if not PYTESSERACT_INSTALLED:
            return False

        bin_path = self._resolve_tesseract_binary()
        if not bin_path:
            return False

        try:
            pytesseract.pytesseract.tesseract_cmd = bin_path
            version = pytesseract.get_tesseract_version()
            return bool(version)
        except Exception:
            return False

    def get_engine_name(self) -> str:
        return "tesseract"

    def extract_from_image(
        self,
        image: Union[Path, str, bytes, Image.Image],
        page_number: int = 1,
    ) -> PageExtraction:
        """
        Extract text from an image using Tesseract OCR.

        Computes confidence from word-level confidence metrics.
        """
        if not self.is_available():
            raise OCREngineUnavailableError(
                "Tesseract OCR is not available. Please install Tesseract OCR on your system "
                "(e.g., from https://github.com/UB-Mannheim/tesseract/wiki on Windows, or "
                "`sudo apt-get install tesseract-ocr` on Linux) and add it to your system PATH."
            )

        try:
            pil_img = self.to_pil_image(image)
            # Ensure RGB or L mode
            if pil_img.mode not in ("RGB", "L"):
                pil_img = pil_img.convert("RGB")

            # Extract word-level data for confidence calculation
            data = pytesseract.image_to_data(pil_img, output_type=Output.DICT)
            
            words = []
            confidences = []

            for i, word in enumerate(data.get("text", [])):
                word_clean = word.strip()
                if word_clean:
                    words.append(word_clean)
                    conf = float(data["conf"][i])
                    # pytesseract returns -1 for spaces/empty blocks
                    if conf >= 0:
                        confidences.append(conf)

            full_text = pytesseract.image_to_string(pil_img).strip()

            # Confidence score calculation: average of word confidences mapped to [0.0, 1.0]
            if confidences:
                avg_confidence = (sum(confidences) / len(confidences)) / 100.0
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
            raise OCRError(f"Tesseract OCR extraction failed: {str(e)}") from e
