# Tests — MedIntel AI

Comprehensive test suite covering all backend services, ML inference pipelines, reference engines, GenAI integrations, and Flutter mobile client workflows.

---

## 1. Test Suite Summary

| Subsystem / Phase | Test File Location | Passing Tests | Scope |
|---|---|:---:|---|
| **Phase 2:** Backend Foundation | `backend/tests/test_phase2.py` | 11 | FastAPI lifecycle, health endpoints, SQLite schema |
| **Phase 3:** Data Preparation | `tests/test_phase3_data.py` | 24 | Deterministic data cleaning, encoding, validation |
| **Phase 4:** PDF & OCR Pipeline | `tests/test_phase4_ocr.py` | 20 | pdfplumber, OCR engine adapters, format checks |
| **Phase 5:** Handwriting Recognition | `tests/test_phase5_handwriting.py` | 18 | TrOCR transforms, CER/WER metrics, dataset splits |
| **Phase 6:** Medical Reference Engine | `tests/test_phase6_parser.py`<br>`tests/test_phase6_reference.py`<br>`backend/tests/test_reference_api.py` | 103 | Deterministic parser, ADA/WHO reference classification, verification gate |
| **Phase 7:** ML Risk Models & API | `tests/test_phase7_ml.py`<br>`tests/test_phase7_audit.py`<br>`tests/test_phase7_api.py` | 48 | Pipeline inference, model loading, `INSUFFICIENT_FEATURES` handling |
| **Phase 8:** Generative AI & Translation | `tests/test_phase8_schemas.py`<br>`tests/test_phase8_api.py`<br>`tests/test_phase8_gemini.py` | 35 | Gemini provider, offline mock, multilingual invariance (EN, HI, MR, GU) |
| **Phase 9:** Mobile Flutter Client | `mobile/test/*_test.dart` (9 suites) | 66 | Cubits, UI widgets, verified snapshot, end-to-end integration |
| **Phase 10 (Steps 1 & 2):** E2E Pipeline Integration | `tests/test_phase10_e2e_integration.py` | 9 | Unified document→analysis→ML→GenAI flow, gate enforcement, persistence |
| **Phase 10 (Step 3):** Edge Cases & Fault Tolerance | `tests/test_phase10_edge_cases_and_fault_tolerance.py` | 33 | Corrupted inputs, ReDoS/stress parsing, extreme boundaries, provider fallbacks, DB rollback |
| **Phase 10 (Step 4):** Performance & Concurrency | `tests/test_phase10_performance_and_concurrency.py` | 6 | Sub-second latencies, model singleton caching, concurrent scaling, memory stability |
| **Total Test Suite** | **Full Repository** | **373 Tests** | **Zero Failures, 100% Passing** |

---

## 2. Running Tests

### Automated Cross-Subsystem Runner

Execute the complete repository suite (backend pytest + Flutter mobile tests) in a single command:

```powershell
.\backend\venv\Scripts\python.exe scripts/run_cross_subsystem_tests.py
```

### Running Backend Tests (Python / Pytest)

From the repository root:

```powershell
# Run complete backend suite
.\backend\venv\Scripts\python.exe -m pytest -q

# Run specific phase test suite
.\backend\venv\Scripts\python.exe -m pytest tests/test_phase10_e2e_integration.py -v
```

### Running Mobile Client Tests (Flutter)

From the `mobile/` directory:

```powershell
cd mobile
flutter test
```

---

## 3. Medical Safety & Privacy Invariants

All tests strictly comply with [PROJECT_RULES.md](../PROJECT_RULES.md) Section 7:
1. **Zero Real Patient Data:** All test cases use synthetic laboratory values and anonymized mock profiles.
2. **Deterministic Classification:** Reference ranges are verified against authoritative medical standards (ADA, WHO, Harrison's, Mayo Clinic).
3. **Non-Diagnostic Assurance:** ML outputs are validated strictly as risk indicators with disclaimers.
4. **Offline Isolation:** Backend unit/integration tests run completely offline with zero external network dependencies.
