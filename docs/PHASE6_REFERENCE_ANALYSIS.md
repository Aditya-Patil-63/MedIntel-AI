# Phase 6: Medical Reference Analysis & Extraction — Architecture & Design Document

> MedIntel AI — Intelligent Medical Report Analyzer
>
> Phase 6: Deterministic Medical Reference Analysis (Complete)

---

## 1. Executive Summary

Phase 6 implements the **Medical Reference Analysis and Deterministic Value Extraction Subsystem** for MedIntel AI. It introduces:
1. An authoritative, audited registry of clinical laboratory reference intervals (`reference/ranges.py`).
2. A deterministic string normalizer and unit compatibility layer (`reference/normalizer.py`).
3. A deterministic report parser for extracting measurements, values, and units from unstructured text (`reference/parser.py`).
4. An auditable, transparent classification engine (`reference/analyzer.py`).

### Primary Safety Directive
- **Strict Non-Diagnostic Guarantee**: The reference analysis subsystem does **NOT** diagnose medical diseases or recommend treatments.
- **Allowed Classifications**: Classifications are strictly restricted to:
  - `LOW`
  - `NORMAL`
  - `HIGH`
  - `CRITICAL`
  - (Or structured non-classifiable statuses: `VALUE_MISSING`, `UNKNOWN_UNIT`, `UNIT_MISMATCH`, `AMBIGUOUS`, `UNRECOGNIZED_ANALYTE`, `QUALITATIVE_RESULT`, `INVALID_VALUE`, `CONTEXT_REQUIRED`).
- The engine never generates clinical declarations such as *"You have diabetes"*, *"You have chronic kidney disease"*, or *"Take insulin"*.
- A mandatory safety disclaimer is appended to every analysis response:
  > *"This is not a medical diagnosis. Please consult a qualified healthcare professional."*

---

## 2. Architecture & Pipeline

```
Unstructured Document / OCR Text
          ↓
MedicalValueParser (`reference/parser.py`)
  ├── Analyte Prefix Match (exact token, zero fuzzy matching)
  ├── Separator Stripping (colon, hyphen, equals, whitespace)
  ├── Range-Text Segregation (captures printed range without corrupting measured value)
  ├── Number Parsing (integers, commas, floats, leading decimals like .95)
  └── Unit Normalization (mg/dL, g/dL, cells/uL, mEq/L, %)
          ↓
ParsedMeasurement (`reference/models.py`)
          ↓
ReferenceAnalyzer (`reference/analyzer.py`)
  ├── Demographic Context Matching (sex, age)
  ├── Non-Negative Physiological Validation
  ├── Strict Unit Compatibility (zero silent unit conversions)
  └── Deterministic Boundary Arithmetic
          ↓
AnalysisResult (`reference/models.py`)
  ├── Classification: LOW / NORMAL / HIGH / CRITICAL
  └── Mandatory Medical Disclaimer
```

### Component Breakdown

1. **`reference.models`**:
   - `Classification`: Enum (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`).
   - `AnalysisStatus`: Operational status tracking (`SUCCESS`, `REFERENCE_NOT_AVAILABLE`, `UNIT_MISMATCH`, `UNKNOWN_UNIT`, `VALUE_MISSING`, `VALUE_NON_NUMERIC`, `INVALID_VALUE`, `CONTEXT_REQUIRED`, `QUALITATIVE_RESULT`).
   - `ParserStatus`: Parsing outcomes (`SUCCESS`, `VALUE_MISSING`, `UNKNOWN_UNIT`, `AMBIGUOUS`, `UNRECOGNIZED_ANALYTE`, `QUALITATIVE_RESULT`).
   - `ReferenceType`: Distinguishes `GENERAL_REFERENCE` from `LAB_SPECIFIC_REFERENCE`.
   - `VerificationStatus`: Audit verification flag (`VERIFIED`, `PENDING_VERIFICATION`).
   - `PatientContext`: Optional demographic context (`sex`, `age`).
   - `ReferenceRange`: Core schema for reference intervals, normal/critical bounds, sex/age constraints, and authoritative clinical citations.
   - `ParsedMeasurement`: Structured output from text parsing with extraction confidence (reflecting parsing fidelity only, never clinical certainty).
   - `TestMeasurement`: Input model for reference analysis.
   - `AnalysisResult`: Complete structured output maintaining a transparent audit trail from input text to canonical classification.

2. **`reference.normalizer` (`AnalyteNormalizer`)**:
   - Deterministic string cleaning (whitespace collapse, case-folding, punctuation normalization).
   - Strict 1-to-1 alias-to-canonical mapping.
   - **Zero Fuzzy Matching**: Edit-distance matching is strictly prohibited to eliminate accidental cross-mapping of distinct clinical entities (e.g., Sodium vs. Potassium).
   - Unit representation normalization (e.g., `mg/dl` $\to$ `mg/dL`, `cells/cumm` $\to$ `cells/uL`).
   - Qualitative result detection (e.g., *"Positive"*, *"Negative"*, *"Reactive"*, *"Trace"*).

3. **`reference.ranges` (`ReferenceRangeRegistry`)**:
   - In-memory registry supporting context-aware resolution.
   - Demographic priority: resolves sex-specific intervals when biological sex is provided (`M` or `F`), falling back to general adult intervals with an audit warning when sex is omitted.
   - Initial factory `get_default_registry()` pre-populated with 10 core laboratory analytes.

4. **`reference.parser` (`MedicalValueParser`)**:
   - Deterministically parses report lines and multi-line text blocks.
   - Separates patient measurement from printed laboratory reference ranges on the same line (e.g. `Glucose 92 mg/dL 70-99`).
   - Flags ambiguity when multiple unmatched numbers appear on a single line without guessing.
   - Preserves qualitative results as text without attempting numeric casting.

5. **`reference.analyzer` (`ReferenceAnalyzer`)**:
   - Validates input presence, numerical parseability, physiological validity, and unit compatibility.
   - Executes deterministic interval classification.
   - Exposes `analyze()` for single measurements and `analyze_many()` for batch processing.

---

## 3. Authoritative Reference Audit Findings (Part A)

All configured reference definitions were audited against authoritative clinical literature, consensus guidelines, and hospital reference policies (ADA Standards of Care 2024, WHO Anemia Guidelines, NKF KDIGO, NCEP ATP III, Mayo Clinic Laboratories Critical Values, and CAP Q-Probes Surveys).

### Verified Reference Definitions

| # | Analyte | Canonical Name | Standard Unit | Normal Range | Critical Low | Critical High | Demographic Context | Audit Status | Authoritative Source Citation |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Fasting Blood Sugar | `Fasting Blood Glucose` | `mg/dL` | 70.0 – 99.0 | < 50.0 | > 400.0 | All adults (8-12h fast) | **VERIFIED** | ADA Standards of Care (2024); Mayo Clinic Laboratories |
| 2 | Hemoglobin (Male) | `Hemoglobin` | `g/dL` | 13.8 – 17.2 | < 7.0 | > 20.0 | Adult Male (`M`) | **VERIFIED** | NIH / Harrison's Principles of Internal Medicine, 21e; Mayo Clinic |
| 3 | Hemoglobin (Female) | `Hemoglobin` | `g/dL` | 12.1 – 15.1 | < 7.0 | > 20.0 | Adult Female (`F`) | **VERIFIED** | NIH / Harrison's Principles of Internal Medicine, 21e; Mayo Clinic |
| 4 | Hemoglobin (General) | `Hemoglobin` | `g/dL` | 12.0 – 17.5 | < 7.0 | > 20.0 | General Adult (fallback) | **VERIFIED** | WHO Haemoglobin Guidelines; Tietz 4e |
| 5 | Serum Creatinine (Male) | `Serum Creatinine` | `mg/dL` | 0.7 – 1.3 | None | None | Adult Male (`M`) | **VERIFIED** | National Kidney Foundation KDIGO; American Kidney Fund; Tietz 6e |
| 6 | Serum Creatinine (Female) | `Serum Creatinine` | `mg/dL` | 0.6 – 1.1 | None | None | Adult Female (`F`) | **VERIFIED** | National Kidney Foundation KDIGO; American Kidney Fund; Tietz 6e |
| 7 | Serum Creatinine (General) | `Serum Creatinine` | `mg/dL` | 0.6 – 1.3 | None | None | General Adult (fallback) | **VERIFIED** | National Kidney Foundation KDIGO; American Kidney Fund; Tietz 6e |
| 8 | White Blood Cell Count | `White Blood Cell Count` | `cells/uL` | 4,000 – 11,000 | < 2,000 | > 30,000 | All adults | **VERIFIED** | Harrison's 21e; CAP Q-Probes Survey |
| 9 | Platelet Count | `Platelet Count` | `cells/uL` | 150,000 – 450,000 | < 50,000 | > 1,000,000 | All adults | **VERIFIED** | Harrison's 21e; Mayo Clinic Laboratories (<= 40,000, >= 1,000,000) |
| 10 | Serum Potassium | `Serum Potassium` | `mEq/L` | 3.5 – 5.0 | < 2.8 | > 6.2 | All adults (unhemolyzed) | **VERIFIED** | Tietz 6e; CAP Critical Values Survey; Mayo Clinic (< 3.0, > 5.9 mmol/L) |
| 11 | Serum Sodium | `Serum Sodium` | `mEq/L` | 135.0 – 145.0 | < 120.0 | > 160.0 | All adults | **VERIFIED** | Tietz 6e; Mayo Clinic Laboratories (< 120, > 160 mmol/L) |
| 12 | Total Cholesterol | `Total Cholesterol` | `mg/dL` | 125.0 – 200.0 | None | None | All adults | **VERIFIED** | NCEP ATP III / American Heart Association (No acute critical values) |
| 13 | Blood Urea Nitrogen | `Blood Urea Nitrogen` | `mg/dL` | 7.0 – 20.0 | None | None | All adults | **VERIFIED** | Tietz 6e; Mayo Clinic (adult normal 6-21 mg/dL; acute panic criteria lab-specific) |
| 14 | Glycated Hemoglobin | `Glycated Hemoglobin` | `%` | 4.0 – 5.6 | None | None | All adults | **VERIFIED** | ADA Standards of Care (2024) (No acute critical values) |

### Specific Audit Decisions:
1. **Adult Creatinine Critical High**: Audit revealed that clinical laboratories (e.g. Mayo Clinic adult critical list, CAP) do not enforce a universal adult critical cutoff for creatinine because patients with chronic kidney disease often have stable elevated baselines, and acute renal failure is diagnosed via rate-of-rise (delta) or eGFR staging. In adherence to the project rule (*"If a critical threshold cannot be reliably sourced, set it to None and do not invent one"*), `critical_high` for adult creatinine is set to `None`.
2. **Total Cholesterol and HbA1c**: Reflect chronic disease risk factors rather than acute metabolic emergencies. Neither test possesses acute panic/critical thresholds in clinical practice; `critical_low` and `critical_high` are set to `None`.
3. **Pending Lab-Specific Calibrations**:
   - *Pediatric Reference Ranges*: Substantially different from adult ranges (e.g., neonatal hemoglobin 14–24 g/dL; pediatric alkaline phosphatase elevated during skeletal development).
   - *Pregnancy Trimester Intervals*: Dilutional physiological anemia and gestational glucose thresholds.
   - *Enzymatic Liver Panels (ALT, AST, ALP)*: Temperature-dependent (37°C vs 30°C) and method-dependent; require lab-specific calibration.

---

## 4. Deterministic Medical Value Extraction Design (Part B)

### Pattern Matching Architecture
1. **Separators**: Colons (`:`), equals (`=`), hyphens with space (`- `), multiple spaces, and tabs (`\t`).
2. **Numeric Representations**: Integers (`92`), floats (`92.0`, `14.2`), comma-thousands (`8,500`, `220,000`), and leading decimals (`.95`).
3. **Unit Tolerances**: Casing variations (`mg/dl`, `MG/DL`), formatting variations (`mg / dL`, `14.2g/dL`), and equivalent synonyms (`/uL`, `/cumm`, `cells/cumm` $\to$ `cells/uL`).
4. **Range-Text Segregation**: Detects and isolates printed reference intervals appearing on the same line (e.g., `Glucose 92 mg/dL 70-99`, `Hb 14.2 g/dL (13.8-17.2)`, `Potassium 4.2 mEq/L [3.5-5.0]`, `Cholesterol 190 mg/dL < 200`) into `extracted_reference_range`, ensuring the patient's measured value is not confused with range boundary numbers.
5. **Ambiguity Policy**: If a line contains multiple competing numbers that do not match range syntax (e.g., `FBS: 92 105 mg/dL`), the parser marks `ParserStatus.AMBIGUOUS` with reduced extraction confidence (0.5) and does **NOT** guess.
6. **Qualitative Handling**: Non-numeric clinical entries (`"Negative"`, `"Positive"`, `"Reactive"`, `"Trace"`) are parsed as `QUALITATIVE_RESULT` rather than miscast into 0.0 or causing runtime exceptions.

---

## 5. FastAPI API & SQLite Database Integration (Step 3)

### Endpoints & Service Architecture
The deterministic reference engine connects to the FastAPI backend via a dedicated service layer (`ReferenceService`), preserving an architectural separation between HTTP/DB logic and clinical reference calculations:

```
FastAPI Router (`backend/app/api/reference.py`)
       ↓
ReferenceService (`backend/app/services/reference_service.py`)
       ↓
MedicalValueParser / ReferenceAnalyzer (`reference/`)
       ↓
Database Persistence (`TestResult` in SQLite)
```

1. **`POST /api/v1/reference/analyze`**:
   - Accepts a batch of structured measurements (`MeasurementInputSchema`) with optional demographic context (`PatientContextSchema`) and report association (`report_id`).
   - Returns structured evaluations containing canonical analyte, normalized unit, classification (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`), reference range metadata, citations, warnings, and mandatory disclaimer.
   - Supports optional persistence via `persist=true`.

2. **`POST /api/v1/reference/parse-and-analyze`**:
   - Accepts raw document text (`text`), optional demographic context (`context`), and optional report link (`report_id`).
   - Runs `MedicalValueParser` to parse each line into structured candidate measurements, then invokes `ReferenceAnalyzer` on each parsed item.
   - Returns per-line parser outcomes (`parsed_analyte`, `parser_status`, `extracted_reference_range`) alongside full deterministic reference analysis.

### Database Persistence & Schema Extension
- Schema: The existing `test_results` table in `backend/app/models/models.py` is extended with 3 nullable audit columns:
  - `canonical_name` (String(255), nullable): Canonical clinical name from the registry.
  - `reference_source` (String(255), nullable): Medical authority citation (e.g. ADA, WHO, Harrison's).
  - `analysis_status` (String(50), nullable): Engine operational status (e.g. `SUCCESS`, `UNIT_MISMATCH`).
- Preserves all 7 existing tables without breaking Phase 2 schema tests (`test_table_count` = 7).
- Behavior:
  - `persist=false` (default): Pure analysis; zero database modifications.
  - `persist=true`: Requires `report_id`. Verified against the `reports` table; returns HTTP 400 if missing, HTTP 404 if invalid.
  - Commits test result records with lowercase classification (`"low"`, `"normal"`, `"high"`, `"critical"`).

### User Verification Safety Gate
- In compliance with project safety rules, OCR extraction is strictly distinguished from verified clinical measurements:
  - `is_user_verified=false` (0 in SQLite): Default for raw OCR extractions.
  - `is_user_verified=true` (1 in SQLite): Set only after explicit user review and confirmation.
- The API explicitly returns `is_user_verified` in responses and persists it to the database, ensuring unreviewed OCR text is never presented downstream as confirmed medical data.

### Privacy & Logging Policy
- API logging records aggregate metadata and operation metrics only (e.g., `submitted=1, classified=1, persisted=False`).
- Does **NOT** log:
  - Complete medical reports or raw OCR documents.
  - Patient names or patient identifiers.
  - Test values, extracted measurements, or API secrets.

---

## 6. Verification & Test Coverage

Test suite status across all project modules:
- **`tests/test_phase6_parser.py` (32 tests)**: Parsing patterns 1–11, decimals (.95), separators, range-text segregation, ambiguity, whitespace noise, and end-to-end pipeline.
- **`tests/test_phase6_reference.py` (40 tests)**: Interval classifications, exact boundaries, context resolution, non-critical limits, and safety disclaimers.
- **`backend/tests/test_phase6_api.py` (20 tests)**: API endpoints (normal, low, high, critical, boundary inclusivity, unit mismatch, missing/invalid values, demographic context, parser pipeline, ambiguity, qualitative results, disclaimers, non-diagnostic verification, HTTP 422, SQLite persistence, report linking, and verification gate).
- **`tests/test_phase5_handwriting.py` (18 tests)**: Phase 5 regression tests.
- **`tests/test_phase4_ocr.py` (20 tests)**: Phase 4 regression tests.
- **`tests/test_phase3_data.py` (24 tests)**: Phase 3 regression tests.
- **`backend/tests/test_phase2.py` (11 tests)**: Phase 2 regression tests.

```text
======================= 165 passed, 1 warning in 6.95s =======================
```
All 165 tests pass with 100% success. Database test fixtures remain strictly isolated in temporary SQLite databases (`tmp_path`).
