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

    def test_prescription_header_and_doctor_advice_filtering(self, client: TestClient):
        """Verify clinic headers, doctor name, and patient info are filtered and advice is captured."""
        prescription_with_headers = (
            "Dr. Rajesh Sharma, MD\n"
            "Apollo Clinic, Mumbai\n"
            "Date: 27/10/2026\n"
            "Patient: Ramesh Kumar, Age: 52\n"
            "Rx\n"
            "1. Tab. Metformin 500mg 1-0-1 after food\n"
            "2. Tab. Telmisartan 40mg 1-0-0 morning\n"
            "Advice:\n"
            "- Low salt diet and brisk walk\n"
            "- Review in 15 days\n"
        )
        res = client.post(
            "/api/v1/prescriptions/explain",
            json={"prescription_text": prescription_with_headers, "language": "english"},
        )
        assert res.status_code == 200
        data = res.json()

        # Only the 2 actual medications should be in the medicines table
        assert len(data["medicines"]) == 2
        med_names = [m["name"].lower() for m in data["medicines"]]
        assert any("metformin" in name for name in med_names)
        assert any("telmisartan" in name for name in med_names)
        assert not any("apollo" in name for name in med_names)
        assert not any("ramesh" in name for name in med_names)

        # Advice should be extracted into doctor notes
        assert "doctor advice" in data["doctor_notes"].lower()
        assert "low salt" in data["doctor_notes"].lower()

    def test_dosage_extraction_from_line(self, client: TestClient):
        """Verify explicit dosage quantities (e.g. 1000mg, 650mg, 2 ml, 1 tablet) are extracted."""
        payload = {
            "medicines": [
                "Tab. Metformin 1000mg",
                "Syrup Paracetamol 5ml",
                "Tab. Atorvastatin 40mg",
            ],
            "language": "english",
        }
        res = client.post("/api/v1/prescriptions/explain", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert len(data["medicines"]) == 3
        # 1000mg extracted
        assert "1000" in data["medicines"][0]["dosage"]
        # 5ml extracted
        assert "5ml" in data["medicines"][1]["dosage"] or "5 ml" in data["medicines"][1]["dosage"]
        # 40mg extracted
        assert "40" in data["medicines"][2]["dosage"]

    def test_timing_schedule_patterns(self, client: TestClient):
        """Verify dosage timing codes (1-0-1, 1-0-0, 0-0-1, SOS) are formatted clearly for patients."""
        payload = {
            "medicines": [
                "Tab. Metformin 500mg 1-0-1 after food",
                "Tab. Amlodipine 5mg 1-0-0 morning",
                "Tab. Atorvastatin 20mg 0-0-1 night",
                "Tab. Paracetamol 650mg SOS",
            ],
            "language": "english",
        }
        res = client.post("/api/v1/prescriptions/explain", json=payload)
        assert res.status_code == 200
        data = res.json()

        # 1-0-1 -> Twice daily
        assert "twice" in data["medicines"][0]["when_to_take"].lower() or "1-0-1" in data["medicines"][0]["when_to_take"]
        # 1-0-0 -> Once daily morning
        assert "once" in data["medicines"][1]["when_to_take"].lower() or "1-0-0" in data["medicines"][1]["when_to_take"]
        # 0-0-1 -> Bedtime / Night
        assert "night" in data["medicines"][2]["when_to_take"].lower() or "bedtime" in data["medicines"][2]["when_to_take"].lower()
        # SOS -> As needed
        assert "sos" in data["medicines"][3]["when_to_take"].lower() or "as needed" in data["medicines"][3]["when_to_take"].lower()

    def test_ambiguous_or_unclear_handwriting_flags_confirmation(self, client: TestClient):
        """Verify ambiguous handwriting markers (? or 'unclear') trigger safety confirmation flag."""
        payload = {
            "medicines": [
                "Tab. Metformin 500mg",
                "Tab. UnclearMed? 2ml dose unclear",
            ],
            "language": "english",
        }
        res = client.post("/api/v1/prescriptions/explain", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert len(data["medicines"]) == 2
        # Clean metformin should not need confirmation
        assert data["medicines"][0]["needs_confirmation"] is False
        # Ambiguous medicine must need confirmation
        assert data["medicines"][1]["needs_confirmation"] is True
        assert data["medicines"][1]["confidence_note"] is not None

    def test_expanded_drug_catalog_brands(self, client: TestClient):
        """Verify common outpatient brand names resolve correctly without false safety flags."""
        brands = [
            "Dolo 650",
            "Augmentin 625",
            "Telma 40",
            "Pan 40",
            "Shelcal 500",
            "Thyronorm 50",
            "Rosuvas 10",
            "Ecosprin 75",
        ]
        res = client.post(
            "/api/v1/prescriptions/explain",
            json={"medicines": brands, "language": "english"},
        )
        assert res.status_code == 200
        data = res.json()

        assert len(data["medicines"]) == 8
        for med in data["medicines"]:
            # All 8 should be identified from knowledge base catalog
            assert med["needs_confirmation"] is False
            assert len(med["purpose"]) > 10
            assert med["when_to_take"] is not None
            assert med["dosage"] is not None

    def test_empty_and_whitespace_input_safety(self, client: TestClient):
        """Verify empty text or whitespace returns a safe fallback without crashing."""
        res = client.post(
            "/api/v1/prescriptions/explain",
            json={"prescription_text": "   \n\n  ", "language": "english"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["medicines"]) == 1
        assert data["medicines"][0]["needs_confirmation"] is True
        assert data["disclaimer"] == MANDATORY_PRESCRIPTION_DISCLAIMER

    def test_table_structure_guarantee(self, client: TestClient):
        """Ensure all 4 Objective 2 table columns exist and are non-empty for every row."""
        payload = {
            "medicines": ["Metformin 500mg", "Pantoprazole 40mg"],
            "language": "english",
        }
        res = client.post("/api/v1/prescriptions/explain", json=payload)
        assert res.status_code == 200
        data = res.json()

        for med in data["medicines"]:
            # Column 1: Medicine Name
            assert med["name"] and len(med["name"].strip()) > 0
            assert med["medicine_name"] and len(med["medicine_name"].strip()) > 0
            # Column 2: Purpose
            assert med["purpose"] and len(med["purpose"].strip()) > 0
            # Column 3: Dosage
            assert med["dosage"] and len(med["dosage"].strip()) > 0
            # Column 4: When to Take
            assert med["when_to_take"] and len(med["when_to_take"].strip()) > 0

