# Medical Reference Analysis & Parser Module (`reference/`)

> MedIntel AI — Phase 6: Deterministic Medical Reference Analysis & Extraction
>
> Intelligent Medical Report Analyzer Using Machine Learning and Generative AI

---

## 1. Overview and Purpose

The `reference/` module provides a **deterministic laboratory reference-range analysis and medical value extraction engine** for MedIntel AI. It bridges unstructured text extracted by OCR and handwriting recognition modules to structured, audited clinical reference interval evaluations.

```
raw OCR / Handwriting Text
          ↓
MedicalValueParser (`reference/parser.py`)
  ├── Deterministic Analyte Matching (zero fuzzy matching)
  ├── Separator Stripping (:, =, -, whitespace)
  ├── Range-Text Segregation (distinguishes measurement from printed range)
  ├── Numeric Value Extraction (integers, floats, decimals like .95)
  └── Unit Normalization (mg/dL, g/dL, cells/uL, mEq/L, %)
          ↓
ParsedMeasurement (`reference/models.py`)
          ↓
ReferenceAnalyzer (`reference/analyzer.py`)
  ├── Context Resolution (demographic sex/age)
  ├── Non-Negative Physiological Validation
  ├── Strict Unit Compatibility (zero silent unit conversions)
  └── Deterministic Boundary Arithmetic
          ↓
AnalysisResult (`reference/models.py`)
  ├── Classification: LOW / NORMAL / HIGH / CRITICAL
  └── Mandatory Medical Disclaimer
```

### Core Non-Diagnostic Safety Guarantee
- The reference analysis engine **does NOT diagnose diseases**.
- It classifies measured values into four strictly defined categories: **`LOW`**, **`NORMAL`**, **`HIGH`**, or **`CRITICAL`** (or structured unclassifiable statuses).
- The engine **NEVER** outputs disease declarations (e.g., *"You have diabetes"*, *"You have chronic kidney disease"*), clinical risk predictions, or treatment instructions.
- A mandatory medical safety disclaimer is included on every analysis response:
  > *"This is not a medical diagnosis. Please consult a qualified healthcare professional."*

---

## 2. Architecture and Subsystems

The module is organized into six cohesive components:

```
reference/
├── __init__.py         # Public exports (models, analyzer, parser, registry)
├── models.py           # Schemas: Classification, AnalysisStatus, ParserStatus, ParsedMeasurement, ReferenceRange, AnalysisResult
├── normalizer.py       # Deterministic alias & unit normalizer (zero fuzzy matching)
├── ranges.py           # In-memory ReferenceRangeRegistry & factory with audited clinical ranges
├── analyzer.py         # Deterministic classification engine with boundary rules
├── parser.py           # Deterministic report line & text parser
└── README.md           # This documentation
```

---

## 3. Authoritative Reference Audit (Part A Findings)

Every reference interval configured in the system was audited against consensus medical publications, clinical laboratory guidelines, and hospital reference policies (ADA, WHO, NIH, Harrison's, Tietz, Mayo Clinic Laboratories, and CAP Q-Probes).

### Distinction: `GENERAL_REFERENCE` vs. `LAB_SPECIFIC_REFERENCE`
- **`GENERAL_REFERENCE`**: Represents well-established, population-level consensus reference intervals (e.g., ADA fasting glucose < 100 mg/dL). Configured intervals serve as **general educational baselines**. They are never represented as universally valid across all laboratories.
- **`LAB_SPECIFIC_REFERENCE`**: Acknowledges that specific hospital and clinical laboratories calibrate intervals based on unique local instrumentation, reagents, and local populations.

### Comprehensive Audit Matrix

| # | Analyte | Canonical Name | Standard Unit | Normal Interval | Critical Low | Critical High | Demographic Context | Verification Status | Source & Citation |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Fasting Blood Sugar | `Fasting Blood Glucose` | `mg/dL` | 70.0 – 99.0 | < 50.0 | > 400.0 | Adults (8-12h fast) | **VERIFIED** | ADA Standards of Care (2024); Mayo Clinic Laboratories Critical Values |
| 2 | Hemoglobin (Male) | `Hemoglobin` | `g/dL` | 13.8 – 17.2 | < 7.0 | > 20.0 | Adult Male (`M`) | **VERIFIED** | Harrison's Principles of Internal Medicine, 21e; Mayo Clinic |
| 3 | Hemoglobin (Female) | `Hemoglobin` | `g/dL` | 12.1 – 15.1 | < 7.0 | > 20.0 | Adult Female (`F`) | **VERIFIED** | Harrison's Principles of Internal Medicine, 21e; Mayo Clinic |
| 4 | Hemoglobin (General) | `Hemoglobin` | `g/dL` | 12.0 – 17.5 | < 7.0 | > 20.0 | General Adult (fallback) | **VERIFIED** | WHO Haemoglobin Guidelines; Tietz 4e |
| 5 | Serum Creatinine (Male) | `Serum Creatinine` | `mg/dL` | 0.7 – 1.3 | None | None | Adult Male (`M`) | **VERIFIED** | National Kidney Foundation KDIGO; American Kidney Fund; Tietz 6e |
| 6 | Serum Creatinine (Female) | `Serum Creatinine` | `mg/dL` | 0.6 – 1.1 | None | None | Adult Female (`F`) | **VERIFIED** | National Kidney Foundation KDIGO; American Kidney Fund; Tietz 6e |
| 7 | Serum Creatinine (General) | `Serum Creatinine` | `mg/dL` | 0.6 – 1.3 | None | None | General Adult (fallback) | **VERIFIED** | National Kidney Foundation KDIGO; American Kidney Fund; Tietz 6e |
| 8 | White Blood Cell Count | `White Blood Cell Count` | `cells/uL` | 4,000 – 11,000 | < 2,000 | > 30,000 | All adults | **VERIFIED** | Harrison's 21e; CAP Q-Probes Survey (Mayo lists >= 100,000) |
| 9 | Platelet Count | `Platelet Count` | `cells/uL` | 150,000 – 450,000 | < 50,000 | > 1,000,000 | All adults | **VERIFIED** | Harrison's 21e; Mayo Clinic Laboratories (<= 40,000, >= 1,000,000) |
| 10 | Serum Potassium | `Serum Potassium` | `mEq/L` | 3.5 – 5.0 | < 2.8 | > 6.2 | All adults (unhemolyzed) | **VERIFIED** | Tietz 6e; CAP Survey; Mayo Clinic (< 3.0, > 5.9 mmol/L) |
| 11 | Serum Sodium | `Serum Sodium` | `mEq/L` | 135.0 – 145.0 | < 120.0 | > 160.0 | All adults | **VERIFIED** | Tietz 6e; Mayo Clinic Laboratories (< 120, > 160 mmol/L) |
| 12 | Total Cholesterol | `Total Cholesterol` | `mg/dL` | 125.0 – 200.0 | None | None | All adults | **VERIFIED** | NCEP ATP III / American Heart Association (No acute critical values) |
| 13 | Blood Urea Nitrogen | `Blood Urea Nitrogen` | `mg/dL` | 7.0 – 20.0 | None | None | All adults | **VERIFIED** | Tietz 6e; Mayo Clinic (adult normal 6-21 mg/dL; acute panic criteria lab-specific) |
| 14 | Glycated Hemoglobin | `Glycated Hemoglobin` | `%` | 4.0 – 5.6 | None | None | All adults | **VERIFIED** | ADA Standards of Care (2024) (No acute critical values) |

### Key Audit Notes:
1. **Adult Creatinine Critical High**: In clinical literature (Mayo Clinic Laboratories Critical Values, CAP), there is **no single universally accepted adult critical cutoff** for creatinine. Chronic kidney disease patients frequently live with stable elevated levels, and acute kidney injury is diagnosed via rate-of-change (delta) or eGFR staging. In compliance with the safety directive (*"If a critical threshold cannot be reliably sourced, set it to None and do not invent one"*), `critical_high` for adult creatinine is set to `None`.
2. **Total Cholesterol & HbA1c**: Reflect chronic cardiovascular and long-term glycemic risk, not acute physiological collapse. They have **no acute critical panic thresholds** in laboratory medicine.
3. **Pending Lab-Specific Calibrations**:
   - *Pediatric Intervals*: Children and neonates have vastly different baselines (e.g., hemoglobin in neonates is 14–24 g/dL; alkaline phosphatase is elevated during bone growth). Marked as requiring lab-specific pediatric nomograms.
   - *Pregnancy-Specific Intervals*: Gestational hemodilution alters normal hemoglobin and fasting glucose ranges.
   - *Enzymatic Liver Panels* (ALT, AST, ALP): Dependent on laboratory incubation temperature (37°C vs. 30°C) and reagent formulations.

---

## 4. Deterministic Medical Value Extraction (`reference/parser.py`)

The `MedicalValueParser` extracts candidate clinical measurements from raw OCR lines using pure deterministic pattern matching:

### Supported Input Patterns
1. **Standard Separators**:
   - Colon: `"FBS: 92 mg/dL"`
   - Space: `"Fasting Blood Glucose 105 mg/dL"`
   - Hyphen: `"Hemoglobin - 11.5 g/dL"`
   - Equals: `"Creatinine = 1.0 mg/dL"`
   - Multi-space / Tabs: `"  \t Hb  :   14.2   g / dL  \t "`
2. **Number Formats**:
   - Standard integers: `92`, `8500`, `220000`
   - Comma thousands: `8,500`, `220,000`
   - Standard decimals: `92.0`, `14.2`, `1.25`
   - Leading decimals: `.95`, `.8`
3. **Unit Variations**:
   - Casing: `mg/dl`, `MG/DL`, `mg/dL`, `cells/ul`, `CELLS/UL`
   - Equivalents: `cells/cumm`, `/cumm`, `/uL`, `cells/uL`
   - Spacing: `14.2 g/dL`, `14.2g/dL`, `14.2  g / dL`
4. **Range-Text Segregation**:
   - Trailing ranges: `"Glucose 92 mg/dL 70-99"` $\to$ value: `92.0`, range: `"70-99"`
   - Parenthesized: `"Hemoglobin 14.2 g/dL (13.8-17.2)"` $\to$ value: `14.2`, range: `"(13.8-17.2)"`
   - Bracketed: `"Potassium: 4.2 mEq/L [3.5 - 5.0]"` $\to$ value: `4.2`, range: `"[3.5 - 5.0]"`
   - Inequality bound: `"Total Cholesterol: 190 mg/dL < 200"` $\to$ value: `190.0`, range: `"< 200"`
   - *Note: Printed ranges on OCR lines are captured for reference but NEVER automatically override the configured authoritative registry.*

### Ambiguity & Edge Case Policy
- **Multiple Unmatched Numbers**: If a line contains multiple numeric candidates outside of a recognized range (e.g., `"FBS: 92 105 mg/dL"`), the parser flags `ParserStatus.AMBIGUOUS` with confidence 0.5 and does **NOT** guess.
- **Missing Value**: `"Glucose: "` $\to$ `ParserStatus.VALUE_MISSING`.
- **Missing Unit**: `"Glucose 92"` $\to$ `ParserStatus.UNKNOWN_UNIT` (numeric value preserved).
- **Qualitative Results**: `"Glucose: Negative"`, `"HIV: Non-reactive"` $\to$ `ParserStatus.QUALITATIVE_RESULT` (preserved as text, never forced to float 0.0).
- **Unsupported Analytes**: `"UnknownEnzyme: 12.5 U/L"` $\to$ `ParserStatus.UNRECOGNIZED_ANALYTE`.
- **Zero Fuzzy Matching**: Typographical variations like `"Sodum"` or `"Potasium"` are rejected rather than incorrectly cross-mapped.

---

## 5. Usage Examples

### 1. Parsing a Single Line
```python
from reference import MedicalValueParser, ParserStatus

parser = MedicalValueParser()
parsed = parser.parse_line("FBS: 92 mg/dL (70-99)")

assert parsed.status == ParserStatus.SUCCESS
assert parsed.canonical_name == "Fasting Blood Glucose"
assert parsed.value == 92.0
assert parsed.normalized_unit == "mg/dL"
assert parsed.extracted_reference_range == "(70-99)"
```

### 2. End-to-End Pipeline (Text $\to$ Parser $\to$ Analyzer)
```python
from reference import MedicalValueParser, PatientContext

parser = MedicalValueParser()
report_text = """
1. Fasting Blood Glucose: 110 mg/dL
2. Hb: 10.5 g/dL (12.1-15.1)
3. Platelet Count: 220,000 /uL
"""

# Process with female demographic context
results = parser.parse_and_analyze(report_text, context=PatientContext(sex="F"))

for parsed, analysis in results:
    print(f"{analysis.canonical_name}: {analysis.numeric_value} {analysis.unit} -> {analysis.classification}")
# Output:
# Fasting Blood Glucose: 110.0 mg/dL -> HIGH
# Hemoglobin: 10.5 g/dL -> LOW
# Platelet Count: 220000.0 /uL -> NORMAL
```

---

## 6. FastAPI API & Database Integration (Step 3)

The reference engine is integrated directly into the FastAPI backend with database persistence and a user verification safety gate:

```
FastAPI Router (`backend/app/api/reference.py`)
       ↓
ReferenceService (`backend/app/services/reference_service.py`)
       ↓
MedicalValueParser / ReferenceAnalyzer (`reference/`)
       ↓
SQLite Database (`backend/app/models/models.py` -> `TestResult`)
```

### Endpoints

#### 1. `POST /api/v1/reference/analyze`
Evaluates structured laboratory measurements deterministically.
- **Request**:
  ```json
  {
    "measurements": [
      {
        "test_name": "FBS",
        "value": 92.0,
        "unit": "mg/dL",
        "is_user_verified": true
      }
    ],
    "context": {"sex": "M", "age": 45},
    "report_id": 1,
    "persist": false
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "total_submitted": 1,
    "total_classified": 1,
    "report_id": null,
    "results": [
      {
        "original_test_name": "FBS",
        "canonical_name": "Fasting Blood Glucose",
        "numeric_value": 92.0,
        "original_value_text": "92.0",
        "unit": "mg/dL",
        "normalized_unit": "mg/dL",
        "classification": "NORMAL",
        "analysis_status": "SUCCESS",
        "reference_range": {
          "canonical_name": "Fasting Blood Glucose",
          "unit": "mg/dL",
          "normal_low": 70.0,
          "normal_high": 99.0,
          "critical_low": 50.0,
          "critical_high": 400.0,
          "source": "American Diabetes Association (ADA) 2024 / Mayo Clinic Laboratories",
          "citation": "Diabetes Care 2024;47(Suppl. 1):S20-S42; Mayo Clinic Laboratories Critical Values",
          "reference_type": "GENERAL_REFERENCE",
          "verification_status": "VERIFIED"
        },
        "reference_source": "American Diabetes Association (ADA) 2024 / Mayo Clinic Laboratories",
        "is_user_verified": true,
        "persisted_test_result_id": null,
        "warnings": [],
        "disclaimer": "This is not a medical diagnosis. Please consult a qualified healthcare professional."
      }
    ],
    "disclaimer": "This is not a medical diagnosis. Please consult a qualified healthcare professional."
  }
  ```

#### 2. `POST /api/v1/reference/parse-and-analyze`
Extracts measurements from raw report text via `MedicalValueParser` and evaluates each deterministically via `ReferenceAnalyzer`.
- **Request**:
  ```json
  {
    "text": "FBS: 92 mg/dL\nHemoglobin: 14.2 g/dL\nWBC: 8500 cells/uL",
    "context": {"sex": "M"},
    "is_user_verified": false,
    "report_id": null,
    "persist": false
  }
  ```
- **Response**: Array of `items` containing both `parsed_analyte`, `parser_status`, and embedded `analysis`.

### Persistence & Verification Gate Policy
- **Analysis-Only by Default**: Calls with `persist=false` perform in-memory evaluation without touching SQLite.
- **Report Association**: When `persist=true`, `report_id` is mandatory and verified against the `reports` table. If omitted, returns HTTP 400; if report is not found, returns HTTP 404.
- **Verification Gate**: Raw parser extractions default to `is_user_verified=false` (`0` in DB). Unverified OCR measurements are never stored or represented as verified clinical data until confirmed by the user.

### Database Mapping (`TestResult`)
The existing Phase 2 `test_results` table is extended with three nullable audit columns:
- `canonical_name` (String(255), nullable): Audited clinical name.
- `reference_source` (String(255), nullable): Authoritative source organization.
- `analysis_status` (String(50), nullable): Status code (`SUCCESS`, `UNIT_MISMATCH`, etc.).
Existing Phase 2 schema and 7-table layout remain 100% backward-compatible.

---

## 7. Verification & Test Coverage

The test suite contains **92 dedicated Phase 6 tests** across three test modules:
- `tests/test_phase6_reference.py` (40 tests): Classification categories, exact boundaries, context resolution, non-critical limits, and safety disclaimers.
- `tests/test_phase6_parser.py` (32 tests): Standard formats 1–11, decimals (.95), separators, range-text segregation, ambiguity handling, noise tolerance, and end-to-end pipeline.
- `backend/tests/test_phase6_api.py` (20 tests): FastAPI endpoints, normal/low/high/critical, boundary tests, unit mismatch, missing/invalid values, demographic context, multi-line parser pipeline, ambiguous lines, qualitative results, disclaimers, HTTP 422, SQLite persistence, report linking, and verification gate distinction.

```text
======================= 165 passed, 1 warning in 6.95s =======================
```
All 73 previous regression tests (Phases 2–5) continue to pass.
