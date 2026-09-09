# OCR & Document Extraction Module

> MedIntel AI — Phase 4: PDF & OCR Pipeline
>
> Architecture, setup, and usage guidelines for document ingestion and text extraction.

---

## 1. Overview

The `ocr/` module provides a modular, reliable document extraction layer for medical reports, lab sheets, and prescriptions. It determines the nature of the incoming document (digital PDF vs. scanned/image-based) and routes it to the optimal extraction pipeline.

```
Incoming Document (PDF / Image)
           │
           ▼
   DocumentProcessor (Validates format, size ≤ 10 MB)
           │
   ┌───────┴────────────────────────┐
   ▼                                ▼
Digital PDF                     Scanned PDF / Image
   │                                │
   ▼                                ▼
PDFExtractor (pdfplumber)       BaseOCREngine (Adapter Pattern)
   │                             ├── TesseractAdapter (pytesseract)
   │                             └── EasyOCRAdapter (easyocr, lazy-loaded)
   │                                │
   └───────────────┬────────────────┘
                   ▼
       DocumentExtractionResult
   (success, pages, full_text, confidence, warnings, safety disclaimer)
```

---

## 2. Supported Formats & Engines

| Format | Extensions | Primary Extraction Engine | Fallback / Alternative |
|--------|------------|---------------------------|------------------------|
| **Digital PDF** | `.pdf` | `pdfplumber` (native text) | OCR if pages are scanned |
| **Scanned PDF** | `.pdf` | Render to image + OCR | Tesseract or EasyOCR |
| **Image** | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp` | `TesseractAdapter` | `EasyOCRAdapter` |

---

## 3. Module Structure

```
ocr/
├── __init__.py               # Public API exports
├── models.py                 # Pydantic schemas (DocumentExtractionResult, PageExtraction, etc.)
├── ocr_engine.py             # BaseOCREngine ABC and custom exceptions
├── tesseract_adapter.py      # Tesseract OCR adapter with availability checks
├── easyocr_adapter.py        # EasyOCR adapter with lazy loading
├── pdf_extractor.py          # pdfplumber-based PDF extractor
├── document_processor.py     # Routing decision layer, validation, error handling
└── README.md                 # Module documentation (this file)
```

---

## 4. Setup & Engine Installation

### 4.1 Python Dependencies

Install the Phase 4 backend requirements:
```bash
pip install -r backend/requirements.txt
```
This installs `pdfplumber`, `pillow`, `pytesseract`, and `python-multipart`.

### 4.2 Tesseract OCR (System Executable)

`pytesseract` requires the standalone Tesseract OCR binary on your operating system:

- **Windows**:
  1. Download the installer from [UB-Mannheim Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).
  2. Install to default path (e.g. `C:\Program Files\Tesseract-OCR`).
  3. Ensure `tesseract.exe` is added to your system `PATH`.
  4. Alternatively via Chocolatey:
     ```powershell
     choco install tesseract
     ```
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr
  ```
- **macOS**:
  ```bash
  brew install tesseract
  ```

If Tesseract is not installed, `TesseractAdapter.is_available()` returns `False`, and invoking extraction raises a descriptive `OCREngineUnavailableError` without crashing the application.

### 4.3 EasyOCR (Optional PyTorch Engine)

EasyOCR is designed as a pluggable, lazy-loaded adapter. To enable EasyOCR:
```bash
pip install torch easyocr
```
If not installed, `EasyOCRAdapter.is_available()` returns `False` and informs the user how to install it.

---

## 5. Python API Usage

```python
from ocr import DocumentProcessor, SourceType

processor = DocumentProcessor(default_ocr_engine="tesseract")

# Extract from a digital PDF
with open("sample_report.pdf", "rb") as f:
    result = processor.process_document(
        file_bytes=f.read(),
        filename="sample_report.pdf",
    )

print(f"Extraction Succeeded: {result.success}")
print(f"Source Type: {result.source_type}")
print(f"Extractor: {result.extractor}")
print(f"Total Pages: {result.total_pages}")
print(f"Full Text:\n{result.full_text}")
print(f"Disclaimer: {result.disclaimer}")
```

---

## 6. Safety & Privacy Guardrails

1. **No Medical Diagnosis**: The extraction pipeline extracts raw text only. It does NOT diagnose conditions, classify lab values, or prescribe medication.
2. **Mandatory Disclaimer**: Every result includes the mandatory disclaimer:
   > *"This is not a medical diagnosis. Please consult a qualified healthcare professional."*
3. **Data Privacy**: No patient text is ever permanently written to disk or printed into logs. Only file metadata (filename, byte size, page count, extractor name) is logged.
4. **File Size Enforcement**: Strict default 10MB limit prevents denial-of-service / memory exhaustion attacks.
