"""
MedIntel AI — Phase 10: End-to-End System Integration & Cross-Subsystem Tests.

Comprehensive integration test suite validating the complete clinical workflow:
1. Health & Liveness Checks (Backend, ML pipelines, GenAI providers)
2. Synthetic PDF Ingestion -> Text Extraction (pdfplumber) -> Reference Parsing
3. User Verification Safety Gate Enforcement (Extracted vs. Verified)
4. Full Verified Pipeline: Reference Analysis + ML Risk Predictions + Multilingual GenAI Explanations
5. Zero-Imputation Safety on Incomplete Feature Sets (INSUFFICIENT_FEATURES)
6. Acute Critical Value Handling (CRITICAL classifications & alerts)
7. Edge-Case Ingestion Handling (Oversized >10MB, unsupported extensions, empty files)
8. End-to-End SQLite Database Persistence (Report, TestResult, Prediction, Summary)
9. Demographic Context Resolution (Sex-specific reference intervals)
10. Multilingual Translation & Clinical Invariance across English, Hindi, Marathi, and Gujarati
"""

import io
import math
import sys
from pathlib import Path
from typing import List, Optional
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure repository root and backend directory are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.models.models import Prediction, Report, Summary, TestResult, User
from app.schemas.genai import (
    GenAIExplainRequest,
    MANDATORY_GENAI_DISCLAIMER,
    MLRiskSummary,
    SupportedLanguage,
    VerifiedAnalyteSummary,
)
from ml.common.schemas import MANDATORY_ML_DISCLAIMER

STANDARD_MEDICAL_DISCLAIMER = "This is not a medical diagnosis. Please consult a qualified healthcare professional."


# ===================================================================
# Test Database Fixture & Client Setup
# ===================================================================

@pytest.fixture
def test_client_and_db(tmp_path):
    """Provide an isolated TestClient backed by a fresh temporary SQLite database."""
    db_path = tmp_path / "test_phase10_e2e.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed test user and report
    db = TestingSessionLocal()
    user = User(
        name="Integration Test Patient",
        email="patient@example.com",
        language_preference="en",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    report = Report(
        user_id=user.id,
        file_name="comprehensive_lab_report.pdf",
        file_path="/tmp/comprehensive_lab_report.pdf",
        file_type="pdf",
        document_type="lab_report",
        status="uploaded",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    user_id = user.id
    report_id = report.id
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with patch.object(settings, "GENAI_PROVIDER", "mock"):
        with TestClient(app) as client:
            yield {
                "client": client,
                "engine": engine,
                "session_factory": TestingSessionLocal,
                "user_id": user_id,
                "report_id": report_id,
            }

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ===================================================================
# Pure-Python Synthetic PDF Generator Helper
# ===================================================================

def make_synthetic_lab_pdf(text_lines: List[str]) -> bytes:
    """Generate a minimal valid PDF 1.4 byte sequence without external libraries."""
    stream_content = "BT\n/F1 12 Tf\n50 750 Td\n15 TL\n"
    for line in text_lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_content += f"({escaped}) '\n"
    stream_content += "ET\n"
    stream_bytes = stream_content.encode("latin1")

    objects = []
    # Obj 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    # Obj 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [4 0 R] /Count 1 >>\nendobj")
    # Obj 3: Font
    objects.append("3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
    # Obj 4: Page
    objects.append(
        "4 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 5 0 R /Resources << /Font << /F1 3 0 R >> >> >>\nendobj"
    )
    # Obj 5: Stream
    obj5_hdr = f"5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n"
    obj5_ftr = "\nendstream\nendobj"
    objects.append((obj5_hdr.encode("latin1"), stream_bytes, obj5_ftr.encode("latin1")))

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        if isinstance(obj, tuple):
            out.extend(obj[0])
            out.extend(obj[1])
            out.extend(obj[2])
        else:
            out.extend(obj.encode("latin1"))
        out.extend(b"\n")

    xref_offset = len(out)
    num_objects = len(offsets)
    out.extend(f"xref\n0 {num_objects}\n".encode("latin1"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("latin1"))
    out.extend(f"trailer\n<< /Size {num_objects} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1"))
    return bytes(out)


# ===================================================================
# Test Cases
# ===================================================================

def test_01_liveness_and_subsystem_health(test_client_and_db):
    """Verify system liveness and health checks across backend, ML, and GenAI."""
    client = test_client_and_db["client"]

    # 1. Root health check
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"
    assert r_health.json()["application"] == settings.APP_NAME

    # 2. ML status endpoint
    r_ml = client.get("/api/v1/ml/status")
    assert r_ml.status_code == 200
    ml_data = r_ml.json()
    assert "models" in ml_data
    assert "diabetes" in ml_data["models"]
    assert "heart_disease" in ml_data["models"]
    assert "kidney_disease" in ml_data["models"]

    # 3. GenAI status endpoint
    r_genai = client.get("/api/v1/genai/status")
    assert r_genai.status_code == 200
    genai_data = r_genai.json()
    assert genai_data["provider"] in ("mock", "gemini")
    assert genai_data["status"] == "OK"


def test_02_synthetic_pdf_extraction_to_reference_parsing(test_client_and_db):
    """Verify document upload -> OCR text extraction -> deterministic reference parsing."""
    client = test_client_and_db["client"]

    # Generate synthetic report with realistic clinical lines
    pdf_bytes = make_synthetic_lab_pdf([
        "METROPOLITAN DIAGNOSTICS LABORATORY",
        "PATIENT: Jane Doe (Age: 45, Sex: F)",
        "FASTING BLOOD SUGAR: 145 mg/dL",
        "HEMOGLOBIN: 14.5 g/dL",
        "SERUM CREATININE: 1.1 mg/dL",
        "TOTAL CHOLESTEROL: 235 mg/dL",
        "POTASSIUM: 4.5 mEq/L",
    ])

    # 1. Ingest via POST /api/v1/extract
    response = client.post(
        "/api/v1/extract",
        files={"file": ("lab_report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    extract_data = response.json()
    assert extract_data["filename"] == "lab_report.pdf"
    assert extract_data["total_pages"] == 1
    assert not extract_data["is_empty"] if "is_empty" in extract_data else extract_data["success"]
    assert STANDARD_MEDICAL_DISCLAIMER in extract_data["disclaimer"]

    extracted_text = extract_data["full_text"]
    assert "FASTING BLOOD SUGAR: 145 mg/dL" in extracted_text

    # 2. Parse extracted text via POST /api/v1/reference/parse-and-analyze
    r_parse = client.post(
        "/api/v1/reference/parse-and-analyze",
        json={"text": extracted_text, "patient_context": {"age": 45, "sex": "F"}},
    )
    assert r_parse.status_code == 200
    parse_data = r_parse.json()
    assert parse_data["success"] is True
    assert len(parse_data["items"]) >= 3
    assert STANDARD_MEDICAL_DISCLAIMER in parse_data["disclaimer"]


def test_03_user_verification_gate_enforcement(test_client_and_db):
    """Enforce non-negotiable safety gate: unverified measurements cannot trigger clinical analysis or AI summaries."""
    client = test_client_and_db["client"]

    # 1. Reference analysis: is_user_verified=False is preserved on result
    r_ref = client.post(
        "/api/v1/reference/analyze",
        json={
            "measurements": [
                {
                    "test_name": "Fasting Blood Glucose",
                    "value": 145.0,
                    "unit": "mg/dL",
                    "is_user_verified": False,
                }
            ]
        },
    )
    assert r_ref.status_code == 200
    ref_res = r_ref.json()
    assert ref_res["results"][0]["is_user_verified"] is False

    # 2. ML risk prediction: is_user_verified=False returns VERIFICATION_REQUIRED
    r_ml = client.post(
        "/api/v1/ml/diabetes-risk",
        json={
            "Glucose": 145.0,
            "BMI": 32.5,
            "Age": 45.0,
            "is_user_verified": False,
        },
    )
    assert r_ml.status_code == 200
    ml_res = r_ml.json()
    assert ml_res["status"] == "VERIFICATION_REQUIRED"
    assert ml_res["risk_probability"] is None

    # 3. GenAI explanation: is_user_verified=False returns VERIFICATION_REQUIRED
    r_genai = client.post(
        "/api/v1/genai/explain",
        json={
            "analytes": [
                {
                    "test_name": "Fasting Blood Glucose",
                    "value": 145.0,
                    "unit": "mg/dL",
                    "classification": "HIGH",
                }
            ],
            "ml_risks": [],
            "language": "en",
            "is_user_verified": False,
        },
    )
    assert r_genai.status_code == 200
    genai_res = r_genai.json()
    assert genai_res["status"] == "VERIFICATION_REQUIRED"
    assert genai_res["explanation"] is None or genai_res["explanation"] == ""


def test_04_full_verified_e2e_pipeline_with_multilingual_explanations(test_client_and_db):
    """Validate full verified pipeline from deterministic reference analysis, ML risk, to multilingual GenAI explanations."""
    client = test_client_and_db["client"]

    # 1. Verified Reference Analysis (POST /api/v1/reference/analyze)
    r_ref = client.post(
        "/api/v1/reference/analyze",
        json={
            "measurements": [
                {"test_name": "Fasting Blood Glucose", "value": 145.0, "unit": "mg/dL", "is_user_verified": True},
                {"test_name": "Hemoglobin", "value": 14.5, "unit": "g/dL", "is_user_verified": True},
                {"test_name": "Serum Creatinine", "value": 1.1, "unit": "mg/dL", "is_user_verified": True},
                {"test_name": "Total Cholesterol", "value": 240.0, "unit": "mg/dL", "is_user_verified": True},
            ],
            "patient_context": {"age": 45, "sex": "F"},
        },
    )
    assert r_ref.status_code == 200
    ref_data = r_ref.json()
    class_map = {r["original_test_name"]: r["classification"] for r in ref_data["results"]}
    assert class_map["Fasting Blood Glucose"] == "HIGH"
    assert class_map["Hemoglobin"] == "NORMAL"
    assert class_map["Serum Creatinine"] == "NORMAL"
    assert class_map["Total Cholesterol"] == "HIGH"

    # 2. ML Risk Prediction (POST /api/v1/ml/diabetes-risk)
    r_ml_diab = client.post(
        "/api/v1/ml/diabetes-risk",
        json={
            "Glucose": 145.0,
            "BloodPressure": 85.0,
            "BMI": 32.5,
            "Age": 45.0,
            "Pregnancies": 2.0,
            "SkinThickness": 25.0,
            "Insulin": 130.0,
            "DiabetesPedigreeFunction": 0.55,
            "is_user_verified": True,
        },
    )
    assert r_ml_diab.status_code == 200
    diab_data = r_ml_diab.json()
    assert diab_data["status"] == "OK"
    diab_prob = diab_data["risk_probability"]
    assert 0.0 <= diab_prob <= 1.0
    assert diab_data["risk_band"] in ("LOW", "MODERATE", "ELEVATED")
    assert MANDATORY_ML_DISCLAIMER in diab_data["disclaimer"]

    # 3. Multilingual GenAI Explanation Generation across English, Hindi, Marathi, Gujarati
    for lang in [SupportedLanguage.ENGLISH, SupportedLanguage.HINDI, SupportedLanguage.MARATHI, SupportedLanguage.GUJARATI]:
        r_genai = client.post(
            "/api/v1/genai/explain",
            json={
                "analytes": [
                    {
                        "test_name": "Fasting Blood Glucose",
                        "value": 145.0,
                        "unit": "mg/dL",
                        "classification": "HIGH",
                        "reference_low": 70.0,
                        "reference_high": 99.0,
                    },
                    {
                        "test_name": "Hemoglobin",
                        "value": 14.5,
                        "unit": "g/dL",
                        "classification": "NORMAL",
                        "reference_low": 12.0,
                        "reference_high": 16.0,
                    },
                ],
                "ml_risks": [
                    {
                        "condition": "diabetes",
                        "risk_probability": diab_prob,
                        "risk_band": diab_data["risk_band"],
                        "model_name": diab_data["model_name"],
                    }
                ],
                "language": lang.value,
                "is_user_verified": True,
            },
        )
        assert r_genai.status_code == 200
        genai_data = r_genai.json()
        assert genai_data["status"] == "SUCCESS"
        assert genai_data["language"] == lang.value
        assert MANDATORY_GENAI_DISCLAIMER in genai_data["disclaimer"]
        explanation = genai_data["explanation"]
        assert explanation is not None
        assert len(explanation["summary"]) > 20

        # Clinical Invariance: Check findings preserve test value and classification
        f_names = [f["analyte_name"] for f in explanation["findings"]]
        assert "Fasting Blood Glucose" in f_names
        glucose_finding = next(f for f in explanation["findings"] if f["analyte_name"] == "Fasting Blood Glucose")
        assert "145.0 mg/dL" in glucose_finding["observed_value"]
        assert glucose_finding["classification"] == "HIGH"

        # Risk indicator preservation
        risk_item = explanation["risk_explanations"][0]
        assert risk_item["condition"] == "diabetes"
        assert risk_item["model_probability"] == pytest.approx(diab_prob)

        # Translation check
        if lang != SupportedLanguage.ENGLISH:
            assert genai_data["translated_summary"] is not None


def test_05_insufficient_features_zero_imputation_safety(test_client_and_db):
    """Verify that incomplete feature sets yield INSUFFICIENT_FEATURES without fabricating or imputing missing data."""
    client = test_client_and_db["client"]

    # Submit Kidney disease request with only Age and BP, omitting all essential lab analytes
    r_kidney = client.post(
        "/api/v1/ml/kidney-risk",
        json={
            "age": 55.0,
            "bp": 80.0,
            "is_user_verified": True,
        },
    )
    assert r_kidney.status_code == 200
    kidney_data = r_kidney.json()
    assert kidney_data["status"] == "INSUFFICIENT_FEATURES"
    assert kidney_data["risk_probability"] is None
    assert len(kidney_data["missing_features"]) > 0

    # Ensure deterministic reference analysis is not blocked by missing ML features
    r_ref = client.post(
        "/api/v1/reference/analyze",
        json={
            "measurements": [
                {"test_name": "Fasting Blood Glucose", "value": 110.0, "unit": "mg/dL", "is_user_verified": True}
            ]
        },
    )
    assert r_ref.status_code == 200
    assert r_ref.json()["results"][0]["classification"] == "HIGH"


def test_06_acute_critical_value_alert_and_safety(test_client_and_db):
    """Verify acute critical values (CRITICAL) are flagged deterministically and communicated safely."""
    client = test_client_and_db["client"]

    # Critical high potassium (7.2 mEq/L) and critical low hemoglobin (5.0 g/dL)
    r_crit = client.post(
        "/api/v1/reference/analyze",
        json={
            "measurements": [
                {"test_name": "Potassium", "value": 7.2, "unit": "mEq/L", "is_user_verified": True},
                {"test_name": "Hemoglobin", "value": 5.0, "unit": "g/dL", "is_user_verified": True},
            ],
            "patient_context": {"sex": "F"},
        },
    )
    assert r_crit.status_code == 200
    crit_data = r_crit.json()
    pot_res = next(r for r in crit_data["results"] if r["original_test_name"] == "Potassium")
    hb_res = next(r for r in crit_data["results"] if r["original_test_name"] == "Hemoglobin")

    assert pot_res["classification"] in ("CRITICAL", "CRITICAL_HIGH")
    assert hb_res["classification"] in ("CRITICAL", "CRITICAL_LOW")

    # Pass to GenAI explanation
    r_genai = client.post(
        "/api/v1/genai/explain",
        json={
            "analytes": [
                {
                    "test_name": "Potassium",
                    "value": 7.2,
                    "unit": "mEq/L",
                    "classification": pot_res["classification"],
                    "reference_high": 5.0,
                }
            ],
            "ml_risks": [],
            "language": "en",
            "is_user_verified": True,
        },
    )
    assert r_genai.status_code == 200
    genai_res = r_genai.json()
    explanation = genai_res["explanation"]
    assert explanation is not None
    assert len(explanation["findings"]) >= 1
    assert any("potassium" in f["analyte_name"].lower() for f in explanation["findings"])
    assert MANDATORY_GENAI_DISCLAIMER in genai_res["disclaimer"]


def test_07_invalid_document_and_boundary_rejection(test_client_and_db):
    """Verify boundary rejections: oversized documents, unsupported extensions, and empty files."""
    client = test_client_and_db["client"]

    # 1. Unsupported extension (.exe)
    r_unsupported = client.post(
        "/api/v1/extract",
        files={"file": ("virus.exe", b"\x4d\x5a\x90\x00", "application/octet-stream")},
    )
    assert r_unsupported.status_code in (400, 422)

    # 2. Empty file
    r_empty = client.post(
        "/api/v1/extract",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert r_empty.status_code in (400, 422)

    # 3. Oversized file (> 10 MB)
    oversized_bytes = b" " * (10 * 1024 * 1024 + 1024)
    r_oversized = client.post(
        "/api/v1/extract",
        files={"file": ("oversized.pdf", io.BytesIO(oversized_bytes), "application/pdf")},
    )
    assert r_oversized.status_code in (400, 413, 422)


def test_08_end_to_end_sqlite_session_persistence(test_client_and_db):
    """Verify complete end-to-end SQLite session persistence across Report, TestResults, Predictions, and Summary."""
    client = test_client_and_db["client"]
    report_id = test_client_and_db["report_id"]
    session_factory = test_client_and_db["session_factory"]

    # 1. Persist reference analysis into SQLite
    r_ref = client.post(
        "/api/v1/reference/analyze",
        json={
            "measurements": [
                {"test_name": "Fasting Blood Glucose", "value": 130.0, "unit": "mg/dL", "is_user_verified": True}
            ],
            "report_id": report_id,
            "persist": True,
        },
    )
    assert r_ref.status_code == 200

    # 2. Persist ML prediction into SQLite
    r_ml = client.post(
        "/api/v1/ml/diabetes-risk",
        json={
            "Glucose": 130.0,
            "BloodPressure": 80.0,
            "BMI": 30.0,
            "Age": 45.0,
            "Pregnancies": 1.0,
            "SkinThickness": 20.0,
            "Insulin": 100.0,
            "DiabetesPedigreeFunction": 0.45,
            "is_user_verified": True,
            "report_id": report_id,
        },
    )
    assert r_ml.status_code == 200

    # 3. Persist GenAI explanation into SQLite
    r_genai = client.post(
        "/api/v1/genai/explain",
        json={
            "report_id": report_id,
            "persist": True,
            "analytes": [
                {
                    "test_name": "Fasting Blood Glucose",
                    "value": 130.0,
                    "unit": "mg/dL",
                    "classification": "HIGH",
                }
            ],
            "ml_risks": [
                {
                    "condition": "diabetes",
                    "risk_probability": 0.45,
                    "risk_band": "MODERATE",
                }
            ],
            "language": "en",
            "is_user_verified": True,
        },
    )
    assert r_genai.status_code == 200

    # 4. Verify in database
    db = session_factory()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        assert report is not None

        # Verify TestResults
        test_results = db.query(TestResult).filter(TestResult.report_id == report_id).all()
        assert len(test_results) >= 1
        assert test_results[0].test_name == "Fasting Blood Glucose"

        # Verify Predictions
        predictions = db.query(Prediction).filter(Prediction.report_id == report_id).all()
        assert len(predictions) >= 1
        assert predictions[0].condition == "diabetes"

        # Verify Summaries
        summaries = db.query(Summary).filter(Summary.report_id == report_id).all()
        assert len(summaries) >= 1
        assert summaries[0].language == "en"
        assert len(summaries[0].summary_text) > 0
    finally:
        db.close()


def test_09_backward_compatibility_and_demographic_context(test_client_and_db):
    """Verify demographic context changes deterministic classification (Male vs Female Hemoglobin)."""
    client = test_client_and_db["client"]

    # Male context: 13.5 g/dL is below adult male lower reference (13.8 g/dL) -> LOW
    r_male = client.post(
        "/api/v1/reference/analyze",
        json={
            "measurements": [
                {"test_name": "Hemoglobin", "value": 13.5, "unit": "g/dL", "is_user_verified": True}
            ],
            "patient_context": {"sex": "M", "age": 35},
        },
    )
    assert r_male.status_code == 200
    assert r_male.json()["results"][0]["classification"] == "LOW"

    # Female context: 13.5 g/dL is within adult female normal reference (12.1 - 15.1 g/dL) -> NORMAL
    r_female = client.post(
        "/api/v1/reference/analyze",
        json={
            "measurements": [
                {"test_name": "Hemoglobin", "value": 13.5, "unit": "g/dL", "is_user_verified": True}
            ],
            "patient_context": {"sex": "F", "age": 35},
        },
    )
    assert r_female.status_code == 200
    assert r_female.json()["results"][0]["classification"] == "NORMAL"
