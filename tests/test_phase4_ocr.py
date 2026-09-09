"""
MedIntel AI — Phase 4 Tests: Document & OCR Extraction Pipeline.

Tests verify:
    - Pure-Python synthetic PDF generation and digital extraction (pdfplumber)
    - Single-page and multi-page PDF processing
    - Empty/blank PDF handling and warnings
    - Malformed/corrupted PDF rejection
    - File size limit enforcement (rejection of oversized uploads)
    - Unsupported file type rejection (.txt, .exe, .docx)
    - Tesseract adapter availability and graceful error handling
    - EasyOCR adapter availability and graceful error handling
    - Mock OCR engine integration with synthetic image
    - FastAPI endpoint POST /api/v1/extract integration
    - Mandatory medical safety disclaimer presence
    - Absence of premature ML diagnosis or prescription changes

No machine learning models are tested.
No real patient data is used (pure synthetic data only).
"""

import io
import sys
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Ensure repository root and backend directory are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from ocr import (
    BaseOCREngine,
    DocumentExtractionResult,
    DocumentProcessor,
    DocumentSizeExceededError,
    EasyOCRAdapter,
    InvalidDocumentError,
    OCREngineUnavailableError,
    PageExtraction,
    PDFExtractor,
    SourceType,
    TesseractAdapter,
)


# ===================================================================
# Pure-Python Synthetic PDF & Image Test Helpers (Zero extra deps)
# ===================================================================

def make_synthetic_pdf(pages: List[str]) -> bytes:
    """
    Generate a minimal valid PDF 1.4 byte sequence with Type 1 font (Helvetica).
    Uses pure Python without requiring any external PDF-generation library.
    """
    objects = []
    page_ids = [4 + i * 2 for i in range(len(pages))]
    kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)

    # Obj 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    # Obj 2: Pages root
    objects.append(
        f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {len(pages)} >>\nendobj"
    )
    # Obj 3: Base font
    objects.append("3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")

    for i, text in enumerate(pages):
        page_id = 4 + i * 2
        content_id = 5 + i * 2

        # Sanitize text for PDF string literal
        safe_text = text.replace("(", "\\(").replace(")", "\\)")
        stream_content = f"BT\n/F1 12 Tf\n50 700 Td\n({safe_text}) Tj\nET"
        stream_bytes = stream_content.encode("latin-1")

        objects.append(
            f"{page_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 3 0 R >> >> >>\nendobj"
        )
        objects.append(
            f"{content_id} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n"
            f"{stream_content}\nendstream\nendobj"
        )

    out = ["%PDF-1.4\n"]
    offsets = []
    for obj in objects:
        offsets.append(sum(len(x.encode("latin-1")) for x in out))
        out.append(obj + "\n")

    xref_pos = sum(len(x.encode("latin-1")) for x in out)
    out.append(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n")
    for off in offsets:
        out.append(f"{off:010d} 00000 n \n")
    out.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    )

    return "".join(out).encode("latin-1")


def make_synthetic_image_bytes(format: str = "PNG") -> bytes:
    """Create a minimal 100x100 RGB synthetic test image in memory."""
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


class MockOCREngine(BaseOCREngine):
    """Deterministic Mock OCR engine for testing without external binaries."""

    def __init__(self, mock_text: str = "Mock Extracted Lab Data", confidence: float = 0.95):
        self.mock_text = mock_text
        self.confidence = confidence

    def is_available(self) -> bool:
        return True

    def get_engine_name(self) -> str:
        return "mock_ocr"

    def extract_from_image(
        self, image, page_number: int = 1
    ) -> PageExtraction:
        return PageExtraction(
            page_number=page_number,
            text=self.mock_text,
            confidence=self.confidence,
            char_count=len(self.mock_text),
            word_count=len(self.mock_text.split()),
        )


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def test_client():
    """FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
def document_processor():
    """Default DocumentProcessor instance."""
    return DocumentProcessor()


# ===================================================================
# PDFExtractor Tests
# ===================================================================

class TestPDFExtractor:
    """Tests for native digital PDF extraction via pdfplumber."""

    def test_single_page_pdf_extraction(self):
        pdf_bytes = make_synthetic_pdf(["Glucose: 95 mg/dL; HbA1c: 5.6%"])
        extractor = PDFExtractor()
        pages, full_text, is_scanned, warnings = extractor.extract_from_pdf(pdf_bytes)

        assert len(pages) == 1
        assert pages[0].page_number == 1
        assert "Glucose: 95 mg/dL" in pages[0].text
        assert "Glucose: 95 mg/dL" in full_text
        assert pages[0].confidence == 1.0
        assert is_scanned is False

    def test_multi_page_pdf_extraction(self):
        page_1 = "MedIntel Lab Report Page 1: Complete Blood Count"
        page_2 = "MedIntel Lab Report Page 2: Lipid Profile Panel"
        pdf_bytes = make_synthetic_pdf([page_1, page_2])

        extractor = PDFExtractor()
        pages, full_text, is_scanned, warnings = extractor.extract_from_pdf(pdf_bytes)

        assert len(pages) == 2
        assert pages[0].page_number == 1
        assert pages[1].page_number == 2
        assert "Complete Blood Count" in pages[0].text
        assert "Lipid Profile Panel" in pages[1].text
        assert "Complete Blood Count" in full_text
        assert "Lipid Profile Panel" in full_text

    def test_empty_page_pdf_warns(self):
        pdf_bytes = make_synthetic_pdf([""])
        extractor = PDFExtractor()
        pages, full_text, is_scanned, warnings = extractor.extract_from_pdf(pdf_bytes)

        assert len(pages) == 1
        assert pages[0].text == ""
        assert is_scanned is True
        assert any("empty" in w.lower() or "scanned" in w.lower() for w in warnings)

    def test_corrupted_pdf_raises_invalid_document_error(self):
        corrupted_bytes = b"%PDF-1.4\nCorrupted binary garbage without trailer"
        extractor = PDFExtractor()
        with pytest.raises(InvalidDocumentError):
            extractor.extract_from_pdf(corrupted_bytes)


# ===================================================================
# DocumentProcessor Validation & Routing Tests
# ===================================================================

class TestDocumentProcessor:
    """Tests for document processor validation, routing, and size limits."""

    def test_process_valid_digital_pdf(self, document_processor):
        pdf_bytes = make_synthetic_pdf(
            ["Patient Name: John Doe; Fasting Blood Sugar: 105 mg/dL; BP: 120/80"]
        )
        result = document_processor.process_document(
            file_bytes=pdf_bytes,
            filename="patient_report.pdf",
        )

        assert isinstance(result, DocumentExtractionResult)
        assert result.success is True
        assert result.source_type == SourceType.DIGITAL_PDF
        assert result.extractor == "pdfplumber"
        assert result.total_pages == 1
        assert "Fasting Blood Sugar: 105 mg/dL" in result.full_text
        assert result.confidence == 1.0
        assert "This is not a medical diagnosis" in result.disclaimer

    def test_oversized_file_rejected(self):
        processor = DocumentProcessor(max_file_size_bytes=1024)  # 1 KB limit
        large_bytes = b"0" * 2048

        with pytest.raises(DocumentSizeExceededError) as exc_info:
            processor.process_document(large_bytes, "large_file.pdf")
        assert "exceeds maximum allowed size" in str(exc_info.value)

    def test_unsupported_extension_rejected(self, document_processor):
        bad_bytes = b"Some plain text"
        with pytest.raises(InvalidDocumentError) as exc_info:
            document_processor.process_document(bad_bytes, "report.docx")
        assert "Unsupported file format" in str(exc_info.value)

    def test_corrupted_image_rejected(self, document_processor):
        corrupted_img = b"PNG NOT REAL IMAGE BYTES"
        with pytest.raises(InvalidDocumentError) as exc_info:
            document_processor.process_document(corrupted_img, "report.png")
        assert "Corrupted or invalid image" in str(exc_info.value)

    def test_mock_ocr_engine_processing_image(self, document_processor):
        mock_engine = MockOCREngine(mock_text="Hemoglobin: 14.2 g/dL", confidence=0.98)
        document_processor.register_ocr_engine("mock_ocr", mock_engine)

        img_bytes = make_synthetic_image_bytes("PNG")
        result = document_processor.process_document(
            file_bytes=img_bytes,
            filename="blood_test.png",
            engine_name="mock_ocr",
        )

        assert result.success is True
        assert result.source_type == SourceType.IMAGE
        assert result.extractor == "mock_ocr"
        assert result.total_pages == 1
        assert "Hemoglobin: 14.2 g/dL" in result.full_text
        assert result.confidence == 0.98


# ===================================================================
# OCR Engine Adapters & Fallback Tests
# ===================================================================

class TestOCREngines:
    """Tests for OCR engine adapters, error handling, and availability."""

    def test_tesseract_adapter_engine_name(self):
        adapter = TesseractAdapter()
        assert adapter.get_engine_name() == "tesseract"

    def test_tesseract_unavailable_raises_clean_exception(self):
        adapter = TesseractAdapter()
        with patch.object(adapter, "is_available", return_value=False):
            with pytest.raises(OCREngineUnavailableError) as exc_info:
                adapter.extract_from_image(b"fake_image_bytes")
            assert "Tesseract OCR is not available" in str(exc_info.value)

    def test_easyocr_adapter_engine_name(self):
        adapter = EasyOCRAdapter()
        assert adapter.get_engine_name() == "easyocr"

    def test_easyocr_unavailable_raises_clean_exception(self):
        adapter = EasyOCRAdapter()
        with patch.object(adapter, "is_available", return_value=False):
            with pytest.raises(OCREngineUnavailableError) as exc_info:
                adapter.extract_from_image(b"fake_image_bytes")
            assert "EasyOCR is not available" in str(exc_info.value)


# ===================================================================
# FastAPI Endpoint Integration Tests (POST /api/v1/extract)
# ===================================================================

class TestExtractionEndpoint:
    """Integration tests for POST /api/v1/extract endpoint."""

    def test_extract_endpoint_single_page_pdf(self, test_client):
        pdf_bytes = make_synthetic_pdf(
            ["Serum Creatinine: 1.1 mg/dL; Blood Urea: 24 mg/dL"]
        )

        response = test_client.post(
            "/api/v1/extract",
            files={"file": ("lab_report.pdf", pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "lab_report.pdf"
        assert data["source_type"] == "digital_pdf"
        assert data["extractor"] == "pdfplumber"
        assert data["total_pages"] == 1
        assert "Serum Creatinine: 1.1 mg/dL" in data["full_text"]
        assert "This is not a medical diagnosis" in data["disclaimer"]

    def test_extract_endpoint_multi_page_pdf(self, test_client):
        pdf_bytes = make_synthetic_pdf(
            ["Page 1: Liver Function Test", "Page 2: Renal Function Test"]
        )

        response = test_client.post(
            "/api/v1/extract",
            files={"file": ("multi_page.pdf", pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_pages"] == 2
        assert len(data["pages"]) == 2
        assert data["pages"][0]["page_number"] == 1
        assert data["pages"][1]["page_number"] == 2

    def test_extract_endpoint_unsupported_format_returns_400(self, test_client):
        response = test_client.post(
            "/api/v1/extract",
            files={"file": ("malicious.exe", b"MZexecutable", "application/octet-stream")},
        )

        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    def test_extract_endpoint_oversized_file_returns_400(self, test_client):
        # Override MAX_UPLOAD_SIZE_BYTES temporarily in processor
        from app.api.extraction import processor

        original_max = processor.max_file_size_bytes
        try:
            processor.max_file_size_bytes = 100  # 100 bytes limit
            oversized_pdf = make_synthetic_pdf(["Long test report text" * 20])
            response = test_client.post(
                "/api/v1/extract",
                files={"file": ("oversized.pdf", oversized_pdf, "application/pdf")},
            )
            assert response.status_code == 400
            assert "exceeds maximum allowed size" in response.json()["detail"]
        finally:
            processor.max_file_size_bytes = original_max

    def test_extract_endpoint_unavailable_ocr_engine_returns_503(self, test_client):
        img_bytes = make_synthetic_image_bytes("PNG")

        with patch("ocr.document_processor.TesseractAdapter.is_available", return_value=False):
            response = test_client.post(
                "/api/v1/extract?engine=tesseract",
                files={"file": ("scan.png", img_bytes, "image/png")},
            )
            assert response.status_code == 503
            assert "Tesseract OCR is not available" in response.json()["detail"]

    def test_mandatory_disclaimer_always_present(self, test_client):
        pdf_bytes = make_synthetic_pdf(["Glucose: 100 mg/dL"])
        response = test_client.post(
            "/api/v1/extract",
            files={"file": ("check_disclaimer.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "disclaimer" in data
        assert (
            data["disclaimer"]
            == "This is not a medical diagnosis. Please consult a qualified healthcare professional."
        )

    def test_no_diagnosis_in_extraction_output(self, test_client):
        """Extraction layer must only extract text, never output diagnosis or ML predictions."""
        pdf_bytes = make_synthetic_pdf(["Glucose: 350 mg/dL (CRITICAL HIGH)"])
        response = test_client.post(
            "/api/v1/extract",
            files={"file": ("glucose_report.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        # Verify no diagnosis keys exist in DocumentExtractionResult schema
        assert "diagnosis" not in data
        assert "prediction" not in data
        assert "treatment" not in data
        assert "risk_score" not in data
