"""
MedIntel AI — Phase 6 Integration Tests: Reference Analysis API & Database Persistence.

Tests verify:
    1. POST /api/v1/reference/analyze with normal result
    2. Low result
    3. High result
    4. Critical result
    5. Exact normal boundary inclusivity
    6. Unit mismatch handling (HTTP 200 with UNIT_MISMATCH status)
    7. Unsupported analyte handling (HTTP 200 with REFERENCE_NOT_AVAILABLE status)
    8. Missing value handling (HTTP 200 with VALUE_MISSING status)
    9. Invalid (negative) value handling (HTTP 200 with INVALID_VALUE status)
    10. Demographic context resolution (Male vs. Female Hb / Creatinine)
    11. POST /api/v1/reference/parse-and-analyze endpoint with multi-line report
    12. Ambiguous parser result (HTTP 200 with AMBIGUOUS parser status)
    13. Qualitative result parsing and classification
    14. Mandatory safety disclaimer on every response
    15. Strict non-diagnostic guarantee across all API responses
    16. Malformed request payload returns HTTP 422
    17. Database persistence of analyzed test results (persist=True)
    18. Report association with existing Report entity in SQLite database
    19. User verification safety gate (is_user_verified=0 vs 1)
    20. Persistence error handling (400 for missing report_id, 404 for non-existent report_id)
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.session import Base, get_db
from app.main import app
from app.models.models import Report, TestResult, User


@pytest.fixture
def test_db_session(tmp_path):
    """
    Isolated SQLite database fixture for integration testing.
    Creates a fresh database schema with a dummy user and report.
    """
    db_path = tmp_path / "test_ref_api.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    # Seed an initial user and report for persistence testing
    seed_db = TestingSessionLocal()
    user = User(name="Test Patient", email="test@example.com", language_preference="english")
    seed_db.add(user)
    seed_db.flush()

    report = Report(
        user_id=user.id,
        file_name="blood_test.pdf",
        file_path="/tmp/blood_test.pdf",
        file_type="pdf",
        document_type="lab_report",
        status="verified",
    )
    seed_db.add(report)
    seed_db.commit()
    seed_db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db_session) -> TestClient:
    """TestClient wired to isolated test database."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1-5. Classification Categories: Normal, Low, High, Critical, Boundary
# ---------------------------------------------------------------------------

class TestReferenceAnalyzeEndpoints:
    """Verifies POST /api/v1/reference/analyze."""

    def test_01_normal_result(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "FBS", "value": 90.0, "unit": "mg/dL"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["total_classified"] == 1
        item = data["results"][0]
        assert item["canonical_name"] == "Fasting Blood Glucose"
        assert item["classification"] == "NORMAL"
        assert item["analysis_status"] == "SUCCESS"
        assert item["reference_source"] is not None

    def test_02_low_result(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "FBS", "value": 60.0, "unit": "mg/dL"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["results"][0]
        assert item["classification"] == "LOW"

    def test_03_high_result(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "FBS", "value": 135.0, "unit": "mg/dL"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["results"][0]
        assert item["classification"] == "HIGH"

    def test_04_critical_result(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "Sodium", "value": 170.0, "unit": "mEq/L"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["results"][0]
        assert item["classification"] == "CRITICAL"

    def test_05_exact_normal_boundary_inclusivity(self, client: TestClient):
        # Fasting glucose normal interval is 70.0 - 99.0 mg/dL (inclusive)
        payload = {
            "measurements": [
                {"test_name": "FBS", "value": 70.0, "unit": "mg/dL"},
                {"test_name": "FBS", "value": 99.0, "unit": "mg/dL"},
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        items = res.json()["results"]
        assert items[0]["classification"] == "NORMAL"
        assert items[1]["classification"] == "NORMAL"


# ---------------------------------------------------------------------------
# 6-10. Edge Cases: Units, Unsupported, Missing, Invalid, Context
# ---------------------------------------------------------------------------

class TestAnalyzeEdgeCases:
    """Verifies edge cases, mismatches, and demographic context."""

    def test_06_unit_mismatch(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "Glucose", "value": 5.5, "unit": "mmol/L"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["results"][0]
        assert item["classification"] is None
        assert item["analysis_status"] == "UNIT_MISMATCH"
        assert any("automatic unit conversion is not enabled" in w.lower() for w in item["warnings"])

    def test_07_unsupported_analyte(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "UnknownEnzymeXYZ", "value": 45.0, "unit": "U/L"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["results"][0]
        assert item["classification"] is None
        assert item["analysis_status"] == "REFERENCE_NOT_AVAILABLE"

    def test_08_missing_value(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "Glucose", "value": None, "unit": "mg/dL"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["results"][0]
        assert item["analysis_status"] == "VALUE_MISSING"

    def test_09_invalid_negative_value(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "Glucose", "value": -10.0, "unit": "mg/dL"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["results"][0]
        assert item["analysis_status"] == "INVALID_VALUE"
        assert any("physiologically invalid" in w.lower() for w in item["warnings"])

    def test_10_demographic_context_resolution(self, client: TestClient):
        # Hb 13.0 g/dL is LOW for adult male (13.8-17.2) but NORMAL for female (12.1-15.1)
        payload = {
            "measurements": [
                {
                    "test_name": "Hb",
                    "value": 13.0,
                    "unit": "g/dL",
                    "context": {"sex": "M"},
                },
                {
                    "test_name": "Hb",
                    "value": 13.0,
                    "unit": "g/dL",
                    "context": {"sex": "F"},
                },
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        items = res.json()["results"]
        assert items[0]["classification"] == "LOW"
        assert items[1]["classification"] == "NORMAL"


# ---------------------------------------------------------------------------
# 11-15. Parse and Analyze Endpoint, Ambiguity, Qualitative, Safety
# ---------------------------------------------------------------------------

class TestParseAndAnalyzeEndpoint:
    """Verifies POST /api/v1/reference/parse-and-analyze."""

    def test_11_multiline_text_pipeline(self, client: TestClient):
        payload = {
            "text": (
                "METABOLIC PANEL\n"
                "FBS: 92 mg/dL (70-99)\n"
                "Hemoglobin: 14.2 g/dL\n"
                "WBC: 8500 cells/uL\n"
            ),
            "patient_context": {"sex": "M"},
        }
        res = client.post("/api/v1/reference/parse-and-analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["total_measurements_analyzed"] == 3
        items = data["items"]
        assert len(items) == 3
        assert items[0]["canonical_name"] == "Fasting Blood Glucose"
        assert items[0]["analysis"]["classification"] == "NORMAL"
        assert items[0]["extracted_reference_range"] == "(70-99)"

    def test_12_ambiguous_parser_result(self, client: TestClient):
        payload = {
            "text": "FBS: 92 105 mg/dL",
        }
        res = client.post("/api/v1/reference/parse-and-analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["items"][0]
        assert item["parser_status"] == "AMBIGUOUS"
        assert item["extraction_confidence"] == 0.5
        assert item["analysis"]["classification"] is None

    def test_13_qualitative_result(self, client: TestClient):
        payload = {
            "text": "Glucose: Negative",
        }
        res = client.post("/api/v1/reference/parse-and-analyze", json=payload)
        assert res.status_code == 200
        item = res.json()["items"][0]
        assert item["parser_status"] == "QUALITATIVE_RESULT"
        assert item["analysis"]["analysis_status"] == "QUALITATIVE_RESULT"
        assert item["analysis"]["classification"] is None

    def test_14_mandatory_disclaimer_presence(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "FBS", "value": 90.0, "unit": "mg/dL"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        data = res.json()
        expected = "This is not a medical diagnosis. Please consult a qualified healthcare professional."
        assert data["disclaimer"] == expected
        assert data["results"][0]["disclaimer"] == expected

    def test_15_strict_non_diagnostic_guarantee(self, client: TestClient):
        payload = {
            "measurements": [
                {"test_name": "FBS", "value": 550.0, "unit": "mg/dL"}
            ]
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        full_json = res.text.lower()
        forbidden_phrases = [
            "you have diabetes",
            "diabetes mellitus diagnosis",
            "you have kidney disease",
            "prescribe",
            "treatment recommendation",
        ]
        for phrase in forbidden_phrases:
            assert phrase not in full_json

    def test_16_malformed_request_returns_422(self, client: TestClient):
        # Missing required 'measurements' field
        res = client.post("/api/v1/reference/analyze", json={})
        assert res.status_code == 422

        # Malformed measurements type
        res2 = client.post("/api/v1/reference/analyze", json={"measurements": "not a list"})
        assert res2.status_code == 422


# ---------------------------------------------------------------------------
# 17-20. Database Persistence, Report Association, and Verification Gate
# ---------------------------------------------------------------------------

class TestDatabasePersistenceAndVerificationGate:
    """Verifies SQLite persistence, report linking, and verification safety gate."""

    def test_17_database_persistence(
        self,
        client: TestClient,
        test_db_session,
    ):
        session = test_db_session()
        report = session.query(Report).first()
        report_id = report.id
        session.close()

        payload = {
            "report_id": report_id,
            "persist": True,
            "measurements": [
                {
                    "test_name": "FBS",
                    "value": 95.0,
                    "unit": "mg/dL",
                    "is_user_verified": True,
                }
            ],
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        persisted_id = data["results"][0]["persisted_test_result_id"]
        assert persisted_id is not None

        verify_session = test_db_session()
        db_record = verify_session.query(TestResult).filter(TestResult.id == persisted_id).first()
        assert db_record is not None
        assert db_record.test_name == "FBS"
        assert db_record.canonical_name == "Fasting Blood Glucose"
        assert db_record.test_value == 95.0
        assert db_record.classification == "normal"
        assert "ADA" in db_record.reference_source
        assert db_record.analysis_status == "SUCCESS"
        verify_session.close()

    def test_18_report_association(
        self,
        client: TestClient,
        test_db_session,
    ):
        session = test_db_session()
        report = session.query(Report).first()
        report_id = report.id
        session.close()

        payload = {
            "report_id": report_id,
            "persist": True,
            "measurements": [
                {
                    "test_name": "Creatinine",
                    "value": 1.1,
                    "unit": "mg/dL",
                    "is_user_verified": True,
                }
            ],
        }
        res = client.post("/api/v1/reference/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["report_id"] == report_id

        verify_session = test_db_session()
        linked_results = verify_session.query(TestResult).filter(TestResult.report_id == report_id).all()
        assert len(linked_results) >= 1
        assert any(r.test_name == "Creatinine" for r in linked_results)
        verify_session.close()

    def test_19_verification_gate_distinction(self, client: TestClient):
        # Raw parse-and-analyze extractions default to unverified
        payload = {
            "text": "FBS: 92 mg/dL",
            "is_user_verified": False,
        }
        res = client.post("/api/v1/reference/parse-and-analyze", json=payload)
        assert res.status_code == 200
        analysis = res.json()["items"][0]["analysis"]
        assert analysis["is_user_verified"] is False

        # When caller explicitly sets verified (after user confirmation screen)
        payload_verified = {
            "text": "FBS: 92 mg/dL",
            "is_user_verified": True,
        }
        res_v = client.post("/api/v1/reference/parse-and-analyze", json=payload_verified)
        assert res_v.status_code == 200
        analysis_v = res_v.json()["items"][0]["analysis"]
        assert analysis_v["is_user_verified"] is True

    def test_20_persistence_error_handling(self, client: TestClient):
        # Persist requested without report_id -> 400
        payload_no_report = {
            "persist": True,
            "measurements": [
                {"test_name": "FBS", "value": 90.0, "unit": "mg/dL"}
            ],
        }
        res = client.post("/api/v1/reference/analyze", json=payload_no_report)
        assert res.status_code == 400
        assert "report_id is required" in res.json()["detail"].lower()

        # Persist requested with non-existent report_id -> 404
        payload_invalid_report = {
            "report_id": 99999,
            "persist": True,
            "measurements": [
                {"test_name": "FBS", "value": 90.0, "unit": "mg/dL"}
            ],
        }
        res_404 = client.post("/api/v1/reference/analyze", json=payload_invalid_report)
        assert res_404.status_code == 404
        assert "not found" in res_404.json()["detail"].lower()
