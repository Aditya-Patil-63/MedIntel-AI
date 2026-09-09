# Tests — MedIntel AI

Test suite for MedIntel AI.

## Status

- **Phase 2 Backend Tests:** `backend/tests/test_phase2.py` (11 passing tests)
- **Phase 3 Data Preparation Tests:** `tests/test_phase3_data.py` (24 passing tests)
- **Phase 4 PDF & OCR Pipeline Tests:** `tests/test_phase4_ocr.py` (20 passing tests)
- **Phase 5 Handwriting Recognition Tests:** `tests/test_phase5_handwriting.py` (18 passing tests)
- **Total Passing Tests:** 73 tests

## Running Tests

From the repository root:

```bash
# Run Phase 5 Handwriting Recognition Tests
.\backend\venv\Scripts\python.exe -m pytest tests/test_phase5_handwriting.py -v

# Run Phase 4 Document & OCR Tests
.\backend\venv\Scripts\python.exe -m pytest tests/test_phase4_ocr.py -v

# Run Phase 3 Data Preparation Tests
.\backend\venv\Scripts\python.exe -m pytest tests/test_phase3_data.py -v

# Run Phase 2 Backend Tests
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_phase2.py -v

# Run All Tests
.\backend\venv\Scripts\python.exe -m pytest -v
```

## Structure

- `tests/test_phase5_handwriting.py` — Tests for Phase 5 Handwriting Recognition: configuration validation for RTX 3050 4GB VRAM (effective batch size 16, gradient checkpointing), aspect-ratio preserving transforms (raw, preprocessed, and canvas dimensions), manifest loading and split filtering, missing-image detection, split integrity (7,101 train / 1,107 val / 1,776 test, chinmays18 excluded), metric calculations (CER, WER, Exact Match on decoded text predictions), dataset-specific evaluation grouping (RxHandBD, Doctor BD, Combined), trainer test-set isolation protection, TrOCREngineAdapter BaseOCREngine compliance, and non-clinical confidence score labeling. Zero GPU and zero weight downloads required.
- `tests/test_phase4_ocr.py` — Tests for pure-Python synthetic PDF generation, single/multi-page digital extraction (`pdfplumber`), blank PDF warnings, malformed file rejection, file size limit enforcement, unsupported extension rejection, Tesseract adapter fallback, EasyOCR adapter lazy loading, mock OCR processing, FastAPI `POST /api/v1/extract` endpoint integration, and mandatory medical safety disclaimer verification (using synthetic test data only; zero real patient data).
- `tests/test_phase3_data.py` — Tests for external dataset path handling, missing-file handling, expected columns, deterministic cleaning logic, target encoding, and repository cleanliness checks (all using synthetic data; no real patient data).
- `backend/tests/test_phase2.py` — Tests for FastAPI startup, health-check endpoint, and SQLite schema.
