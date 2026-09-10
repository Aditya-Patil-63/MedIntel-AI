# MedIntel AI

**Intelligent Medical Report Analyzer Using Machine Learning and Generative AI**

> Final-Year Project

---

## Overview

MedIntel AI is an intelligent mobile application that analyzes medical reports and prescriptions — including handwritten ones — extracts test values, classifies them against medical reference ranges, predicts disease risk using machine learning, and provides simple multilingual explanations powered by Generative AI.

---

## Key Features

| #  | Feature                                      |
|----|----------------------------------------------|
| 1  | PDF medical report analysis                  |
| 2  | Scanned/image medical report analysis        |
| 3  | Printed prescription extraction              |
| 4  | Handwritten prescription recognition         |
| 5  | Medical test-value extraction                |
| 6  | Low / Normal / High / Critical classification (deterministic reference ranges) |
| 7  | Diabetes risk prediction (ML)                |
| 8  | Heart disease risk prediction (ML)           |
| 9  | Kidney disease risk prediction (ML)          |
| 10 | Simple-language explanations (Generative AI) |
| 11 | Multilingual: English, Hindi, Marathi, Gujarati |
| 12 | Report and history storage                   |
| 13 | Downloadable health summaries                |

---

## Architecture

```
Flutter Mobile App
        ↓
FastAPI Backend (Python)
        ↓
Document / Prescription Extraction
  ├── pdfplumber (digital PDFs)
  ├── EasyOCR / Tesseract (scanned/printed)
  └── TrOCR (handwritten prescriptions)
        ↓
Structured Medical Data (JSON)
        ↓
User Verification (confirm/correct extracted values)
        ↓
Deterministic Reference-Range Analysis
  └── Low / Normal / High / Critical classification
        ↓
ML Risk Prediction
  ├── Diabetes (Scikit-learn / XGBoost)
  ├── Heart Disease (Scikit-learn / XGBoost)
  └── Kidney Disease (Scikit-learn / XGBoost)
        ↓
Generative AI Explanation (Claude API)
        ↓
Multilingual Output (English, Hindi, Marathi, Gujarati)
        ↓
Health Summary + Report History
  └── Downloadable PDF summaries
```

---

## Technology Stack

| Layer               | Technology                          |
|---------------------|-------------------------------------|
| Mobile App          | Flutter (Dart)                      |
| Backend API         | FastAPI (Python 3.10+)              |
| PDF Extraction      | pdfplumber                          |
| Printed OCR         | EasyOCR and/or Tesseract            |
| Handwriting OCR     | TrOCR (TensorFlow / PyTorch)        |
| ML Models           | Scikit-learn, XGBoost               |
| Generative AI       | Claude API (Anthropic)              |
| Database            | SQLite (initial)                    |
| Languages Supported | English, Hindi, Marathi, Gujarati   |

---

## Project Structure

```
MedIntel-AI/
├── mobile/            # Flutter mobile application
├── backend/           # FastAPI + Python backend
├── ml/                # ML models and training scripts
├── ocr/               # OCR pipeline (pdfplumber, EasyOCR, Tesseract)
├── handwriting/       # Handwriting recognition (TrOCR)
├── database/          # SQLite schema, migrations, seed data
├── tests/             # Unit and integration tests
├── reports/           # Generated health summaries
├── docs/              # Documentation and diagrams
├── PROJECT_RULES.md   # Architecture, rules, and phase roadmap
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

---

## Phase Roadmap

| Phase | Name                              | Status         |
|-------|-----------------------------------|----------------|
| 1     | Project Foundation                | ✅ Complete     |
| 2     | Backend Setup                     | ✅ Complete     |
| 3     | Data Collection & Preparation     | ✅ Complete     |
| 4     | PDF & OCR Pipeline                | ✅ Complete     |
| 5     | Handwriting Recognition           | ✅ Complete     |
| 6     | Medical Reference Analysis        | ✅ Complete     |
| 7     | ML Risk Models                    | 🟡 In Progress (Steps 1–4 Complete) |
| 8     | Generative AI Integration         | ⬜ Pending      |
| 9     | Flutter Mobile App                | ⬜ Pending      |
| 10    | Integration & Testing             | ⬜ Pending      |
| 11    | Documentation & Deployment        | ⬜ Pending      |

See [PROJECT_RULES.md](PROJECT_RULES.md) for detailed phase descriptions and all project rules.

---

## Datasets Selected (Phase 3 & Phase 5)

The following datasets have been selected, verified, and audited:

1. **Diabetes Risk:** Pima Indians Diabetes Database (NIDDK, accessible via Kaggle / OpenML)
2. **Heart Disease Risk:** UCI Heart Disease Dataset — Cleveland processed subset (DOI: `10.24432/C52P4X`)
3. **Kidney Disease Risk:** UCI Chronic Kidney Disease Dataset (Apollo Hospitals, DOI: `10.24432/C5G020`)
4. **Handwriting Recognition (Phase 5):**
   - **RxHandBD**: 4,017 Train / 446 Val / 1,115 Test (official 1,115 test set preserved untouched)
   - **Doctor's Handwritten Prescription BD**: 3,084 Train / 661 Val / 661 Test (274 duplicate copies removed)
   - **Combined Primary**: 7,101 Train / 1,107 Val / 1,776 Test (9,984 unique real handwriting crops)
   - *Note:* `chinmays18` synthetic data is strictly excluded from primary training.

*Important:* Actual dataset files are strictly kept outside the Git repository under `MEDINTEL_DATA_DIR`.

---

## Safety Notice

> **MedIntel AI is an academic project. It is NOT a certified medical device or diagnostic tool. All outputs are for educational and informational purposes only. Users must consult qualified healthcare professionals for medical decisions.**

---

## Project Status

**Current Phase: Phase 7 — ML Risk Models (Steps 1–4 Complete)**

- **ML Risk Models & FastAPI Integration (`ml/`, `backend/app/api/ml_risk.py`, `backend/app/services/ml_risk_service.py`)**:
  - Leakage-safe 5-fold Stratified Cross-Validation across Diabetes, Heart Disease, and Chronic Kidney Disease.
  - Champion pipelines trained on 80% train split and evaluated on frozen 20% held-out test splits.
  - Model artifacts externally serialized to `D:\MedIntel-Datasets\ml_models\` with SHA-256 cryptographic verification.
  - Safe, structured FastAPI REST endpoints (`POST /api/v1/ml/diabetes-risk`, `POST /api/v1/ml/heart-risk`, `POST /api/v1/ml/kidney-risk`, `GET /api/v1/ml/status`).
  - In-memory lazy model caching, user verification safety gate (`is_user_verified`), zero-imputation policy (`INSUFFICIENT_FEATURES`), and SQLite `Prediction` persistence.
  - Complete integration guide documented in [docs/PHASE7_API_INTEGRATION.md](docs/PHASE7_API_INTEGRATION.md).
  - 48 Phase 7 tests across `tests/test_phase7_ml.py`, `tests/test_phase7_audit.py`, and `tests/test_phase7_api.py`.


- **Medical Reference Analysis (`reference/`)**:
  - Deterministic reference-range lookup engine (`reference/analyzer.py`, `reference/ranges.py`).
  - 14 audited reference entries across 10 core laboratory analytes based on ADA, WHO, Harrison's, NKF KDIGO, Tietz, and Mayo Clinic Laboratories.
  - Deterministic medical value parser (`reference/parser.py`) separating measurements from printed range intervals.
  - FastAPI REST endpoints (`POST /api/v1/reference/analyze`, `POST /api/v1/reference/parse-and-analyze`).
  - SQLite persistence with `TestResult` audit fields (`canonical_name`, `reference_source`, `analysis_status`) and user verification safety gate (`is_user_verified`).
  - Full regression test suite passing (165/165 tests, 1 warning).

- **Handwriting Recognition Pipeline (`handwriting/`)**:
  - Handwriting recognition pipeline implemented and evaluated using Microsoft TrOCR (`microsoft/trocr-small-handwritten`).
  - Native 2,000-optimizer-step training executed under strict 4 GB VRAM constraints (batch size 1, gradient accumulation 8, FP16 mixed precision, gradient checkpointing).
  - Official held-out evaluation achieved **67.68% case-insensitive exact match**, **20.34% CER**, and **43.89% WER** across 1,776 combined test samples.
  - Dataset-specific performance: **Doctor Prescription BD Test**: 5.55% CER, 8.06% WER, 91.83% Exact Match; **RxHandBD Test**: 28.78% CER, 63.30% WER, 53.36% Exact Match.
  - Complete benchmark results, error categorization, and safety boundaries documented in [docs/PHASE5_HANDWRITING_RESULTS.md](docs/PHASE5_HANDWRITING_RESULTS.md).
  - Full regression test suite passing (73/73 tests).