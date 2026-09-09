"""
Data models and schemas for the document and OCR extraction pipeline.

MedIntel AI — Phase 4: PDF & OCR Pipeline
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Document source type classification."""
    DIGITAL_PDF = "digital_pdf"
    SCANNED_PDF = "scanned_pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


class OCREngineType(str, Enum):
    """Available OCR engine types."""
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    PDFPLUMBER = "pdfplumber"
    NONE = "none"


class PageExtraction(BaseModel):
    """Extracted text and metadata for a single document page."""
    page_number: int = Field(..., description="1-based page index", ge=1)
    text: str = Field(..., description="Raw text extracted from this page")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for this page extraction (0.0 to 1.0)",
    )
    char_count: int = Field(default=0, ge=0, description="Character count")
    word_count: int = Field(default=0, ge=0, description="Word count")


class DocumentExtractionResult(BaseModel):
    """Overall document extraction result returned by the pipeline."""
    success: bool = Field(..., description="Whether extraction succeeded")
    filename: str = Field(..., description="Original name of the uploaded document")
    source_type: SourceType = Field(..., description="Detected source type")
    extractor: str = Field(..., description="Extraction engine/method used")
    total_pages: int = Field(default=0, ge=0, description="Total pages processed")
    pages: List[PageExtraction] = Field(
        default_factory=list,
        description="Per-page extraction details",
    )
    full_text: str = Field(default="", description="Consolidated extracted text across all pages")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall extraction confidence score (0.0 to 1.0)",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings encountered during extraction",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered during extraction if any",
    )
    disclaimer: str = Field(
        default="This is not a medical diagnosis. Please consult a qualified healthcare professional.",
        description="Mandatory medical safety disclaimer",
    )
