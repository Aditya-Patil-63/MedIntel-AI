# Phase 9: Mobile Application Architecture & Integration Guide

> **MedIntel AI — Phase 9: Flutter Mobile Application**
> Document Version: 1.2
> Status: Phase 9 Complete
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
│   │   ├── genai/
│   │   │   ├── genai_explain_request.dart
│   │   │   ├── genai_explain_response.dart
│   │   │   └── genai_status_response.dart
│   │   └── analysis/
│   │       └── verified_snapshot.dart     # Immutable snapshot of confirmed clinical measurements
│   │
│   ├── services/
│   │   ├── api_service.dart               # Typed interface & implementation of 10 endpoints
│   │   └── feature_mapper.dart            # Pure deterministic mapping with strict null preservation
│   │
│   ├── repositories/
│   │   └── medical_repository.dart        # High-level domain actions & safety enforcement
│   │
│   ├── state/                             # BLoC / Cubit State Management
│   │   ├── document/                      # DocumentCubit & DocumentState
│   │   ├── verification/                  # VerificationCubit & VerificationState
│   │   ├── analysis/                      # AnalysisCubit & AnalysisState
│   │   └── history/                       # HistoryCubit & HistoryState
│   │
│   ├── widgets/                           # Reusable UI components
│   │   ├── disclaimer_banner.dart         # Prominent non-diagnostic warning banner
│   │   ├── status_card.dart               # Subsystem health chip
│   │   ├── measurement_edit_dialog.dart   # Interactive edit/add modal
│   │   ├── verification_status_chip.dart  # Verification badge (Unverified, Confirmed, Corrected)
│   │   ├── reference_findings_card.dart   # Phase 6 deterministic laboratory interval card
│   │   ├── ml_risk_card.dart              # Phase 7 risk probability & missing-feature card
│   │   └── genai_explanation_card.dart    # Phase 8 educational explanation & multilingual selector
│   │
│   └── screens/                           # App views
│       ├── home/home_screen.dart          # Main dashboard with status overview & navigation
│       ├── upload/upload_screen.dart      # PDF & image file picker
│       ├── verification/verification_screen.dart # Confirmation gate UI
│       ├── results/results_screen.dart    # Comprehensive 5-section results dashboard
│       └── history/history_screen.dart    # Report history placeholder
│
└── test/
    ├── models_test.dart                   # Serialization / deserialization tests
    ├── api_service_test.dart              # Error mapping & endpoint formatting tests
    ├── cubits_test.dart                   # Document & Verification Cubit lifecycle tests
    ├── feature_mapper_test.dart           # Pure feature extraction & null preservation tests
    ├── analysis_cubit_test.dart           # Multi-stage analysis orchestration & fallback tests
    ├── results_dashboard_test.dart        # Results screen component rendering tests
    └── widget_test.dart                   # App shell smoke test
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
- **Unit & Widget Tests**: 66 automated tests pass in `mobile/test/`:
  - `models_test.dart`: Serialization and deserialization of all 10 endpoint request/response models.
  - `api_service_test.dart`: Dio error unwrapping, JSON serialization, and endpoint routing.
  - `cubits_test.dart`: Document & Verification Cubit lifecycle, verification gate confirmation/invalidation, and mandatory verification guard checks.
  - `feature_mapper_test.dart`: Pure mapping logic, demographic conversion (`M`=1.0, `F`=0.0), alias resolution, and strict `null` preservation without client imputation.
  - `analysis_cubit_test.dart`: Multi-stage pipeline orchestration, unverified rejection, parallel execution, partial error isolation, HTTP 503 fallback, and independent language switching.
  - `results_dashboard_test.dart`: Component rendering of reference interval badges, ML risk probabilities, `INSUFFICIENT_FEATURES` missing data cards, and GenAI explanation cards.
  - `history_cubit_test.dart`: Local session history management, newest-first sorting, deduplication, immutable list wrapping, and serialization roundtrips.
  - `e2e_flow_test.dart`: End-to-end user workflow from document upload through verification, analysis, local history save, inspection, and "Start New Analysis" state reset.
  - `widget_test.dart`: App shell smoke test, upload screen constraints, verification review UI, and results dashboard.
- **Backend Integrity**: `pytest` confirms all 259 backend tests pass with 0 regressions.

---

## 9. Phase 9 Step 3: Document Ingestion, Extraction, Parsing & Verification UI

### 9.1 Implementation Highlights
- **Document Ingestion & File Validation**:
  - `DocumentCubit` validates files before upload: allowed extensions (`.pdf`, `.png`, `.jpg`, `.jpeg`), size cap (10 MB), and non-zero byte check.
  - Granular state machine: `DocumentInitial`, `DocumentSelecting`, `DocumentValidating`, `DocumentValidationFailed`, `DocumentUploading`, `DocumentExtracting`, `DocumentExtracted`, and `DocumentError` with retry support.
- **Multipart Document Extraction**:
  - Direct integration with `POST /api/v1/extract` via Dio multipart `FormData`.
  - Content-Type header is left unset on Dio defaults, allowing boundary generation per request.
- **Automatic Reference Parsing**:
  - Extracted text is automatically passed to `POST /api/v1/reference/parse-and-analyze` with `is_user_verified = false`.
  - Parsed measurements initialize with `VerificationItemStatus.unverified` and `MeasurementOrigin.extracted`.
- **Human-in-the-Loop Medical Verification UI**:
  - `VerificationScreen` presents an interactive review table:
    - Summary status counters: Total items, Unverified, Confirmed, Corrected.
    - Patient context input: Age (0–130) and Sex (`M`, `F`, `unspecified`).
    - Accessible verification badges with distinct colors, labels, and icons.
    - Editable fields: Test name, numerical value, and unit.
    - Ability to add missing measurements (`MeasurementOrigin.manual`) or remove spurious detections.
- **Mandatory Confirmation Gate**:
  - Any edit, addition, deletion, or demographic update instantly invalidates verification (`isVerified = false`).
  - Tapping "Confirm & Analyze" validates all measurements (non-empty name, non-null value, realistic age), promotes unverified items to `confirmed` (preserving `corrected`), and sets `isVerified = true`.

---

## 10. Phase 9 Step 4: Analysis Results, ML Risk Assessment & GenAI Explanation

### 10.1 Architecture & Pipeline Flow
The confirmed clinical measurements from Step 3 feed directly into a multi-stage analysis pipeline:

```
Verified Measurement Snapshot (Immutable)
        │
        ├──► POST /api/v1/reference/analyze (is_user_verified=true, report_id=null, persist=false)
        │
        ├──► POST /api/v1/ml/diabetes-risk (is_user_verified=true)
        ├──► POST /api/v1/ml/heart-risk (is_user_verified=true)
        └──► POST /api/v1/ml/kidney-risk (is_user_verified=true)
        │
        ▼ (Aggregate Deterministic Findings & Valid ML Risks)
        │
        └──► POST /api/v1/genai/explain (is_user_verified=true, language='en'|'hi'|'mr'|'gu')
        │
        ▼
Results Dashboard (5 Visual Sections + Multilingual Switcher)
```

### 10.2 Core Components
1. **`VerifiedSnapshot` (`models/analysis/verified_snapshot.dart`)**:
   - An immutable snapshot capturing confirmed measurements and patient demographics.
   - Enforces an unmodifiable list of measurements to prevent race conditions during downstream processing.

2. **`FeatureMapper` (`services/feature_mapper.dart`)**:
   - Pure, deterministic mapping utility converting snapshot items to typed backend request bodies.
   - Converts patient context demographics (`sex`: `M` -> 1.0, `F` -> 0.0; `age` -> float).
   - Maps known aliases for diabetes (glucose, fasting blood sugar, fbs), heart disease (cholesterol, resting bp, oldpeak, thalach), and kidney disease (serum creatinine, blood urea, hemoglobin).
   - **Strict Null Preservation**: Missing features strictly remain `null`. No client-side defaults, mean imputation, or synthetic scaling are performed in Flutter.

3. **`AnalysisCubit` & `AnalysisState` (`state/analysis/`)**:
   - **Verification Gate Enforcement**: Rejects unverified snapshots immediately (`isVerified == false`), transitioning to `AnalysisStatus.failure` with a client safeguard error.
   - **Parallel Stage Execution**: Executes reference range evaluation and the 3 ML risk models concurrently via `Future.wait`.
   - **Partial Error Isolation**: Individual subsystem errors (e.g. timeout on one ML endpoint) are caught individually and do not destroy other successful results.
   - **Informative ML Card Rendering**: When an ML endpoint returns `INSUFFICIENT_FEATURES`, the model's `missing_features` and required feature counts are displayed cleanly; it is never misrepresented as low risk.
   - **GenAI Explanation Orchestration**: Succeeded ML risks (`status == 'OK'` with non-null probability) and evaluated reference findings are passed to `POST /api/v1/genai/explain`.
   - **Graceful GenAI Degradation**: Transient HTTP 429 (rate limit), 503 (unavailable), and 504 (timeout) errors preserve all reference and ML results, displaying an educational fallback card with a "Retry AI Explanation" CTA.
   - **Independent Multilingual Switching**: Tapping the language dropdown (`English`, `Hindi`, `Marathi`, `Gujarati`) re-queries only the GenAI explanation endpoint without re-executing reference analysis or ML models.
   - **State Invalidation**: Editing any measurement on the verification screen calls `AnalysisCubit.invalidate()`, purging stale analysis state.

4. **Results Dashboard (`screens/results/results_screen.dart`)**:
   - **Section 1**: Sticky non-diagnostic medical disclaimer banner.
   - **Section 2**: Verified snapshot summary card displaying confirmed test count, patient age, and sex.
   - **Section 3**: `ReferenceFindingsCard` rendering deterministic laboratory findings with color-coded classification chips (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`) and normal reference intervals.
   - **Section 4**: Three `MLRiskCard` components displaying statistical risk probabilities with color progress bars (`LOW`, `MODERATE`, `ELEVATED`) or informative missing parameter lists for `INSUFFICIENT_FEATURES`.
   - **Section 5**: `GenAIExplanationCard` with language selector dropdown, plain-language summary, key test findings, follow-up guidance, recommended questions for the physician, and retry action.
   - **Persistent Footer**: Mandatory disclaimer emphasizing non-diagnostic educational purpose.

---

## 11. Phase 9 Step 5: Final Integration, Session History & End-to-End Validation

### 11.1 Completed End-to-End Clinical Flow
The complete Flutter application workflow integrates all 4 engineering phases into a seamless, deterministic, and safe user journey:

```
[Document Selection]
       │ (.pdf, .png, .jpg, .jpeg | <=10 MB | non-empty)
       ▼
[Multipart Extraction] ──► POST /api/v1/extract (Tesseract / EasyOCR / pdfplumber)
       │
       ▼
[Reference Parsing]    ──► POST /api/v1/reference/parse-and-analyze (is_user_verified=false)
       │
       ▼
┌────────────────────────────────────────────────────────┐
│              MANDATORY VERIFICATION GATE               │
│  User reviews, corrects, adds, or deletes values.      │
│  Edits invalidate confirmation (`isVerified = false`). │
│  User taps "Confirm & Analyze" (`isVerified = true`).  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
              [Immutable Verified Snapshot]
              (List.unmodifiable clinical items)
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
[Reference Batch]    [ML Diabetes]        [ML CKD]
POST /reference/analyze  POST /ml/diabetes   POST /ml/kidney
                           │
                           ▼
                     [ML Heart]
                     POST /ml/heart
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │ Aggregated Findings & Valid Risks
                           ▼
                 [GenAI Multilingual]
                 POST /genai/explain (en, hi, mr, gu)
                           │
                           ▼
                  [Results Dashboard]
           ├── Save to Session History
           └── Start New Analysis
```

### 11.2 History Architecture & In-Memory Session Storage
- **Backend Architectural Reality**: The FastAPI backend contains SQLAlchemy ORM persistence models (`reports`, `test_results`, `predictions`, `summaries`) with optional parameters (`report_id`, `persist: bool`), but does NOT expose any history-read endpoints (`GET /api/v1/history` or `GET /api/v1/reports`), nor does it provide user authentication or session management APIs.
- **Mobile Session Store**: In strict adherence to project safety rules prohibiting unauthorized backend rewrites, History is implemented as a strongly typed, in-memory local session store in `HistoryCubit`.
- **Scope & Limitations**:
  - History records are stored in memory for the duration of the active app session.
  - History is strictly mobile-local; the app never falsely claims cloud synchronization or server persistence.
  - No database bloat, no third-party native storage dependencies, and zero risk of cross-patient data leakage.
- **History Immutability**:
  - The `AnalysisHistoryItem` model represents an unmodifiable snapshot of the completed analysis.
  - Contains immutable copies of verified measurements, deterministic reference classifications, ML risk probabilities, and educational GenAI summaries.
  - Lists are wrapped in `List.unmodifiable` to ensure that subsequent edits on the verification screen or starting new analyses never mutate past records.
- **Zero Medical Computation on History Inspection**:
  - Opening `HistoryScreen` or `HistoryDetailScreen` triggers zero network calls, zero ML inference, zero reference evaluations, and zero GenAI queries.
  - Historical records are strictly read-only snapshots.

### 11.3 "Start New Analysis" Workflow
- Tapping "Start New Analysis" on the results screen cleanly resets active state:
  1. `AnalysisCubit.reset()` clears active analysis, reference findings, ML predictions, and GenAI explanations.
  2. `DocumentCubit.reset()` clears uploaded files, extraction results, and progress states.
  3. `VerificationCubit.reset()` clears editable measurements and resets the verification gate to unverified.
  4. Pops back to the root `HomeScreen`, ensuring no stale results can contaminate subsequent analyses.
  5. Saved historical records in `HistoryCubit` remain completely untouched.

### 11.4 Verification Safety & Guard Invariants
1. **Authoritative Backend Verification**: The FastAPI backend remains the authoritative gate. All analysis endpoints reject unverified data with HTTP 400.
2. **Client-Side Safeguard**: `AnalysisCubit.runFullAnalysis` rejects unverified snapshots before issuing any network requests.
3. **Pure Feature Mapping**: `FeatureMapper` performs pure, deterministic conversions and strictly preserves `null` for missing features. No synthetic data, no mean imputation, and no client-side clinical calculations.
4. **Resilience to Subsystem Failure**: Isolated error containment preserves valid findings if an individual ML model returns `INSUFFICIENT_FEATURES` or if GenAI experiences transient rate limiting (HTTP 429).
5. **Non-Diagnostic Educational Disclaimers**: Sticky non-diagnostic banners are rendered on every screen without exception.
