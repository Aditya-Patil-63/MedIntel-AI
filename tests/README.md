# Tests — MedIntel AI

Test suite for MedIntel AI.

## Status

- **Phase 2 Backend Tests:** `backend/tests/test_phase2.py` (11 passing tests)
- **Phase 3 Data Preparation Tests:** `tests/test_phase3_data.py` (24 passing tests)

## Running Tests

From the repository root:

```bash
# Run Phase 3 Data Preparation Tests
.\backend\venv\Scripts\python.exe -m pytest tests/test_phase3_data.py -v

# Run Phase 2 Backend Tests
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_phase2.py -v

# Run All Tests
.\backend\venv\Scripts\python.exe -m pytest -v
```

## Structure

- `tests/test_phase3_data.py` — Tests for external dataset path handling, missing-file handling, expected columns, deterministic cleaning logic, target encoding, and repository cleanliness checks (all using synthetic data; no real patient data)
- `backend/tests/test_phase2.py` — Tests for FastAPI startup, health-check endpoint, and SQLite schema
