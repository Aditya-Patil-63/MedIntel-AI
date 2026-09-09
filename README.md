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
| 4     | PDF & OCR Pipeline                | ⬜ Not Started  |
| 5     | Handwriting Recognition           | ⬜ Not Started  |
| 6     | Medical Reference Analysis        | ⬜ Not Started  |
| 7     | ML Risk Models                    | ⬜ Not Started  |
| 8     | Generative AI Integration         | ⬜ Not Started  |
| 9     | Flutter Mobile App                | ⬜ Not Started  |
| 10    | Integration & Testing             | ⬜ Not Started  |
| 11    | Documentation & Deployment        | ⬜ Not Started  |

See [PROJECT_RULES.md](PROJECT_RULES.md) for detailed phase descriptions and all project rules.

---

## Datasets Selected (Phase 3)

The following exact three public/academic datasets have been selected and verified for the project's risk-prediction tasks:

1. **Diabetes:** Pima Indians Diabetes Database (NIDDK, accessible via Kaggle / OpenML)
2. **Heart Disease:** UCI Heart Disease Dataset — Cleveland processed subset (DOI: `10.24432/C52P4X`)
3. **Kidney Disease:** UCI Chronic Kidney Disease Dataset (Apollo Hospitals, DOI: `10.24432/C5G020`)

*Important:* Actual dataset files are strictly kept outside the Git repository. Documentation, metadata, and reproducible preparation scripts are located in `ml/data/` and `ml/scripts/`.

---

## Safety Notice

> **MedIntel AI is an academic project. It is NOT a certified medical device or diagnostic tool. All outputs are for educational and informational purposes only. Users must consult qualified healthcare professionals for medical decisions.**

---

## Project Status

**Current Phase: 3 — Data Collection & Preparation**

Selected and verified three clinical datasets (Pima Diabetes, UCI Cleveland Heart Disease, UCI Chronic Kidney Disease). Created external dataset storage architecture (`MEDINTEL_DATA_DIR`), dataset metadata, source documentation with DOIs, data quality report, inspection scripts, reproducible preparation scripts, and validation tests. ML models have NOT been trained yet (deferred to the ML Model Development phase).