# Mobile App (Flutter)

Flutter mobile client (`medintel_mobile`) for MedIntel AI.

## Status

**Phase 9 — Mobile Application Development** (COMPLETE)

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
- **Immutable Verified Snapshot**: Unmodifiable capture of verified measurements and patient context (`VerifiedSnapshot`)
- **Pure Feature Mapper**: Deterministic extraction of ML features and reference bodies with strict `null` preservation (zero client imputation)
- **Multi-Stage Analysis Pipeline**: Concurrent execution of deterministic reference evaluation (`POST /api/v1/reference/analyze`) and ML risk models (Diabetes, Heart Disease, Kidney Disease) with partial failure isolation
- **Informative ML Risk Cards**: Clean visualization of risk probabilities and bands, or explicit missing feature requirements when `INSUFFICIENT_FEATURES`
- **GenAI Clinical Explanation**: Orchestration of `POST /api/v1/genai/explain` with graceful HTTP 429/503/504 degradation and retry CTA
- **Independent Multilingual Switching**: On-demand language switching (`en`, `hi`, `mr`, `gu`) without re-running reference or ML analysis
- **Comprehensive Results Dashboard**: 5-section dashboard with sticky disclaimer, verification summary, laboratory reference cards, ML risk indicators, AI explanation card, and local session actions
- **Local Session History**: Strongly typed, immutable `AnalysisHistoryItem` snapshots saved in `HistoryCubit`; review past analyses in `HistoryScreen` and read-only `HistoryDetailScreen`
- **Start New Analysis**: Complete state reset of analysis, document, and verification cubits while preserving saved session history
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

### Run Commands & Networking Configuration

```powershell
# Default (Android emulator connecting to host machine -> http://10.0.2.2:8000):
flutter run

# Physical Android device on local Wi-Fi network:
# Replace 192.168.1.100 with your development PC's actual local IP address:
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000

# Desktop / Web development:
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

> **Android Device Networking Note**: When testing on a physical Android phone, ensure both the computer and phone are connected to the same Wi-Fi network, and that Windows Firewall permits inbound traffic on port 8000.

### Running Tests and Static Analysis

From the `mobile/` directory:

```powershell
# Run Flutter linter and analyzer (0 issues expected)
flutter analyze

# Run all 66 unit, widget, and integration tests
flutter test
```

From the repository root `D:\MedIntel AI`:

```powershell
# Run backend pytest suite (259 tests passing, 0 regressions)
.\backend\venv\Scripts\python.exe -m pytest -q
```

## History Behavior & Known Limitations

1. **In-Memory Session Storage**: The FastAPI backend currently does not provide `GET /api/v1/history`, `GET /api/v1/reports`, or user authentication endpoints. To respect strict architectural rules and avoid unauthorized backend refactoring, report history is implemented as an in-memory local session store in `HistoryCubit`.
2. **Session Lifespan**: History records remain available during the active app session. They are reset upon complete app restart.
3. **Immutability & Safety**: Historical items represent unmodifiable snapshots. Inspecting past reports in `HistoryDetailScreen` is strictly read-only and never makes network or medical API calls.
4. **Authoritative Backend Verification Gate**: The mobile client enforces an explicit verification check, but the FastAPI backend remains the authoritative gate. All analysis endpoints reject unverified data with HTTP 400.

## Mandatory Medical Disclaimer

> **This application handles medical data. It provides risk indicators and educational information only. It does NOT diagnose medical conditions, recommend treatments, or prescribe medications. All outputs are strictly for educational and informational purposes. Users must consult qualified healthcare professionals for all medical decisions.**

## Architecture Documentation

See [docs/PHASE9_MOBILE_ARCHITECTURE.md](../docs/PHASE9_MOBILE_ARCHITECTURE.md) for full architectural specifications, security boundaries, and API integration details.
