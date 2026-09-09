"""
Digital PDF Extractor using pdfplumber.

Extracts text, preserves page structure, and identifies scanned / image-based PDFs.
MedIntel AI — Phase 4: PDF & OCR Pipeline
"""

from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple, Union
import pdfplumber
from PIL import Image

from ocr.models import PageExtraction
from ocr.ocr_engine import InvalidDocumentError


class PDFExtractor:
    """Extracts text and metadata from digital/native PDF documents using pdfplumber."""

    # Threshold for considering a PDF page as scanned/empty (under 20 characters of extractable text)
    MIN_DIGITAL_TEXT_CHARS_PER_PAGE = 20

    def extract_from_pdf(
        self,
        pdf_source: Union[Path, str, bytes, BytesIO],
    ) -> Tuple[List[PageExtraction], str, bool, List[str]]:
        """
        Extract text page-by-page from a PDF document.

        Args:
            pdf_source: File path or raw bytes of the PDF.

        Returns:
            Tuple containing:
            - pages: List of PageExtraction objects
            - full_text: Consolidated extracted text across all pages
            - is_likely_scanned: True if the PDF has little/no text and appears to be scanned
            - warnings: List of warning strings

        Raises:
            InvalidDocumentError: If the PDF is corrupted, password-protected, or unreadable.
        """
        pages: List[PageExtraction] = []
        warnings: List[str] = []
        full_text_parts: List[str] = []
        is_likely_scanned = False

        try:
            if isinstance(pdf_source, (bytes, bytearray)):
                pdf_file = BytesIO(pdf_source)
            elif isinstance(pdf_source, BytesIO):
                pdf_file = pdf_source
            else:
                pdf_file = open(str(pdf_source), "rb")

            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                if total_pages == 0:
                    warnings.append("PDF contains 0 pages.")
                    return pages, "", False, warnings

                empty_pages_count = 0
                has_images = False

                for page_idx, page in enumerate(pdf.pages):
                    page_num = page_idx + 1
                    try:
                        extracted = page.extract_text() or ""
                    except Exception as e:
                        extracted = ""
                        warnings.append(f"Page {page_num}: text extraction error ({str(e)})")

                    text_clean = extracted.strip()
                    char_count = len(text_clean)
                    word_count = len(text_clean.split())

                    # Check for embedded raster images
                    if getattr(page, "images", None) and len(page.images) > 0:
                        has_images = True

                    if char_count == 0:
                        empty_pages_count += 1

                    if text_clean:
                        full_text_parts.append(text_clean)

                    pages.append(
                        PageExtraction(
                            page_number=page_num,
                            text=text_clean,
                            confidence=1.0 if text_clean else 1.0,
                            char_count=char_count,
                            word_count=word_count,
                        )
                    )

                # Heuristic for scanned PDF: all or majority of pages have < threshold text, but have images or 0 text
                if empty_pages_count == total_pages:
                    is_likely_scanned = True
                    if has_images:
                        warnings.append(
                            "PDF appears to be scanned or image-based with no embedded digital text."
                        )
                    else:
                        warnings.append("PDF appears to be empty with no text content.")

                full_text = "\n\n".join(full_text_parts)
                return pages, full_text, is_likely_scanned, warnings

        except InvalidDocumentError:
            raise
        except Exception as e:
            raise InvalidDocumentError(f"Failed to parse PDF document: {str(e)}") from e

    def render_page_to_image(
        self,
        pdf_source: Union[Path, str, bytes, BytesIO],
        page_number: int = 1,
        resolution: int = 200,
    ) -> Image.Image:
        """
        Render a specific PDF page as a PIL Image for OCR processing.

        Args:
            pdf_source: PDF path or bytes.
            page_number: 1-based page number.
            resolution: Rendering resolution (DPI).

        Returns:
            PIL Image of the rendered page.
        """
        try:
            if isinstance(pdf_source, (bytes, bytearray)):
                pdf_file = BytesIO(pdf_source)
            elif isinstance(pdf_source, BytesIO):
                pdf_file = pdf_source
            else:
                pdf_file = open(str(pdf_source), "rb")

            with pdfplumber.open(pdf_file) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    raise ValueError(
                        f"Page {page_number} is out of bounds (1 to {len(pdf.pages)})"
                    )
                page = pdf.pages[page_number - 1]
                page_img = page.to_image(resolution=resolution)
                return page_img.original
        except Exception as e:
            raise InvalidDocumentError(f"Failed to render PDF page {page_number}: {str(e)}") from e
