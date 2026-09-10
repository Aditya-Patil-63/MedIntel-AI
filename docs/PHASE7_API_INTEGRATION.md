# Phase 7 — ML Risk Models: Step 4 FastAPI Integration Report

> **MedIntel AI — FastAPI Machine Learning Risk Estimation Integration**  
> **Status:** Phase 7 Step 4 Complete (FastAPI REST Endpoints, In-Memory Model Caching, Cryptographic SHA-256 Verification, User Verification Gate, and SQLite Database Persistence)  
> **Mandatory Medical Disclaimer:** These models provide continuous *model-estimated risk probabilities* derived from historical research benchmarks for educational screening prototypes. They do NOT provide a clinical diagnosis, medical prognosis, or treatment recommendation.

---

## 1. System Architecture

The FastAPI backend exposes disease risk estimation endpoints as independent analytical modules operating downstream of user verification:

```
Document Upload (PDF / Scanned / Handwritten)
                    ↓
         OCR / TrOCR Extraction
                    ↓
        Structured Medical Values
                    ↓
        USER VERIFICATION GATE
       (is_user_verified == True)
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
Phase 6 Reference Engine       Phase 7 ML Risk Models
Deterministic Ranges           Continuous Risk Probability P(target=1)
(Low / Normal / High / Critical) (Low / Moderate / Elevated)
       │                         │
       └────────────┬────────────┘
                    ▼
          Aggregated Response
                    ↓
       GenAI Simple Explanation (Future Phase)
```

### Architectural Separation:
- **Phase 6 Reference Engine:** Deterministic rule-based evaluation against authoritative laboratory intervals. Outputs classification: `LOW`, `NORMAL`, `HIGH`, `CRITICAL`.
- **Phase 7 ML Risk Models:** Statistical probability estimation from multivariate patient profiles. Outputs continuous probability: $P(\text{target}=1) \in [0.0, 1.0]$ and educational risk band: `LOW`, `MODERATE`, `ELEVATED`.
- **Independent Analytical Components:** The reference analysis engine does not call the ML models, and the ML models do not alter or overwrite deterministic reference intervals.

---

## 2. API Endpoints

All endpoints are registered under `/api/v1/ml`:

| Method | Endpoint | Request Schema | Response Schema | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/ml/diabetes-risk` | `DiabetesRiskRequest` | `RiskPredictionResponse` | Estimates diabetes risk from 8 clinical features (Random Forest) |
| `POST` | `/api/v1/ml/heart-risk` | `HeartDiseaseRiskRequest` | `RiskPredictionResponse` | Estimates heart disease risk from 13 clinical features (Logistic Regression) |
| `POST` | `/api/v1/ml/kidney-risk` | `KidneyDiseaseRiskRequest` | `RiskPredictionResponse` | Estimates CKD risk from 24 clinical features (Logistic Regression) |
| `GET` | `/api/v1/ml/status` | None | `MLStatusResponse` | Health check reporting model availability and SHA integrity without leaking private paths |

---

## 3. Request & Response Schemas

### 3.1 Request Schemas (`backend/app/schemas/ml_risk.py`)
- **`DiabetesRiskRequest`:**
  - Features: `Pregnancies`, `Glucose`, `BloodPressure`, `SkinThickness`, `Insulin`, `BMI`, `DiabetesPedigreeFunction`, `Age` (all `Optional[float] = None`).
  - Workflow Controls: `is_user_verified: bool = True`, `report_id: Optional[int] = None`.
  - Input Validation: Pydantic field validators reject `NaN`, `Inf`, or non-numeric strings with HTTP 422.
- **`HeartDiseaseRiskRequest`:**
  - Continuous Features: `age`, `trestbps`, `chol`, `thalach`, `oldpeak`.
  - Binary Features: `sex`, `fbs`, `exang`.
  - Categorical Features: `cp`, `restecg`, `slope`, `ca`, `thal`.
  - Workflow Controls: `is_user_verified: bool = True`, `report_id: Optional[int] = None`.
- **`KidneyDiseaseRiskRequest`:**
  - 14 Numerical Features: `age`, `bp`, `sg`, `al`, `su`, `bgr`, `bu`, `sc`, `sod`, `pot`, `hemo`, `pcv`, `wc`, `rc`.
  - 10 Categorical Features: `rbc`, `pc`, `pcc`, `ba`, `htn`, `dm`, `cad`, `appet`, `pe`, `ane` (strings normalized and stripped).
  - Workflow Controls: `is_user_verified: bool = True`, `report_id: Optional[int] = None`.

### 3.2 Response Schema: `RiskPredictionResponse`
```json
{
  "condition": "diabetes",
  "status": "OK",
  "risk_probability": 0.2872,
  "risk_band": "LOW",
  "model_name": "RandomForest_d4_s8",
  "model_version": "2026-09-10T06:06:01.123456+00:00",
  "supplied_features_count": 8,
  "required_features_count": 8,
  "missing_features": [],
  "disclaimer": "This estimated risk score is an educational indicator derived from historical research datasets. It is NOT a medical diagnosis, clinical prognosis, or treatment recommendation. Please consult a qualified healthcare professional for comprehensive medical evaluation.",
  "persisted_prediction_id": 14
}
```

---

## 4. User Verification Safety Gate

In clinical workflows, input features derived from OCR or TrOCR must not trigger automated ML inference without patient/clinician review:
- If `is_user_verified == False`:
  - The service halts prediction immediately.
  - Returns HTTP 200 with `status="VERIFICATION_REQUIRED"`.
  - `risk_probability=None` and `risk_band=None`.
  - Database persistence is completely skipped.
  - Protects against noisy or unconfirmed OCR extractions influencing algorithmic outputs.

---

## 5. Missing Feature Policy (`INSUFFICIENT_FEATURES`)

To eliminate risks of silent imputation or hallucinated risk indicators:
- If any required feature is missing or `None`:
  - Returns HTTP 200 with `status="INSUFFICIENT_FEATURES"`.
  - `risk_probability=None` and `risk_band=None`.
  - Returns the exact list of missing features in `missing_features`.
  - Zero default values or population averages are substituted.

---

## 6. Model Loading, Caching & Cryptographic Integrity

### Caching:
- `MLRiskService` implements an in-memory dictionary cache (`self._predictors`).
- Pipelines are loaded into memory once on first access and reused for subsequent requests, ensuring fast response times without repeated disk I/O.

### Cryptographic Verification:
- When loading an external artifact, the service computes its SHA-256 checksum and compares it against `model_metadata.json["pipeline_sha256"]`.
- If a binary file is modified or tampered with, loading immediately aborts and returns HTTP 500 (`"Model artifact failed cryptographic integrity verification"`).
- Missing artifacts or invalid directories similarly return descriptive HTTP 500 errors.

---

## 7. Probability Semantics & Educational Risk Bands

- **Probability Metric:** All endpoints return $P(\text{target}=1)$ using `estimator.classes_` to identify the positive class index.
- **Terminology:** Described strictly as `"model-estimated risk probability"`. Prohibited terms ("diagnosis", "confirmed disease", "medical certainty") are strictly excluded.
- **Educational Risk Bands:**
  - **LOW:** $P < 0.30$
  - **MODERATE:** $0.30 \le P < 0.70$
  - **ELEVATED:** $P \ge 0.70$
  - Defined as non-diagnostic display categories for educational screening prototypes only.

---

## 8. Database Persistence Integration

The service integrates seamlessly with the existing Phase 2 SQLite database schema:
- When `report_id` is supplied in the request body:
  1. Validates that the report exists in `reports` table (raises HTTP 404 if missing).
  2. Maps educational risk band to `Prediction.risk_level` enum (`low`, `moderate`, `high`).
  3. Inserts record into `predictions` table with `condition`, `risk_score`, `model_name`, `model_version`, `disclaimer`, and `created_at`.
  4. Returns the database record primary key in `persisted_prediction_id`.
- If `report_id` is omitted, prediction proceeds statelessly without database writes.

---

## 9. Test Suite Verification

Comprehensive integration tests implemented in [`tests/test_phase7_api.py`](file:///d:/MedIntel%20AI/tests/test_phase7_api.py) (20 tests covering endpoints, verification gates, missing-feature safety, type validation, NaN/Inf rejection, unknown categoricals, caching, SHA verification, persistence, and Phase 6 backward compatibility).

### Full Workspace Regression Results:
```
213 passed, 4 warnings in 23.50s
```
- **Phase 1–6 tests:** 165 passed
- **Phase 7 Step 2 ML tests:** 20 passed
- **Phase 7 Step 3 Audit tests:** 8 passed
- **Phase 7 Step 4 API tests:** 20 passed
- **Total Passing:** **213 tests (0 failures, 0 regressions)**
