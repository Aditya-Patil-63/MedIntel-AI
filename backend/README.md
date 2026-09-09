# Backend (FastAPI + Python)

FastAPI backend server for MedIntel AI.

## Status

**Phase 2 — Complete** ✅

Basic backend foundation with health-check endpoint and database schema.

---

## Quick Start

### 1. Create a Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy the example env file
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# Edit .env if needed (defaults work for development)
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at: **http://127.0.0.1:8000**

Interactive docs at: **http://127.0.0.1:8000/docs**

### 5. Run Tests

```bash
pytest -v
```

---

## Current Endpoints

| Method | Path      | Description                    |
|--------|-----------|--------------------------------|
| GET    | `/health` | Health check — verify the backend is running |

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # App package
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py        # Health-check endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Settings from environment variables
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py       # SQLAlchemy engine, session, Base
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py        # ORM models (7 tables)
│   ├── schemas/
│   │   └── __init__.py      # Pydantic schemas (Phase 3+)
│   └── services/
│       └── __init__.py      # Business logic (Phase 3+)
├── tests/
│   ├── __init__.py
│   └── test_phase2.py       # Phase 2 tests
├── .env.example              # Environment variable template
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## Database Schema

SQLite database with 7 tables managed by SQLAlchemy ORM:

| Table           | Purpose                                      |
|-----------------|----------------------------------------------|
| `users`         | Application users with language preferences  |
| `reports`       | Uploaded medical documents (PDFs, images)    |
| `test_results`  | Extracted medical test values and classifications |
| `predictions`   | ML risk prediction outputs (with disclaimers)|
| `prescriptions` | Extracted prescription metadata              |
| `medicines`     | Individual medicines within prescriptions    |
| `summaries`     | Generated health summary documents           |

See [models.py](app/models/models.py) for the full schema definition.

---

## Intentionally Deferred to Later Phases

The following are **NOT** implemented in Phase 2:

| Feature                          | Phase |
|----------------------------------|-------|
| PDF text extraction              | 3     |
| OCR (EasyOCR / Tesseract)        | 3     |
| Handwriting recognition (TrOCR)  | 4     |
| Reference-range analysis         | 5     |
| ML risk models                   | 6     |
| Claude API / GenAI explanations  | 7     |
| Report upload endpoint           | 3     |
| Analysis endpoint                | 5–7   |
| Prediction endpoint              | 6     |
| Summary generation endpoint      | 7     |
| User authentication              | 8     |
| File upload handling              | 3     |
