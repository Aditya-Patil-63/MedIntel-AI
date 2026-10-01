# MedIntel AI — Deployment & Operations Guide

> **Phase 11: Documentation, Packaging & Final Deployment**  
> Comprehensive operations, containerization, and deployment guide for MedIntel AI.

---

## 1. System Overview & Architecture

MedIntel AI is composed of two primary deployment artifacts:

1. **FastAPI Backend Service (`backend/`)**:
   - Python 3.10+ / 3.12 microservice hosting REST endpoints.
   - Bundles the deterministic clinical reference engine (`reference/`), ML risk model inference (`ml/`), OCR & document parsing pipelines (`ocr/`, `handwriting/`), Generative AI explanation service (`backend/app/services/genai_service.py`), and SQLite persistence (`database/`).
   - Packaged as a lightweight multi-stage Docker container (`Dockerfile`).

2. **Flutter Cross-Platform Mobile Application (`mobile/`)**:
   - Client application running on Android (API 36+ compileSdk, API 21+ minSdk) and iOS / Web.
   - Communicates with the FastAPI backend over secure REST/HTTPS channels.

```
   ┌────────────────────────────────────────────────────────┐
   │                  Flutter Mobile Client                 │
   │           (Android / iOS / Desktop Client)             │
   └───────────────────────────┬────────────────────────────┘
                               │ HTTP / JSON API
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │             MedIntel AI Backend Container              │
   │               (FastAPI / Uvicorn Server)               │
   │                                                        │
   │   ┌───────────────┐  ┌───────────────┐  ┌──────────┐   │
   │   │  OCR Pipeline │  │  Ref Engine   │  │ ML Risk  │   │
   │   │ (Tesseract/DL)│  │ (Deterministic│  │ Models   │   │
   │   └───────────────┘  └───────────────┘  └──────────┘   │
   │   ┌───────────────┐  ┌───────────────┐                 │
   │   │ GenAI Service │  │ SQLite Store  │                 │
   │   │ (Gemini/Mock) │  │ (medintel.db) │                 │
   │   └───────────────┘  └───────────────┘                 │
   └────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites & Environment Requirements

### 2.1 Hardware Requirements

| Component | Minimum Specification | Recommended Specification |
|:---|:---|:---|
| **CPU** | 2 cores (x86_64 or ARM64) | 4+ cores |
| **RAM** | 4 GB | 8 GB+ (16 GB for deep learning model training) |
| **Disk Space** | 5 GB available disk | 20 GB available disk |
| **GPU** | Optional (CPU inference supported) | NVIDIA CUDA GPU (for TrOCR fine-tuning) |

### 2.2 Software Prerequisites

- **Docker**: Version 24.0+ and **Docker Compose** v2.20+ (for containerized deployment).
- **Python**: Version 3.10, 3.11, or 3.12 (for bare-metal/local Python deployment).
- **Tesseract OCR**: Version 5.x with English and OSD language models.
- **Flutter SDK**: Version 3.24+ (Dart 3.5+) for mobile client builds.
- **Android SDK**: Build tools 34.0.0+, compileSdk 36.

---

## 3. Containerized Deployment (Docker & Docker Compose)

The recommended production deployment method is via Docker Compose.

### 3.1 Directory Layout & Configuration Files

The repository root includes:
- `Dockerfile`: Multi-stage Debian slim container with system libraries (Tesseract OCR, OpenCV runtime `libgl1`, `libglib2.0-0`, `curl`).
- `docker-compose.yml`: Multi-container orchestration, persistent volume mounts, and automated health checks.
- `.dockerignore`: Excludes caches, temporary files, Git history, and client code from build context.

### 3.2 Environment Configuration

Create an environment configuration file `.env` in the repository root (or copy from `.env.example`):

```bash
# Server Configuration
MEDINTEL_ENV=production
PORT=8000

# Generative AI Configuration
# Set to 'gemini' for production live calls, or 'mock' for offline deterministic operation
GENAI_PROVIDER=mock
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# OCR Configuration
DEFAULT_OCR_ENGINE=tesseract

# Database & Storage
DATABASE_URL=sqlite:////app/database/medintel.db
MEDINTEL_ML_MODELS_DIR=/app/ml/models
MAX_UPLOAD_SIZE_BYTES=10485760
```

### 3.3 Building and Starting the Container

To build and run the MedIntel AI backend service in detached mode:

```bash
# 1. Build the Docker container image
docker compose build

# 2. Start the service
docker compose up -d

# 3. View running container status
docker compose ps

# 4. View real-time container logs
docker compose logs -f backend
```

### 3.4 Automated Health Check & Verification

The container includes a built-in Docker healthcheck polling `http://localhost:8000/health` every 30 seconds.

Verify service operational status from your host terminal:

```bash
# Verify base server health
curl -f http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"1.0.0","environment":"production"}

# Verify ML subsystem readiness
curl -f http://localhost:8000/api/v1/ml/status

# Verify GenAI service readiness
curl -f http://localhost:8000/api/v1/genai/status
```

### 3.5 Stopping and Managing the Container

```bash
# Stop containers without removing volumes
docker compose stop

# Restart containers
docker compose restart

# Tear down containers and networks (preserves persistent volumes)
docker compose down

# Tear down containers and delete database volume
docker compose down -v
```

---

## 4. Local Bare-Metal Setup (Development & Testing)

If running directly on the host machine without Docker:

### 4.1 Python Virtual Environment

```bash
# 1. Navigate to the repository root
cd "D:\MedIntel AI"

# 2. Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 3. Upgrade pip and install backend dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4.2 System Dependencies (Tesseract OCR)

- **Windows**: Install Tesseract OCR from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Ensure `tesseract.exe` is added to system `PATH` (e.g. `C:\Program Files\Tesseract-OCR`).
- **Ubuntu/Debian**:
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
  ```
- **macOS**:
  ```bash
  brew install tesseract
  ```

### 4.3 Database Initialization

The SQLite database automatically provisions its schema upon first startup. To verify or manually run database migrations:

```bash
python -c "from app.database import init_db; init_db()"
```

### 4.4 Launching the Uvicorn Server

```bash
# Development mode with hot reload
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# Production mode with multiple worker processes
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --workers 4
```

Interactive OpenAPI documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 5. Mobile Application Build & Deployment (Flutter)

The Flutter application (`mobile/`) provides the cross-platform client for end users.

### 5.1 Configuring Backend API URL

Configure the mobile client to point to the backend server. The default base URL is defined in `mobile/lib/core/constants/app_constants.dart` (or configurable via environment variables):

- **Android Emulator**: `http://10.0.2.2:8000`
- **Physical Device / Local LAN**: `http://<YOUR_HOST_LOCAL_IP>:8000` (e.g., `http://192.168.1.100:8000`)
- **Production Server**: `https://api.medintel.yourdomain.com`

### 5.2 Building for Physical Android Device

Ensure Android device has **USB Debugging** enabled.

```bash
cd mobile

# 1. Fetch Flutter dependencies
flutter pub get

# 2. Run static analysis (verify zero errors/warnings)
flutter analyze

# 3. Run mobile widget and unit test suites
flutter test

# 4. Run directly on connected physical device
flutter run -d <DEVICE_ID>
```

### 5.3 Generating Release Android APK

```bash
cd mobile

# Build universal release APK
flutter build apk --release

# The compiled APK is generated at:
# mobile/build/app/outputs/flutter-apk/app-release.apk
```

> [!NOTE]
> Android SDK compilation requires `compileSdk = 36` to satisfy modern Android lifecycle dependencies (`flutter_plugin_android_lifecycle`). This is configured in `mobile/android/app/build.gradle`.

---

## 6. Security & Production Hardening

### 6.1 Reverse Proxy & SSL/TLS (Nginx Example)

In a public deployment, terminate SSL/TLS at a reverse proxy (Nginx or Traefik) in front of the FastAPI backend:

```nginx
server {
    listen 443 ssl http2;
    server_name api.medintel.example.com;

    ssl_certificate /etc/letsencrypt/live/api.medintel.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.medintel.example.com/privkey.pem;

    client_max_body_size 12M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6.2 Data Privacy & Regulatory Guardrails

1. **Zero Real Patient Data**: Do not store unanonymized PHI/PII on unencrypted public storage.
2. **Volatile In-Memory Verification**: OCR extractions remain unverified until the user confirms them. The backend enforces `is_user_verified=True` before analytical and GenAI processing.
3. **API Key Isolation**: Keep `GEMINI_API_KEY` restricted to server-side environment variables; never compile API secrets into the mobile application binary.
4. **CORS Restrictions**: In production, restrict `allow_origins` in `backend/app/main.py` from `["*"]` to your specific client domains.

---

## 7. Operational Troubleshooting

| Issue | Likely Root Cause | Solution |
|:---|:---|:---|
| `502 Bad Gateway` / Connection Refused | Backend container is not running or crashed | Check logs: `docker compose logs backend`. Confirm port 8000 is open. |
| `INSUFFICIENT_FEATURES` on ML endpoint | Required biomarker missing from request payload | Verify all clinical features are supplied. Check `docs/PHASE7_API_INTEGRATION.md`. |
| OCR returns empty text | Image resolution too low or unreadable font | Ensure image has $\ge 300\text{ DPI}$ or utilize the manual correction dialog. |
| Gemini API `429 Too Many Requests` | Quota exceeded or network timeout | Service automatically falls back to offline deterministic explanation generator. |
| Mobile connection timeout on physical phone | Mobile device cannot route to `localhost` | Replace `127.0.0.1` with the local LAN IP address of your machine in `app_constants.dart`. |
