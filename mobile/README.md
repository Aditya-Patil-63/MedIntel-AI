# Mobile App (Flutter)

Flutter mobile client (`medintel_mobile`) for MedIntel AI.

## Status

**Phase 9 — Mobile Application Development** (Step 2 Complete)

- Flutter SDK: 3.47.3 stable / Dart 3.13.3
- Layered feature-oriented architecture (`core/`, `models/`, `services/`, `repositories/`, `state/`, `screens/`, `widgets/`)
- Strongly typed Dart domain models mirroring all 10 FastAPI backend schemas
- Typed `Dio` API client supporting timeouts, multipart document extraction, and error unwrapping
- BLoC/Cubit state management enforcing mandatory human-in-the-loop verification gate
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
