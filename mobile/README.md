# Mobile App (Flutter)

Flutter mobile client (`medintel_mobile`) for MedIntel AI.

## Status

**Phase 9 — Mobile Application Development** (Step 4 Complete)

- Flutter SDK: 3.47.3 stable / Dart 3.13.3
- Layered feature-oriented architecture (`core/`, `models/`, `services/`, `repositories/`, `state/`, `screens/`, `widgets/`)
- Strongly typed Dart domain models mirroring all 10 FastAPI backend schemas
- Typed `Dio` API client supporting timeouts, multipart document extraction, and error unwrapping
- **Document Ingestion & File Validation**: PDF, PNG, JPG, JPEG formats strictly capped at 10 MB with 0-byte detection
- **Multipart Document Extraction**: Direct integration with `POST /api/v1/extract` via Dio multipart upload
- **Reference Parsing**: Unstructured extracted text parsed via `POST /api/v1/reference/parse-and-analyze` (`is_user_verified = false`)
- **Medical Verification UI**: Complete human-in-the-loop review interface with accessible status chips (`UNVERIFIED`, `CONFIRMED`, `CORRECTED`), item origin (`EXTRACTED`, `MANUAL`), and edit/add/delete actions
- **Patient Demographics**: Optional Age (0–130) and Sex (`M`, `F`, `unspecified`) input
- **Mandatory Confirmation Gate**: Strict client safeguard requiring explicit confirmation; any edit instantly invalidates verification
- **Immutable Verified Snapshot**: Unmodifiable capture of verified measurements and patient context
- **Pure Feature Mapper**: Deterministic extraction of ML features and reference bodies with strict `null` preservation (no client imputation)
- **Multi-Stage Analysis Pipeline**: Concurrent execution of deterministic reference evaluation (`POST /api/v1/reference/analyze`) and ML risk models (Diabetes, Heart Disease, Kidney Disease) with partial failure isolation
- **Informative ML Risk Cards**: Clean visualization of risk probabilities and bands, or explicit missing feature requirements when `INSUFFICIENT_FEATURES`
- **GenAI Clinical Explanation**: Orchestration of `POST /api/v1/genai/explain` with graceful HTTP 429/503/504 degradation and retry CTA
- **Independent Multilingual Switching**: On-demand language switching (`en`, `hi`, `mr`, `gu`) without re-running reference or ML analysis
- **Comprehensive Results Dashboard**: 5-section dashboard with sticky disclaimer, verification summary, laboratory reference cards, ML risk indicators, and AI explanation card
- App shell with Material 3 medical theme and persistent non-diagnostic educational disclaimer banner

## Running the Mobile App

### Prerequisites

- Flutter SDK (>= 3.13.3)
- Android SDK (or connected Android emulator / physical device)
- FastAPI backend running on port 8000:
  ```powershell
  cd ..\backend
  .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
  ```

### Run Commands

```powershell
# Default (Android emulator -> http://10.0.2.2:8000):
flutter run

# Custom base URL (physical device or LAN server):
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000

# Chrome / Web development:
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

### Running Tests and Static Analysis

```powershell
flutter analyze
flutter test
```

## Architecture Documentation

See [PHASE9_MOBILE_ARCHITECTURE.md](../docs/PHASE9_MOBILE_ARCHITECTURE.md) for full architectural specifications, security boundaries, and API integration details.
