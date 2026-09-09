"""
OCR and Document Extraction Module.

MedIntel AI — Phase 4: PDF & OCR Pipeline
"""

from ocr.models import (
    DocumentExtractionResult,
    OCREngineType,
    PageExtraction,
    SourceType,
)
from ocr.ocr_engine import (
    BaseOCREngine,
    DocumentSizeExceededError,
    InvalidDocumentError,
    OCREngineUnavailableError,
    OCRError,
)
from ocr.pdf_extractor import PDFExtractor
from ocr.tesseract_adapter import TesseractAdapter
from ocr.easyocr_adapter import EasyOCRAdapter
from ocr.document_processor import DocumentProcessor

__all__ = [
    "DocumentExtractionResult",
    "SourceType",
    "OCREngineType",
    "PageExtraction",
    "BaseOCREngine",
    "OCRError",
    "OCREngineUnavailableError",
    "InvalidDocumentError",
    "DocumentSizeExceededError",
    "PDFExtractor",
    "TesseractAdapter",
    "EasyOCRAdapter",
    "DocumentProcessor",
]
