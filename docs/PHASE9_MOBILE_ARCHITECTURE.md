# Phase 9: Mobile Application Architecture & Integration Guide

> **MedIntel AI — Phase 9: Flutter Mobile Application**  
> Document Version: 1.0  
> Status: Phase 9 Step 2 Complete  
> Target Platform: Android (Primary), Cross-Platform ready  

---

## 1. Architectural Overview

The MedIntel AI Mobile Client (`medintel_mobile`) provides a patient- and clinician-facing interface designed with a **layered, feature-oriented architecture**. 

```
┌───────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                         │
│  ├── Screens: Home, Upload, Verification Gate, Results, History  │
│  ├── Widgets: DisclaimerBanner, StatusCard                        │
│  └── Theme: AppColors, AppTheme (Material 3)                      │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │ Blocs / Cubits
┌─────────────────────────────────▼─────────────────────────────────┐
│                     State Management Layer                        │
│  ├── DocumentCubit: Handles report file selection & upload        │
│  ├── VerificationCubit: User review & confirmation safety gate    │
│  ├── AnalysisCubit: Orchestrates reference, ML risk & GenAI       │
│  └── HistoryCubit: Stored reports & summary cache                 │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │
┌─────────────────────────────────▼─────────────────────────────────┐
│                       Domain / Data Layer                         │
│  ├── MedicalRepository: Domain orchestration & client safeguards  │
│  ├── ApiService: Typed contract covering all 10 FastAPI endpoints │
│  ├── Models: Extraction, Reference, ML Risk, GenAI (mirroring API)│
│  └── Network: DioClient with error unwrapping & custom timeouts   │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │ HTTP / REST (Multipart & JSON)
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Port 8000)                      │
│     OCR Pipeline | Reference Engine | ML Models | GenAI Provider   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & Package Structure

The mobile project resides directly within `mobile/` without redundant nesting:

```
mobile/
├── lib/
│   ├── main.dart                      # App entrypoint (WidgetsFlutterBinding, runApp)
│   ├── app.dart                       # MedIntelApp with MultiBlocProvider & Theme
│   │
│   ├── core/                          # Cross-cutting foundational utilities
│   │   ├── constants/
│   │   │   ├── api_constants.dart     # Base URL (--dart-define) & endpoint routes
│   │   │   └── app_constants.dart     # Brand strings and mandatory disclaimers
│   │   ├── errors/
│   │   │   ├── api_exception.dart     # Structured hierarchy: Network, 422, 503, 500
│   │   │   └── failure.dart           # Presentation-level failure representations
│   │   ├── network/
│   │   │   └── dio_client.dart        # Configured Dio instance with timeouts & logging
│   │   └── theme/
│   │       ├── app_colors.dart        # Medical semantic colors (Low, Normal, High, Critical)
│   │       └── app_theme.dart         # Material 3 light theme configuration
│   │
│   ├── models/                        # Strongly typed Dart models mirroring Pydantic
│   │   ├── common/
│   │   │   └── enums.dart             # SourceType, AnalyteClassification, RiskBand, etc.
│   │   ├── extraction/
│   │   │   ├── page_extraction.dart
│   │   │   └── document_extraction_result.dart
│   │   ├── reference/
│   │   │   ├── patient_context.dart
│   │   │   ├── measurement_input.dart
│   │   │   ├── reference_range_summary.dart
│   │   │   ├── analysis_result.dart
│   │   │   ├── batch_analysis.dart
│   │   │   └── parse_and_analyze.dart
│   │   ├── ml_risk/
│   │   │   ├── diabetes_risk_request.dart
│   │   │   ├── heart_disease_risk_request.dart
│   │   │   ├── kidney_disease_risk_request.dart
│   │   │   ├── risk_prediction_response.dart
│   │   │   └── ml_status_response.dart
│   │   └── genai/
│   │       ├── genai_explain_request.dart
│   │       ├── genai_explain_response.dart
│   │       └── genai_status_response.dart
│   │
│   ├── services/
│   │   └── api_service.dart           # Typed interface & implementation of 10 endpoints
│   │
│   ├── repositories/
│   │   └── medical_repository.dart    # High-level domain actions & safety enforcement
│   │
│   ├── state/                         # BLoC / Cubit State Management
│   │   ├── document/                  # DocumentCubit & DocumentState
│   │   ├── verification/              # VerificationCubit & VerificationState
│   │   ├── analysis/                  # AnalysisCubit & AnalysisState
│   │   └── history/                   # HistoryCubit & HistoryState
│   │
│   ├── widgets/                       # Reusable UI components
│   │   ├── disclaimer_banner.dart     # Prominent non-diagnostic warning banner
│   │   └── status_card.dart           # Subsystem health chip
│   │
│   └── screens/                       # App views
│       ├── home/home_screen.dart      # Main dashboard with status overview & navigation
│       ├── upload/upload_screen.dart  # PDF & image file picker
│       ├── verification/verification_screen.dart # Confirmation gate UI
│       ├── results/results_screen.dart # Reference & ML risk display
│       └── history/history_screen.dart # Report history placeholder
│
└── test/
    ├── models_test.dart               # Serialization / deserialization tests
    ├── api_service_test.dart          # Error mapping & endpoint formatting tests
    ├── cubits_test.dart               # State transitions & verification gate tests
    └── widget_test.dart               # App shell smoke test
```

---

## 3. Dependencies and Rationale

| Package | Version | Purpose |
|---------|---------|---------|
| `dio` | `^5.7.0` | Robust HTTP client supporting multipart file uploads, granular timeout handling, interceptors, and error mapping. |
| `flutter_bloc` | `^8.1.6` | Predictable, unidirectional state management decoupling business rules from presentation. |
| `equatable` | `^2.0.5` | Value equality for immutable state objects and request models without boilerplate. |
| `file_picker` | `^8.1.7` | Platform-native file selector for PDFs and images. |
| `bloc_test` | `^9.1.7` | (Dev) Specialized testing tools for verifying Cubit state transitions. |
| `mocktail` | `^1.0.4` | (Dev) Type-safe mocking for unit testing services and repositories. |

---

## 4. API Endpoints Mapping

The `ApiService` contract maps 1:1 to the 10 FastAPI endpoints:

| # | HTTP Method | Endpoint Route | Request Model | Response Model | Description |
|---|-------------|----------------|---------------|----------------|-------------|
| 1 | `GET` | `/health` | None | `Map<String, dynamic>` | FastAPI server heartbeat |
| 2 | `POST` | `/api/v1/extract` | `FormData` (`file`, `engine?`) | `DocumentExtractionResult` | OCR / text extraction |
| 3 | `POST` | `/api/v1/reference/parse-and-analyze` | `ParseAndAnalyzeRequest` | `ParseAndAnalyzeResponse` | Unstructured text parsing & classification |
| 4 | `POST` | `/api/v1/reference/analyze` | `BatchAnalysisRequest` | `BatchAnalysisResponse` | Deterministic reference range classification |
| 5 | `GET` | `/api/v1/ml/status` | None | `MLStatusResponse` | Health of trained ML models |
| 6 | `POST` | `/api/v1/ml/diabetes-risk` | `DiabetesRiskRequest` | `RiskPredictionResponse` | Pima Indians diabetes risk score |
| 7 | `POST` | `/api/v1/ml/heart-risk` | `HeartDiseaseRiskRequest` | `RiskPredictionResponse` | Cleveland heart disease risk score |
| 8 | `POST` | `/api/v1/ml/kidney-risk` | `KidneyDiseaseRiskRequest` | `RiskPredictionResponse` | UCI CKD kidney disease risk score |
| 9 | `GET` | `/api/v1/genai/status` | None | `GenAIStatusResponse` | GenAI provider status & mode |
| 10 | `POST` | `/api/v1/genai/explain` | `GenAIExplainRequest` | `GenAIExplainResponse` | Multilingual educational explanations |

---

## 5. End-to-End Clinical Flow & Verification Gate

The end-to-end data flow enforces a strict human-in-the-loop verification gate:

```
[Upload Document] 
      │
      ▼
[FastAPI Extraction] 
  (pdfplumber / Tesseract)
      │
      ▼
[Raw Extracted Values] (Unverified)
      │
      ▼
┌────────────────────────────────────────────────────────┐
│              MANDATORY VERIFICATION GATE               │
│                                                        │
│  User reviews extracted test names, values, units.     │
│  User modifies OCR mistakes if necessary.              │
│  User taps "Confirm & Verify".                         │
│  State transitions: is_user_verified = true.           │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    [Reference Analysis]          [ML Risk Estimation]
    (Deterministic ranges)        (Trained models)
             │                           │
             └─────────────┬─────────────┘
                           │ Verified Findings
                           ▼
               [GenAI Multilingual Explanation]
               (English, Hindi, Marathi, Gujarati)
                           │
                           ▼
                  [Results & History]
```

### Verification Gate Architecture
- **Client-Side Safeguard**: `VerificationCubit` holds values and sets `isVerified = false` upon loading or any user edit. `AnalysisCubit` and `MedicalRepository` throw a `VerificationRequiredException` if an analysis is requested with unverified values.
- **Backend Authoritative Gate**: The FastAPI endpoints (`/reference/analyze`, `/ml/*`, `/genai/explain`) independently check `is_user_verified`. If false or missing, the backend returns HTTP 400 with a safety hold. The mobile client never weakens or bypasses backend verification.

---

## 6. Development Base URL Configuration

The API base URL is configured at build or run time using Dart compile-time environment variables:

```bash
# Default (Android Emulator accessing host FastAPI server):
flutter run

# Custom local network (Physical Android device on same Wi-Fi):
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000

# Localhost (Desktop / Web development):
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

---

## 7. Security and Privacy Invariants

1. **Zero Client Secrets**: No Gemini API keys, LLM tokens, or database credentials reside in Flutter. All provider credentials live securely in `backend/.env`.
2. **No Local Medical Computation**: The mobile client performs zero reference range computations and zero ML inference locally. All clinical intelligence is centralized in FastAPI.
3. **Privacy-Preserving Logs**: `DioClient` logs sanitized request metadata only (endpoints, status codes, errors). Extracted patient text and document bytes are never printed to debug logs.
4. **Non-Diagnostic UI Disclaimers**: A sticky educational disclaimer is rendered prominently on every screen:
   > *"This is not a medical diagnosis. Please consult a qualified healthcare professional."*

---

## 8. Automated Verification Suite

- **Static Analysis**: `flutter analyze` passes with **0 errors and 0 warnings**.
- **Unit & Widget Tests**: 23 automated tests pass in `mobile/test/`:
  - `models_test.dart`: Serialization and deserialization of all 10 endpoint request/response models.
  - `api_service_test.dart`: Dio error unwrapping, JSON serialization, and endpoint routing.
  - `cubits_test.dart`: Extraction loading, verification confirmation, and mandatory verification guard checks.
  - `widget_test.dart`: App shell smoke test verifying title, disclaimer banner, and pipeline navigation tiles.
- **Backend Integrity**: `pytest` confirms all 259 backend tests pass with 0 regressions.
