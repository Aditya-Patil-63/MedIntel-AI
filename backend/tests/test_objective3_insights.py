"""
MedIntel AI — Objective 3 Comprehensive Insights & Analysis Test Suite.

Tests:
1. Automated Patient Details Extraction (Name, Age, Gender, Date, Lab).
2. Missing / Unreadable Fallback strictly to 'Not Available' (no hallucinated details).
3. Clinical Guidance Generation: Alert Messages, Possible Health Implications, Precautions.
4. Multilingual Support: English, Hindi, Marathi, Gujarati.
5. Structured 9-Column Medical Table data readiness.
6. Longitudinal Health Trends & Tracking across historical reports.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from reference.guidance import get_clinical_guidance
from reference.models import PatientContext, TestMeasurement
from reference.parser import MedicalValueParser, extract_patient_details
from reference.analyzer import ReferenceAnalyzer


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestPatientDetailsExtraction:
    """Verifies automated report metadata extraction and 'Not Available' fallback."""

    def test_full_patient_header_extraction(self):
        sample_report = """
        Metropolis Healthcare Pathology Laboratory
        Collection Date: 12/04/2024
        Patient Name: Ramesh K. Sharma
        Age / Sex: 52 Y / Male
        Referring Doctor: Dr. A. V. Patel, MD

        TEST DESCRIPTION           VALUE     UNIT     REFERENCE RANGE
        Fasting Blood Glucose      145       mg/dL    70 - 99
        Hemoglobin                 14.2      g/dL     13.8 - 17.2
        Serum Creatinine           1.0       mg/dL    0.7 - 1.3
        """
        details = extract_patient_details(sample_report)
        assert details.name == "Ramesh K. Sharma"
        assert details.age == 52.0
        assert details.age_display == "52 Y"
        assert details.gender == "Male"
        assert details.date == "12/04/2024"
        assert "Metropolis" in details.lab_name

    def test_missing_patient_details_fallback_to_not_available(self):
        """Zero guessing rule: unmentioned details must be strictly 'Not Available'."""
        sparse_report = """
        Fasting Blood Glucose: 110 mg/dL
        Serum Creatinine: 0.9 mg/dL
        """
        details = extract_patient_details(sparse_report)
        assert details.name == "Not Available"
        assert details.age is None
        assert details.age_display == "Not Available"
        assert details.gender == "Not Available"
        assert details.date == "Not Available"
        assert details.lab_name == "Not Available"

    def test_partial_patient_details(self):
        partial_report = """
        City Diagnostic Centre
        Date: 2024-05-18
        Name: Anita Desai
        WBC: 6500 cells/uL
        """
        details = extract_patient_details(partial_report)
        assert details.name == "Anita Desai"
        assert details.date == "2024-05-18"
        assert "City Diagnostic" in details.lab_name
        assert details.age is None
        assert details.age_display == "Not Available"
        assert details.gender == "Not Available"


class TestClinicalGuidanceEngine:
    """Verifies deterministic alert messages, implications, and precautions."""

    def test_glucose_high_guidance_english(self):
        alert, imp, prec = get_clinical_guidance(
            canonical_name="Fasting Blood Glucose",
            test_name="Fasting Blood Glucose",
            value=145.0,
            value_text="145",
            unit="mg/dL",
            classification="HIGH",
            reference_low=70.0,
            reference_high=99.0,
            language="en",
        )
        assert "elevated" in alert.lower() or "glucose" in alert.lower()
        assert "prediabetes" in imp.lower() or "insulin resistance" in imp.lower()
        assert "doctor" in prec.lower() or "hba1c" in prec.lower()

    def test_glucose_high_guidance_multilingual(self):
        for lang in ["hi", "mr", "gu"]:
            alert, imp, prec = get_clinical_guidance(
                canonical_name="Fasting Blood Glucose",
                test_name="Fasting Blood Glucose",
                value=145.0,
                value_text="145",
                unit="mg/dL",
                classification="HIGH",
                reference_low=70.0,
                reference_high=99.0,
                language=lang,
            )
            assert len(alert) > 5
            assert len(imp) > 5
            assert len(prec) > 5

    def test_hemoglobin_low_guidance(self):
        alert, imp, prec = get_clinical_guidance(
            canonical_name="Hemoglobin",
            test_name="Hb",
            value=9.5,
            value_text="9.5",
            unit="g/dL",
            classification="LOW",
            reference_low=12.0,
            reference_high=17.5,
            language="en",
        )
        assert "lower" in alert.lower() or "hemoglobin" in alert.lower()
        assert "anemia" in imp.lower() or "oxygen" in imp.lower()
        assert "iron" in prec.lower() or "doctor" in prec.lower()

    def test_normal_value_guidance(self):
        alert, imp, prec = get_clinical_guidance(
            canonical_name="Serum Creatinine",
            test_name="Serum Creatinine",
            value=0.9,
            value_text="0.9",
            unit="mg/dL",
            classification="NORMAL",
            reference_low=0.7,
            reference_high=1.3,
            language="en",
        )
        assert "normal" in alert.lower()
        assert "healthy" in imp.lower() or "filtration" in imp.lower()
        assert "routine" in prec.lower() or "maintain" in prec.lower()

    def test_critical_value_guidance(self):
        alert, imp, prec = get_clinical_guidance(
            canonical_name="White Blood Cell Count",
            test_name="WBC",
            value=35000.0,
            value_text="35000",
            unit="cells/uL",
            classification="CRITICAL",
            reference_low=4000.0,
            reference_high=11000.0,
            language="en",
        )
        assert "CRITICAL" in alert
        assert "urgent" in prec.lower() or "emergency" in prec.lower()

    def test_requires_review_guidance(self):
        alert, imp, prec = get_clinical_guidance(
            canonical_name=None,
            test_name="Custom Biomarker",
            value=42.0,
            value_text="42",
            unit="U/L",
            classification=None,
            reference_low=None,
            reference_high=None,
            language="en",
        )
        assert "review" in alert.lower() or "laboratory" in alert.lower()
        assert "physician" in prec.lower() or "doctor" in prec.lower() or "report" in prec.lower()


class TestParseAndAnalyzeAPIObjective3:
    """Tests the parse-and-analyze endpoint with Objective 3 fields."""

    def test_parse_and_analyze_returns_patient_details_and_guidance(self, client):
        text_payload = """
        Dr. Lal PathLabs
        Date: 15/06/2024
        Patient Name: Sunita Patel
        Age: 48 Y
        Gender: Female

        Fasting Blood Glucose: 160 mg/dL
        Hemoglobin: 11.0 g/dL
        Serum Creatinine: 0.8 mg/dL
        """
        response = client.post(
            "/api/v1/reference/parse-and-analyze",
            json={"text": text_payload, "is_user_verified": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Check patient details
        assert "patient_details" in data and data["patient_details"] is not None
        pt = data["patient_details"]
        assert pt["name"] == "Sunita Patel"
        assert pt["age"] == 48.0
        assert pt["gender"] == "Female"
        assert pt["date"] == "15/06/2024"
        assert "Dr. Lal" in pt["lab_name"]

        # Check guidance fields in items
        items = data["items"]
        assert len(items) >= 3
        for item in items:
            analysis = item.get("analysis")
            if analysis:
                assert "alert_message" in analysis
                assert "possible_health_implications" in analysis
                assert "precautions_and_next_steps" in analysis
                assert analysis["alert_message"] is not None
                assert analysis["possible_health_implications"] is not None
                assert analysis["precautions_and_next_steps"] is not None


class TestHealthTrendsTrackingAPI:
    """Tests the longitudinal trends endpoint across reports."""

    def test_trends_endpoint_returns_aggregated_metrics(self, client):
        import uuid
        unique = uuid.uuid4().hex[:8]
        user_email = f"tracker_{unique}@example.com"
        password = "SecurePassword123!"
        reg = client.post(
            "/api/v1/auth/register",
            json={"name": "Tracker User", "email": user_email, "password": password},
        )
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Save Report 1
        rep1_payload = {
            "document_name": "Report_May_2024.pdf",
            "reference_results": [
                {"test_name": "Fasting Blood Glucose", "value": 140.0, "unit": "mg/dL", "classification": "HIGH"},
                {"test_name": "Hemoglobin", "value": 13.5, "unit": "g/dL", "classification": "NORMAL"},
            ],
        }
        res1 = client.post("/api/v1/reports", json=rep1_payload, headers=headers)
        assert res1.status_code == 201

        # Save Report 2
        rep2_payload = {
            "document_name": "Report_June_2024.pdf",
            "reference_results": [
                {"test_name": "Fasting Blood Glucose", "value": 115.0, "unit": "mg/dL", "classification": "HIGH"},
                {"test_name": "Hemoglobin", "value": 14.0, "unit": "g/dL", "classification": "NORMAL"},
            ],
        }
        res2 = client.post("/api/v1/reports", json=rep2_payload, headers=headers)
        assert res2.status_code == 201

        # Query trends
        trends_res = client.get("/api/v1/reports/trends", headers=headers)
        assert trends_res.status_code == 200
        trends_data = trends_res.json()
        assert trends_data["total_reports"] >= 2
        assert "Fasting Blood Glucose" in trends_data["trends"]
        glucose_history = trends_data["trends"]["Fasting Blood Glucose"]
        assert len(glucose_history) == 2
        assert glucose_history[0]["value"] == 140.0
        assert glucose_history[1]["value"] == 115.0
