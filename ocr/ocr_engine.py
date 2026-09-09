"""
Abstract base class and exception definitions for OCR engines.

MedIntel AI — Phase 4: PDF & OCR Pipeline
"""

from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Union
from PIL import Image

from ocr.models import PageExtraction


class OCRError(Exception):
    """Base exception for all OCR extraction errors."""
    pass


class OCREngineUnavailableError(OCRError):
    """Raised when the requested OCR engine is not installed or available on the system."""
    pass


class InvalidDocumentError(Exception):
    """Raised when a document is malformed, corrupted, or cannot be parsed."""
    pass


class DocumentSizeExceededError(Exception):
    """Raised when a document exceeds the allowed file size limit."""
    pass


class BaseOCREngine(ABC):
    """Abstract interface that all OCR engine adapters must implement."""

    @abstractmethod
    def extract_from_image(
        self,
        image: Union[Path, str, bytes, Image.Image],
        page_number: int = 1,
    ) -> PageExtraction:
        """
        Extract text and compute confidence from an image input.

        Args:
            image: Path to image file, raw bytes, or PIL Image object.
            page_number: 1-based page number to associate with this extraction.

        Returns:
            PageExtraction containing extracted text, confidence, char count, and word count.

        Raises:
            OCREngineUnavailableError: If the OCR engine binary/library is not installed.
            OCRError: If extraction fails during processing.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this OCR engine is installed and ready to use."""
        pass

    @abstractmethod
    def get_engine_name(self) -> str:
        """Return the name/identifier of this OCR engine."""
        pass

    @staticmethod
    def to_pil_image(image: Union[Path, str, bytes, Image.Image]) -> Image.Image:
        """Helper to convert various image input formats into a PIL Image object."""
        if isinstance(image, Image.Image):
            return image
        if isinstance(image, (str, Path)):
            return Image.open(str(image))
        if isinstance(image, (bytes, bytearray)):
            return Image.open(BytesIO(image))
        raise TypeError(f"Unsupported image input type: {type(image)}")
