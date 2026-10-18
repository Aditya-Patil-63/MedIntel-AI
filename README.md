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
| 14 | Secure user authentication & password hashing (PBKDF2-HMAC-SHA256) |
| 15 | Strict user-partitioned report isolation (private SQLite data per user) |
| 16 | Modern healthcare mobile design system & connection settings |

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
| 7     | ML Risk Models                    | ✅ Complete     |
| 8     | Generative AI Integration         | ✅ Complete     |
| 9     | Flutter Mobile App                | ✅ Complete     |
| 10    | Integration & Testing             | ✅ Complete     |
| 11    | Documentation & Deployment        | ✅ Complete     |
| Post  | Mobile UI/UX Redesign & User Authentication | ✅ Complete (19 Oct 2026) |

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

**Current Status: All Phases Complete (Phases 1–11 ✅) — Production & Defense Ready**

- **Packaging, Deployment & Capstone Documentation (`Dockerfile`, `docker-compose.yml`, `docs/`)**:
  - Phase 11 Complete: Multi-stage Debian slim `Dockerfile` with bundled Tesseract OCR, OpenCV, and FastAPI Uvicorn engine, orchestrated with `docker-compose.yml` and persistent volume mounts.
  - Complete operations and deployment guide in [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md).
  - Interactive end-to-end clinical pipeline demo runner (`scripts/run_demo.py`) with support for interactive and automated CLI walk-throughs across scenarios A (Normal), B (Elevated Risk), and C (Critical Alert) in English, Hindi, Marathi, and Gujarati.
  - Comprehensive academic & engineering final capstone report in [docs/CAPSTONE_PROJECT_REPORT.md](docs/CAPSTONE_PROJECT_REPORT.md).
  - End-user patient & clinician application manual in [docs/USER_MANUAL.md](docs/USER_MANUAL.md).
  - 20-slide presentation deck outline, speaker notes, and committee defense guide in [docs/PRESENTATION_DECK.md](docs/PRESENTATION_DECK.md).

- **System-Wide Integration & Resilience Testing (`docs/PHASE10_INTEGRATION_AND_TESTING.md`, `docs/PHASE10_PERFORMANCE_AND_CONCURRENCY_REPORT.md`)**:
  - Phase 10 Complete: Unified end-to-end clinical workflow verified across document ingestion (PDF/OCR), deterministic reference parsing, verification safety gating, parallel ML risk prediction, multilingual GenAI explanations (EN, HI, MR, GU), and SQLite persistence.
  - 373 total passing tests across backend (307) and Flutter mobile (66) with zero failures.
  - Automated cross-subsystem test runner: `scripts/run_cross_subsystem_tests.py`.
  - Comprehensive resilience test suite (33 tests) verifying corrupted documents, ReDoS immunity under 120k characters, 429/504/503 provider fallbacks, prompt injection defenses, and transactional rollbacks.
  - Empirical performance and concurrency audit: Sub-second response times (20–130 ms), in-memory singleton ML model caching, 0.0% error rate across 700 concurrent requests, and throughput up to 527 RPS.

- **Flutter Mobile Client (`mobile/`, `docs/PHASE9_MOBILE_ARCHITECTURE.md`)**:
  - Phase 9 Complete: Modern cross-platform client with BLoC/Cubit state management (`UploadCubit`, `VerificationCubit`, `AnalysisCubit`, `HistoryCubit`).
  - Native document ingestion via camera and file picker with client-side format and 10 MB size limits.
  - Interactive User Verification Gate allowing review, corrections, and additions before clinical analysis.
  - Parallel analysis dispatch orchestrating reference engine, ML risk predictions, and multilingual GenAI explanations.
  - Snapshot-based in-memory session history with search, sorting, and deep inspection.
  - Android API 36 compilation compatibility verified on physical device.
  - 66 tests passing across 9 test suites (`flutter test`).

- **Generative AI Explanation & Translation (`docs/PHASE8_GENAI_ARCHITECTURE.md`, `backend/app/schemas/genai.py`, `backend/app/services/genai_service.py`, `backend/app/api/genai.py`)**:
  - Phase 8 Complete: Production Gemini provider and deterministic offline mock provider integrated.
  - Pydantic contracts enforcing strict non-diagnostic, non-prescriptive communication.
  - Service orchestration layer (`GenAIExplanationService`) managing provider factory, user verification safety gate (`is_user_verified`), multilingual translation dispatch, and SQLite `Summary` persistence.
  - FastAPI endpoints: `POST /api/v1/genai/explain` and `GET /api/v1/genai/status`.
  - Multilingual translation support across English (`en`), Hindi (`hi`), Marathi (`mr`), and Gujarati (`gu`) strictly preserving numerical and clinical invariance.
  - 35 Phase 8 tests passing.

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

---

## 🚀 Latest Development Progress — 19 October 2026

### 1. Complete Mobile UI/UX Redesign
- **Premium Healthcare Aesthetic**: Replaced the developer prototype with a calm, trustworthy medical design system utilizing Deep Teal (`#006D77`), Mint accents (`#83C5BE`), crisp white cards (`#FFFFFF`), and soft background slate (`#F8F9FA`).
- **User-Centric Navigation**: Implemented a responsive bottom navigation bar (`Dashboard`, `Analyze`, `History`, `Settings`) structured for ordinary patients and non-technical users.
- **Home Dashboard**: Replaced technical banners with an intuitive hero card (*"Analyze a Medical Report"*), a clear 3-step explainer (*"How MedIntel AI Works"*), and quick clinical action cards.
- **Workflow & Layout Consistency**: Redesigned Upload, Verification Gate, Analysis Results, and History screens with zero RenderFlex overflows across both compact and large Android viewports.

### 2. User Authentication & Security System
- **App Entry Gate**: Unauthenticated users are immediately presented with the clean **MedIntel AI Sign In** screen on startup.
- **Account Registration**: Added a dedicated **Create Account** screen with real-time form validation (email format, matching passwords, minimum length).
- **Cryptographic Password Protection**:
  - Passwords hashed with `PBKDF2-HMAC-SHA256` using 100,000 iterations and a unique 16-byte cryptographically random salt per user.
  - Zero plaintext passwords stored in the database.
- **Session Management**: HMAC-SHA256 signed bearer tokens with timestamped expiration.
- **State Machine**: Powered by `AuthCubit` (`Unauthenticated`, `AuthLoading`, `Authenticated`, `AuthError`).

### 3. User-Partitioned SQLite Database Isolation
- **Strict Data Partitioning**: All report storage (`POST /api/v1/reports`, `GET /api/v1/reports`, `DELETE /api/v1/reports/{id}`) is strictly bound to `current_user.id`.
- **Privacy Guarantees**: A user can never view, mutate, or delete another user's clinical reports.
- **Multi-Tenant Protection**: Attempts to access foreign report IDs return HTTP 404.
- **Clean Session Teardown**: Signing out wipes the local authentication state and cleans cached history to prevent cross-account data leakage on shared mobile devices.

### 4. Settings & Network Connectivity Hub
- **User Profile Card**: Displays user avatar, full name, email, and a verified green status badge: *"User Isolation: Reports are private to this account"*.
- **Flexible Network Configuration**:
  - Quick presets: **Wi-Fi LAN (Auto)**, **USB Cable (Phone)**, and **Android Emulator**.
  - Custom Base URL input with live ping/health check button.
  - Subsystem diagnostic indicators for backend health and API responsiveness.

---

## 🛠️ Setup & Installation Guide

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.12)
- **Flutter SDK**: 3.27+ with Android SDK (API 36 / 35 supported)
- **ADB**: Android Debug Bridge for physical device and emulator communication

### 1. FastAPI Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server on port 8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The backend API documentation is accessible at `http://localhost:8000/docs`.

### 2. Flutter Mobile Setup
```bash
# Navigate to mobile directory
cd mobile

# Fetch Flutter dependencies
flutter pub get

# Run static analysis
flutter analyze

# Run unit and widget tests
flutter test

# Launch mobile application on connected device / emulator
flutter run
```

### 3. Connecting a Physical Android Phone or Emulator
To allow the mobile app to communicate with your local FastAPI server:

#### Option A: USB Cable Connection (Recommended for Physical Devices)
1. Connect your phone via USB with **USB Debugging** enabled.
2. In terminal, run reverse port forwarding:
   ```powershell
   adb reverse tcp:8000 tcp:8000
   ```
3. In the MedIntel AI app, tap the **Settings** gear, select **USB Cable (Phone)** (`http://127.0.0.1:8000`), and tap **Test & Save Connection**.

#### Option B: Wi-Fi Local Area Network (Same Wi-Fi)
1. Find your computer's local IP address (e.g., `ipconfig` on Windows -> `192.168.x.x` or `10.x.x.x`).
2. Ensure both computer and phone are connected to the same Wi-Fi router.
3. In the MedIntel AI app, tap **Settings**, select or enter `http://<YOUR_PC_IP>:8000`, and tap **Test & Save Connection**.

#### Option C: Android Emulator
- Select **Android Emulator** (`http://10.0.2.2:8000`), which bridges directly to `localhost:8000` on the host machine.

---

## 🧪 Verified Test Suite & Device Validation

### Automated Test Coverage
- **Flutter Mobile Analysis**: `flutter analyze` -> **0 issues found** across all Dart files.
- **Flutter Test Suite**: `flutter test` -> **75 tests passed, 0 failures** (including AuthCubit, HistoryCubit, UploadCubit, VerificationCubit, E2E workflow, and UI widgets).
- **Backend Test Suite**: `pytest` -> **33 tests passed, 0 failures** (verifying registration, password verification, HMAC authentication, duplicate rejection, and multi-user report isolation).

### Physical & Virtual Device Validation
- **Physical Android Device (Realme RMX3771)**: Verified APK build, streamed ADB installation, startup into the Sign In screen, responsive touch handling, and backend connectivity via reverse port forwarding.
- **Android Virtual Device (Emulator API 36)**: Verified end-to-end user registration, login, dashboard rendering, settings navigation, and session sign-out.

---

## 📌 Known Limitations & Ongoing Work
- **Handwritten Prescription Integration on Mobile**: The backend TrOCR deep learning model requires GPU/CUDA acceleration for sub-second response times; mobile currently routes primarily to digital PDF parsing and printed OCR.
- **Cloud Database Synchronization**: Current user and report persistence uses local SQLite. Transition to PostgreSQL/MySQL is architected for future multi-region cloud deployment.
- **Biometric Authentication**: Fingerprint and Face Unlock biometric shortcuts will be integrated in a subsequent release to augment password login.