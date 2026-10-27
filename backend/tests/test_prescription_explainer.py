"""
MedIntel AI — Unit and Integration Tests for Prescription & Medicine Explainer.

Objective 2: Helping patients understand what the doctor has prescribed,
including the medicines, their purpose, and how they should be taken.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.prescription import MANDATORY_PRESCRIPTION_DISCLAIMER


@pytest.fixture
def client() -> TestClient:
    """Create a test client for FastAPI application."""
    return TestClient(app)


class TestPrescriptionExplainer:
    """Tests for the Prescription & Medicine Explainer endpoint and service."""

    def test_explain_common_medicines_english(self, client: TestClient):
        """Verify explanation of chronic medications in English."""
        payload = {
            "medicines": ["Metformin 500mg", "Amlodipine 5mg", "Atorvastatin 20mg"],
            "language": "english",
            "is_user_verified": True,
        }
        res = client.post("/api/v1/prescriptions/explain", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["language"] == "english"
        assert len(data["medicines"]) == 3

        # Check Metformin
        metformin = data["medicines"][0]
        assert "Metformin" in metformin["name"]
        assert "blood sugar" in metformin["purpose"].lower()
        assert metformin["dosage"] is not None
        assert metformin["when_to_take"] is not None
        assert metformin["needs_confirmation"] is False
        assert "after meals" in metformin["schedule"].lower() or "with" in metformin["schedule"].lower()

        # Check Amlodipine
        amlodipine = data["medicines"][1]
        assert "Amlodipine" in amlodipine["name"]
        assert "blood pressure" in amlodipine["purpose"].lower()
        assert amlodipine["when_to_take"] is not None
        assert amlodipine["needs_confirmation"] is False

        # Check Atorvastatin
        statin = data["medicines"][2]
        assert "Atorvastatin" in statin["name"]
        assert "cholesterol" in statin["purpose"].lower()
        assert statin["when_to_take"] is not None
        assert statin["needs_confirmation"] is False
        assert "night" in statin["schedule"].lower() or "dinner" in statin["schedule"].lower()

        # General advice and questions
        assert len(data["questions_for_doctor"]) >= 3
        assert data["disclaimer"] == MANDATORY_PRESCRIPTION_DISCLAIMER

    def test_explain_multilingual_hindi_marathi_gujarati(self, client: TestClient):
        """Verify accurate localized outputs across Indian regional languages."""
        # 1. Hindi test
        hi_res = client.post(
            "/api/v1/prescriptions/explain",
            json={"medicines": ["Pantoprazole 40mg"], "language": "hindi"},
        )
        assert hi_res.status_code == 200
        hi_data = hi_res.json()
        assert hi_data["language"] == "hindi"
        assert "एसिड" in hi_data["medicines"][0]["purpose"] or "पेट" in hi_data["medicines"][0]["purpose"]
        assert "खाली पेट" in hi_data["medicines"][0]["schedule"]

        # 2. Marathi test
        mr_res = client.post(
            "/api/v1/prescriptions/explain",
            json={"medicines": ["Pantoprazole 40mg"], "language": "marathi"},
        )
        assert mr_res.status_code == 200
        mr_data = mr_res.json()
        assert mr_data["language"] == "marathi"
        assert "उपाशीपोटी" in mr_data["medicines"][0]["schedule"]

        # 3. Gujarati test
        gu_res = client.post(
            "/api/v1/prescriptions/explain",
            json={"medicines": ["Pantoprazole 40mg"], "language": "gujarati"},
        )
        assert gu_res.status_code == 200
        gu_data = gu_res.json()
        assert gu_data["language"] == "gujarati"
        assert "ભૂખ્યા પેટે" in gu_data["medicines"][0]["schedule"]

    def test_explain_raw_prescription_text(self, client: TestClient):
        """Verify extraction and explanation from raw multi-line prescription text."""
        raw_prescription = (
            "Rx\n"
            "Tab. Paracetamol 650mg SOS\n"
            "Cap. Amoxicillin 500mg 1-0-1 x 5 days\n"
            "Tab. Levocetirizine 5mg at night\n"
        )
        res = client.post(
            "/api/v1/prescriptions/explain",
            json={"prescription_text": raw_prescription, "language": "english"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["medicines"]) == 3

        # Paracetamol fever/pain
        assert "Paracetamol" in data["medicines"][0]["name"]
        assert "pain" in data["medicines"][0]["purpose"].lower() or "fever" in data["medicines"][0]["purpose"].lower()

        # Amoxicillin antibiotic
        assert "Amoxicillin" in data["medicines"][1]["name"]
        assert "infection" in data["medicines"][1]["purpose"].lower() or "bacterial" in data["medicines"][1]["purpose"].lower()
        assert "course" in data["medicines"][1]["instructions"].lower()

        # Levocetirizine allergy
        assert "Levocetirizine" in data["medicines"][2]["name"]
        assert "allerg" in data["medicines"][2]["purpose"].lower()
        assert "night" in data["medicines"][2]["schedule"].lower()

    def test_fallback_for_unlisted_medication(self, client: TestClient):
        """Verify graceful fallback and safety confirmation flag for unlisted or customized medications."""
        res = client.post(
            "/api/v1/prescriptions/explain",
            json={"medicines": ["UnlistedHerbMed 100mg"], "language": "english"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["medicines"]) == 1
        med = data["medicines"][0]
        assert "Unlistedherbmed" in med["name"]
        assert "prescribed by your doctor" in med["purpose"].lower()
        assert med["when_to_take"] is not None
        assert med["needs_confirmation"] is True
        assert "pharmacist" in med["confidence_note"].lower() or "doctor" in med["confidence_note"].lower()
