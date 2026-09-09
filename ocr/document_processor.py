"""
Document Processor & Routing Decision Layer.

Orchestrates document classification, size validation, routing between
pdfplumber and OCR engines, and returns consolidated DocumentExtractionResult.
MedIntel AI — Phase 4: PDF & OCR Pipeline
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Type, Union
from PIL import Image

from ocr.easyocr_adapter import EasyOCRAdapter
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


class DocumentProcessor:
    """
    Coordinates document ingestion, validation, routing, and text extraction.
    """

    ALLOWED_PDF_EXTENSIONS = {".pdf"}
    ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
    DEFAULT_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

    def __init__(
        self,
        default_ocr_engine: str = "tesseract",
        max_file_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
    ):
        """
        Initialize the DocumentProcessor.

        Args:
            default_ocr_engine: Default OCR engine name ('tesseract' or 'easyocr').
            max_file_size_bytes: Maximum allowed document size in bytes.
        """
        self.default_ocr_engine_name = default_ocr_engine.lower()
        self.max_file_size_bytes = max_file_size_bytes
        self.pdf_extractor = PDFExtractor()
        self._custom_ocr_engines: Dict[str, BaseOCREngine] = {}

    def register_ocr_engine(self, name: str, engine: BaseOCREngine) -> None:
        """Register a custom or mock OCR engine instance."""
        self._custom_ocr_engines[name.lower()] = engine

    def get_ocr_engine(self, engine_name: Optional[str] = None) -> BaseOCREngine:
        """
        Resolve an OCR engine by name.

        Args:
            engine_name: 'tesseract', 'easyocr', or a registered custom engine name.

        Returns:
            An instance implementing BaseOCREngine.
        """
        name = (engine_name or self.default_ocr_engine_name).lower()
        if name in self._custom_ocr_engines:
            return self._custom_ocr_engines[name]
        if name == "tesseract":
            return TesseractAdapter()
        if name == "easyocr":
            return EasyOCRAdapter()
        raise ValueError(
            f"Unknown OCR engine '{engine_name}'. Supported: 'tesseract', 'easyocr', "
            f"or registered engines ({list(self._custom_ocr_engines.keys())})"
        )

    def validate_file(self, filename: str, file_bytes: bytes) -> str:
        """
        Validate file extension and size.

        Returns:
            The normalized lowercase file extension (e.g. '.pdf', '.png').

        Raises:
            DocumentSizeExceededError: If file exceeds maximum size.
            InvalidDocumentError: If file extension is unsupported.
        """
        if len(file_bytes) > self.max_file_size_bytes:
            max_mb = self.max_file_size_bytes / (1024 * 1024)
            actual_mb = len(file_bytes) / (1024 * 1024)
            raise DocumentSizeExceededError(
                f"File size ({actual_mb:.2f} MB) exceeds maximum allowed size ({max_mb:.1f} MB)."
            )

        ext = Path(filename).suffix.lower()
        all_allowed = self.ALLOWED_PDF_EXTENSIONS | self.ALLOWED_IMAGE_EXTENSIONS
        if ext not in all_allowed:
            raise InvalidDocumentError(
                f"Unsupported file format '{ext}'. Allowed formats: {sorted(list(all_allowed))}"
            )

        return ext

    def process_document(
        self,
        file_bytes: bytes,
        filename: str,
        engine_name: Optional[str] = None,
        force_ocr_on_pdf: bool = False,
    ) -> DocumentExtractionResult:
        """
        Process an uploaded document (PDF or Image) and extract text.

        Args:
            file_bytes: Raw content bytes of the uploaded file.
            filename: Name of the uploaded file.
            engine_name: Optional explicit OCR engine ('tesseract' or 'easyocr').
            force_ocr_on_pdf: If True, renders PDF pages to images and runs OCR.

        Returns:
            DocumentExtractionResult with extracted text, metadata, and safety disclaimer.
        """
        ext = self.validate_file(filename, file_bytes)
        warnings: List[str] = []
        errors: List[str] = []

        # ----------------------------------------------------
        # Route 1: PDF Document Handling
        # ----------------------------------------------------
        if ext in self.ALLOWED_PDF_EXTENSIONS:
            if not force_ocr_on_pdf:
                try:
                    pages, full_text, is_scanned, pdf_warnings = self.pdf_extractor.extract_from_pdf(
                        file_bytes
                    )
                    warnings.extend(pdf_warnings)

                    # If not scanned or text was found, return native digital PDF extraction
                    if not is_scanned or len(full_text.strip()) > 0:
                        return DocumentExtractionResult(
                            success=True,
                            filename=filename,
                            source_type=SourceType.DIGITAL_PDF,
                            extractor="pdfplumber",
                            total_pages=len(pages),
                            pages=pages,
                            full_text=full_text,
                            confidence=1.0,
                            warnings=warnings,
                            errors=errors,
                        )

                    # Textless PDF detected: check if OCR engine is available for fallback
                    ocr_engine = self.get_ocr_engine(engine_name)
                    if not ocr_engine.is_available():
                        warnings.append(
                            f"PDF contains no digital text, and OCR engine '{ocr_engine.get_engine_name()}' "
                            f"is not available for scanned page extraction."
                        )
                        return DocumentExtractionResult(
                            success=True,
                            filename=filename,
                            source_type=SourceType.SCANNED_PDF,
                            extractor="none",
                            total_pages=len(pages),
                            pages=pages,
                            full_text=full_text,
                            confidence=0.0,
                            warnings=warnings,
                            errors=errors,
                        )

                    warnings.append(
                        "PDF contains minimal or no native text. Attempting OCR on rendered pages."
                    )
                except InvalidDocumentError:
                    raise
                except Exception as e:
                    raise InvalidDocumentError(f"Error parsing PDF file: {str(e)}") from e

            # OCR fallback for scanned PDF
            return self._ocr_pdf(file_bytes, filename, engine_name, warnings)

        # ----------------------------------------------------
        # Route 2: Image Document Handling
        # ----------------------------------------------------
        return self._ocr_image(file_bytes, filename, engine_name, warnings)

    def _ocr_image(
        self,
        image_bytes: bytes,
        filename: str,
        engine_name: Optional[str],
        warnings: List[str],
    ) -> DocumentExtractionResult:
        """Process a single image using the selected OCR engine."""
        ocr_engine = self.get_ocr_engine(engine_name)
        active_engine_name = ocr_engine.get_engine_name()

        # Validate that image is readable
        try:
            from io import BytesIO
            with Image.open(BytesIO(image_bytes)) as img:
                img.verify()
        except Exception as e:
            raise InvalidDocumentError(f"Corrupted or invalid image file: {str(e)}") from e

        page_result = ocr_engine.extract_from_image(image_bytes, page_number=1)

        if not page_result.text.strip():
            warnings.append("OCR engine detected no readable text in the image.")

        return DocumentExtractionResult(
            success=True,
            filename=filename,
            source_type=SourceType.IMAGE,
            extractor=active_engine_name,
            total_pages=1,
            pages=[page_result],
            full_text=page_result.text,
            confidence=page_result.confidence,
            warnings=warnings,
            errors=[],
        )

    def _ocr_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        engine_name: Optional[str],
        warnings: List[str],
    ) -> DocumentExtractionResult:
        """Render pages of a scanned PDF and run OCR on each page."""
        ocr_engine = self.get_ocr_engine(engine_name)
        active_engine_name = ocr_engine.get_engine_name()

        # Check engine availability before attempting page rendering
        if not ocr_engine.is_available():
            raise OCREngineUnavailableError(
                f"Cannot perform OCR on scanned PDF: '{active_engine_name}' engine is unavailable."
            )

        import pdfplumber
        from io import BytesIO

        pages: List[PageExtraction] = []
        confidences: List[float] = []

        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                total_pages = len(pdf.pages)
                for page_idx in range(total_pages):
                    page_num = page_idx + 1
                    try:
                        pil_img = self.pdf_extractor.render_page_to_image(
                            pdf_bytes, page_number=page_num
                        )
                        page_ext = ocr_engine.extract_from_image(pil_img, page_number=page_num)
                        pages.append(page_ext)
                        confidences.append(page_ext.confidence)
                    except Exception as e:
                        warnings.append(f"Failed to OCR PDF page {page_num}: {str(e)}")
                        pages.append(
                            PageExtraction(
                                page_number=page_num,
                                text="",
                                confidence=0.0,
                                char_count=0,
                                word_count=0,
                            )
                        )
                        confidences.append(0.0)

            full_text = "\n\n".join(p.text for p in pages if p.text.strip())
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return DocumentExtractionResult(
                success=True,
                filename=filename,
                source_type=SourceType.SCANNED_PDF,
                extractor=f"pdfplumber+{active_engine_name}",
                total_pages=len(pages),
                pages=pages,
                full_text=full_text,
                confidence=round(avg_confidence, 4),
                warnings=warnings,
                errors=[],
            )
        except OCREngineUnavailableError:
            raise
        except Exception as e:
            raise InvalidDocumentError(f"Failed to process scanned PDF: {str(e)}") from e
