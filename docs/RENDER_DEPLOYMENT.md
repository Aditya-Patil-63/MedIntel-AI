# MedIntel AI — Render & Neon Postgres Deployment Guide

> Complete step-by-step deployment guide for running the MedIntel AI backend on **Render (Free Plan, 512 MB RAM, Docker Web Service)** with an external **Neon PostgreSQL (Free Serverless)** database.

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │          Flutter Mobile App            │
                      └──────────────────┬─────────────────────┘
                                         │ HTTPS / REST
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Render Free Web Service (Docker Container: 512 MB RAM, 1 CPU Worker)                   │
│                                                                                        │
│  FastAPI Backend (Uvicorn single-worker, PORT dynamic)                                 │
│  ├── Health Check (/health) & ML Status (/api/v1/ml/status)                           │
│  ├── In-repo Trained Models (deploy/ml_models/ ~262 KB: Diabetes, Heart, Kidney)       │
│  ├── Tesseract OCR (Engine with 15s timeout safeguard & 10-page scan capping)         │
│  └── Deterministic Medical Reference Range Evaluator                                  │
└───────────────────┬────────────────────────────────────────────┬───────────────────────┘
                    │                                            │
                    ▼                                            ▼
┌──────────────────────────────────────┐     ┌───────────────────────────────────────────┐
│ Neon Serverless PostgreSQL Database  │     │ Google Gemini API                         │
│ (Free Tier, SSL Mode Required)       │     │ (gemini-3.5-flash-lite explanations)      │
└──────────────────────────────────────┘     └───────────────────────────────────────────┘
```

---

## Step 1: Provision Free Database on Neon

1. Visit [Neon Console](https://console.neon.tech/) and sign up / log in.
2. Click **Create Project**:
   - **Project Name**: `medintel-ai`
   - **Postgres Version**: 16 (default)
   - **Region**: Choose **Singapore (`ap-southeast-1`)** or **Frankfurt (`eu-central-1`)** to match your Render deployment region for low latency.
3. Once created, copy the connection string from the dashboard. It will look like:
   ```text
   postgresql://<user>:<password>@ep-<endpoint-id>.singapore.aws.neon.tech/neondb?sslmode=require
   ```
   > **Note**: MedIntel AI automatically normalizes `postgres://` or `postgresql://` to `postgresql+psycopg2://` while keeping SSL parameters intact.

---

## Step 2: Obtain Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Create or select a Google Cloud Project and generate an **API Key**.
3. Keep this key handy for the Render configuration.
   > The default production model configured is `gemini-3.5-flash-lite` for high speed, low latency, and optimal free-tier rate limits.

---

## Step 3: Deploy to Render

### Option A: Using the Render Blueprint (Recommended — 1 Click)

1. Fork or push this repository to your GitHub account (`Aditya-Patil-63/MedIntel-AI` or your fork).
2. Go to the [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** > **Blueprint**.
4. Connect your GitHub repository. Render will automatically detect [`render.yaml`](../render.yaml) at the repository root.
5. Render will prompt you for the **4 Secret Environment Variables** (marked `sync: false`):
   - `DATABASE_URL`: Your Neon connection string (from Step 1).
   - `SECRET_KEY`: A secure random string of at least 32 characters. Generate one using:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - `GEMINI_API_KEY`: Your Google Gemini API key (from Step 2).
   - `CORS_ORIGINS`: Leave empty to allow mobile apps, or specify comma-separated origins (e.g. `https://my-domain.com`).
6. Click **Apply**. Render will build the Docker container and start the service.

### Option B: Manual Web Service Setup

If you prefer setting up the web service manually:

1. Click **New +** > **Web Service**.
2. Connect your repository.
3. Configure the service settings:
   - **Name**: `medintel-backend`
   - **Region**: `Singapore` (or `Frankfurt`)
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Instance Type**: `Free` (0.1 CPU, 512 MB RAM)
   - **Health Check Path**: `/health`
4. In the **Environment Variables** tab, add:
   | Key | Value | Notes |
   |-----|-------|-------|
   | `APP_ENV` | `production` | Enables production security checks |
   | `DEBUG` | `false` | Disables debug mode and query echo |
   | `GENAI_PROVIDER` | `gemini` | Uses Google Gemini API |
   | `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Recommended model |
   | `DEFAULT_OCR_ENGINE` | `tesseract` | Pure system OCR |
   | `MEDINTEL_ML_MODELS_DIR` | `/app/deploy/ml_models` | Uses bundled models |
   | `DATABASE_URL` | *Your Neon Postgres URL* | **Secret** |
   | `SECRET_KEY` | *Your 32+ char secret* | **Secret** |
   | `GEMINI_API_KEY` | *Your Gemini API key* | **Secret** |
   | `CORS_ORIGINS` | *Empty or allowed origins* | **Secret/Config** |
5. Click **Create Web Service**.

---

## Step 4: Verification & Smoke Testing

Once deployment completes and your service status is **Live**:

### 1. Verify Health Check
```bash
curl -i https://<your-render-service>.onrender.com/health
```
**Expected Response (HTTP 200)**:
```json
{
  "status": "healthy",
  "application": "MedIntel AI",
  "environment": "production",
  "version": "1.0.0",
  "timestamp": "2026-10-29T..."
}
```

### 2. Verify ML Models Integrity
```bash
curl -i https://<your-render-service>.onrender.com/api/v1/ml/status
```
**Expected Response (HTTP 200)**:
```json
{
  "status": "healthy",
  "models_directory": "/app/deploy/ml_models",
  "models": {
    "diabetes": {
      "model_type": "LogisticRegression",
      "available": true,
      "integrity_verified": true
    },
    "heart_disease": {
      "model_type": "LogisticRegression",
      "available": true,
      "integrity_verified": true
    },
    "kidney_disease": {
      "model_type": "RandomForestClassifier",
      "available": true,
      "integrity_verified": true
    }
  }
}
```

### 3. (Optional) Run Postgres Verification Locally
You can test your Neon database connection and table creation from your local machine before connecting to Render:
```bash
# In PowerShell:
$env:DATABASE_URL="your-neon-postgres-connection-string"
& python scripts/check_postgres.py
```
**Expected Output**:
```text
PostgreSQL connection string detected. Initiating Neon Postgres verification...
1/5: Verifying database schema and table initialization...
2/5: Creating test tenant user and testing authentication...
3/5: Creating second tenant user for isolation validation...
4/5: Creating sample report record for tenant 1...
5/5: Querying records and asserting tenant isolation...
Neon Postgres check: PASSED (verified 1 report record, 2 isolated tenant users)
```

---

## Step 5: Point Flutter Mobile App to Production

Update the mobile app's API base URL:

1. Open `mobile/lib/core/constants/api_constants.dart` (or your environment config).
2. Set `baseUrl`:
   ```dart
   static const String baseUrl = 'https://<your-render-service>.onrender.com';
   ```
3. Build and test on your device or emulator:
   ```bash
   flutter run --release
   ```

---

## Key Free-Tier Constraints & Safeguards

| Resource | Constraint | MedIntel AI Implementation |
|----------|------------|----------------------------|
| **RAM Budget** | 512 MB | Single Uvicorn worker (`--workers 1`), lightweight Scikit-learn pipelines (~262 KB total), no startup PyTorch/EasyOCR imports. |
| **OCR Memory** | Scanned PDFs can OOM | Automatic cap to first 10 pages for scanned PDF OCR; explicit PIL Image cleanup after extraction. |
| **OCR Timeouts** | Giant scans can hang worker | 15-second hard timeout enforced on all Tesseract invocations. |
| **Ephemeral Disk** | Disk resets on container redeploy | Relational records, user sessions, reports, and audit trails persist permanently in Neon Postgres. |
| **Cold Starts** | Inactive services sleep after 15 mins | Free Render services take 30–50 seconds to wake on initial request. The `/health` endpoint is lightweight and responds immediately once woken. |
| **Public Repo** | GitHub repo is public | Zero secrets stored in Git; strict `.dockerignore` prevents accidental file baking; models tracked via clean binary SHA-256 integrity checks. |
