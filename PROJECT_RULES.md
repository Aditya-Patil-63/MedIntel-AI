# MedIntel AI — Project Rules & Architecture

> Intelligent Medical Report Analyzer Using Machine Learning and Generative AI
>
> Final-Year Project

---

## 1. System Architecture

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
Multilingual Output
  ├── English
  ├── Hindi
  ├── Marathi
  └── Gujarati
        ↓
Health Summary + Report History
  └── Downloadable PDF summaries
```

---

## 2. Project Structure

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
├── PROJECT_RULES.md   # This file — architecture and rules
├── README.md          # Project overview
└── .gitignore         # Git ignore rules
```

---

## 3. Technology Stack

| Layer               | Technology                          |
|---------------------|-------------------------------------|
| Mobile App          | Flutter (Dart)                      |
| Backend API         | FastAPI (Python 3.10+)              |
| PDF Extraction      | pdfplumber                          |
| Printed OCR         | EasyOCR and/or Tesseract            |
| Handwriting OCR     | TrOCR (TensorFlow / PyTorch)        |
| ML Models           | Scikit-learn, XGBoost               |
| Generative AI       | Claude API (Anthropic)              |
| Database            | SQLite (initial), upgradeable later |
| Languages Supported | English, Hindi, Marathi, Gujarati   |

---

## 4. Supported Input Types

1. **Digital PDF reports** — Native text extraction via pdfplumber
2. **Scanned/image medical reports** — OCR via EasyOCR / Tesseract
3. **Printed prescriptions** — OCR pipeline
4. **Handwritten prescriptions** — TrOCR deep learning model

---

## 5. Core Features

1. Medical test-value extraction from reports and prescriptions
2. Low / Normal / High / Critical classification using **deterministic reference ranges** (not ML)
3. Diabetes risk prediction (ML)
4. Heart disease risk prediction (ML)
5. Kidney disease risk prediction (ML)
6. Simple-language explanations via Generative AI (Claude API)
7. Multilingual support: English, Hindi, Marathi, Gujarati
8. Report and history storage per user
9. Downloadable health summary PDFs

---

## 6. Development Rules

### 6.1 General

- **Phase-gated development**: Do not implement features from a later phase until the current phase is complete and verified.
- **No placeholder predictions**: Never return fake, hardcoded, or random medical predictions. If a model is not trained, the feature must be clearly marked as unavailable.
- **No hallucinated medical data**: All reference ranges must come from verified medical sources. Never invent reference ranges.
- **User verification is mandatory**: Every extracted value must be shown to the user for confirmation before analysis.

### 6.2 Code Standards

- **Python**: Follow PEP 8. Use type hints for all function signatures.
- **Dart/Flutter**: Follow the official Dart style guide. Use `flutter analyze` with zero warnings.
- **Naming**: Use `snake_case` for Python files, functions, and variables. Use `camelCase` for Dart.
- **Docstrings**: All public functions and classes must have docstrings.
- **No hardcoded secrets**: API keys, credentials, and sensitive config must use environment variables (`.env` files, excluded from Git).

### 6.3 Git & Version Control

- Write clear, descriptive commit messages.
- Do not commit large model files, datasets, or binary artifacts to Git.
- Use `.gitignore` to exclude generated files, virtual environments, and IDE config.

---

## 7. Safety Rules

> **CRITICAL**: This application handles medical data. These rules are non-negotiable.

1. **No diagnosis**: The application provides **risk indicators and educational information only**. It does NOT diagnose medical conditions.
2. **Mandatory disclaimer**: Every prediction and explanation must include a disclaimer stating: *"This is not a medical diagnosis. Please consult a qualified healthcare professional."*
3. **No treatment advice**: The application must NEVER suggest medications, dosages, or treatment plans.
4. **Reference-range analysis is deterministic**: Classification of test values as Low / Normal / High / Critical must use published medical reference ranges — never ML predictions.
5. **ML models predict risk, not diagnosis**: ML outputs are probability scores for risk estimation, clearly labeled as such.
6. **GenAI outputs are explanatory only**: Claude API is used to explain results in simple language. It must not generate diagnoses or treatment suggestions.
7. **Data privacy**: No real patient data in the repository. All test data must be synthetic or anonymized.
8. **User confirmation**: Extracted data must be presented to the user for verification before any analysis is performed.

---

## 8. Testing Requirements

- **Unit tests**: Required for all utility functions, data processing, and ML inference code.
- **Integration tests**: Required for the full pipeline (upload → extraction → analysis → explanation).
- **Test data**: Use synthetic/anonymized medical data only. Never use real patient data.
- **Minimum coverage target**: 70% line coverage for backend and ML modules.
- **Flutter tests**: Widget tests for key UI components.

---

## 9. Phase Roadmap

### Phase 1 — Project Foundation ✅
- Repository initialization
- Directory structure creation
- PROJECT_RULES.md, README.md, .gitignore
- No code, no models, no dependencies

### Phase 2 — Backend Setup ✅
- FastAPI project initialization
- Basic project configuration (requirements.txt, .env.example)
- SQLite database schema design
- Health-check endpoint
- Basic project scaffolding

### Phase 3 — Data Collection & Preparation ✅
- Dataset research, selection, and verification for 3 risk prediction tasks:
  1. **Diabetes:** Pima Indians Diabetes Database (NIDDK, accessible via Kaggle / OpenML)
  2. **Heart Disease:** UCI Heart Disease Dataset (Cleveland subset, processed, DOI: 10.24432/C52P4X)
  3. **Kidney Disease:** UCI Chronic Kidney Disease Dataset (Apollo Hospitals, DOI: 10.24432/C5G020)
- Policy enforcement: Datasets strictly stored outside Git repository (`MEDINTEL_DATA_DIR`)
- Dataset source documentation (`ml/data/DATASET_SOURCES.md`)
- Dataset setup guide (`ml/data/DATASET_SETUP.md`)
- Dataset metadata (`ml/data/metadata/`)
- Data quality report and leakage prevention strategy (`ml/data/DATA_QUALITY_REPORT.md`)
- Reproducible inspection scripts (`ml/scripts/inspect_*.py`)
- Reproducible deterministic preparation scripts (`ml/scripts/prepare_*.py`)
- Unit tests for preparation utilities (`tests/test_phase3_data.py`)
- *Note: ML models are NOT trained in this phase (deferred to Phase 7).*

### Phase 4 — PDF & OCR Pipeline ✅
- pdfplumber integration for digital/native PDF text extraction
- Pluggable OCR engine adapter architecture (`BaseOCREngine`)
- Tesseract adapter (`pytesseract`) with availability checks and confidence calculation
- EasyOCR adapter (`easyocr`) with lazy loading to avoid heavy dependencies at startup
- `DocumentProcessor` routing decision layer enforcing 10MB limit and format validation
- Structured extraction schema (`DocumentExtractionResult`, `PageExtraction`, `SourceType`)
- FastAPI endpoint `POST /api/v1/extract` with privacy-preserving logging
- Mandatory medical safety disclaimer on all extraction responses
- Comprehensive unit and integration test suite (`tests/test_phase4_ocr.py`)

### Phase 5 — Handwriting Recognition ✅
- External dataset curation completed: 9,984 real handwriting images (7,101 train / 1,107 val / 1,776 test)
- RxHandBD official test split preserved (1,115); Doctor BD deduplicated (661 val / 661 test); chinmays18 excluded
- Architecture established around `microsoft/trocr-small-handwritten` for word/line crop recognition
- Aspect-ratio preserving resizing with white letterbox padding (`handwriting/data/transforms.py`)
- Decoded text prediction metric calculation (CER, WER, Exact Match in `handwriting/evaluation/metrics.py`)
- Disaggregated benchmark evaluation runner (`handwriting/evaluation/evaluate.py`)
- Memory-safe training engine with gradient accumulation (effective batch size 8), FP16, and gradient checkpointing
- Native 2,000-optimizer-step training executed under 4 GB VRAM limit (best checkpoint validation CER: 6.47%, exact match: 84.50%)
- Official held-out evaluation completed across 1,776 test samples (Combined: 67.68% exact match, 20.34% CER; Doctor BD: 91.83% exact match, 5.55% CER; RxHandBD: 53.36% exact match, 28.78% CER)
- Comprehensive test suite passing (73/73 tests)
- Full documentation in `docs/PHASE5_HANDWRITING_RESULTS.md`

### Phase 6 — Medical Reference Analysis
- Deterministic reference-range lookup system
- Low / Normal / High / Critical classification
- Reference-range data from verified medical sources
- Unit tests for classification logic

### Phase 7 — ML Risk Models
- Dataset acquisition (public medical datasets)
- Data preprocessing and feature engineering
- Model training: Diabetes, Heart Disease, Kidney Disease
- Model evaluation and validation
- Model serialization and inference API

### Phase 8 — Generative AI Integration
- Claude API integration
- Prompt engineering for medical explanations
- Simple-language explanation generation
- Safety guardrails and disclaimer injection
- Multilingual output: English, Hindi, Marathi, Gujarati

### Phase 9 — Flutter Mobile App
- Flutter project initialization
- Camera capture and PDF upload UI
- API integration with backend
- User verification screen for extracted data
- Health dashboard with risk indicators
- Report history and downloadable summaries
- Multilingual UI support

### Phase 10 — Integration & Testing
- End-to-end pipeline integration
- Comprehensive testing (unit, integration, UI)
- Performance optimization
- Error handling and edge cases
- User acceptance testing

### Phase 11 — Documentation & Deployment
- Complete documentation
- Deployment configuration
- Demo preparation
- Final project report

---

## 10. Disclaimer

> **MedIntel AI is an academic project. It is NOT a certified medical device or diagnostic tool. All outputs are for educational and informational purposes only. Users must consult qualified healthcare professionals for medical decisions.**
