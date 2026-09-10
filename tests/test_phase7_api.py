"""
MedIntel AI — Phase 7 Step 4: FastAPI ML Integration Tests.

Verifies:
1. Diabetes risk endpoint (POST /api/v1/ml/diabetes-risk)
2. Heart disease risk endpoint (POST /api/v1/ml/heart-risk)
3. Chronic kidney disease risk endpoint (POST /api/v1/ml/kidney-risk)
4. Successful probability range in [0.0, 1.0]
5. Positive-class probability semantics
6. Risk-band calculation (LOW, MODERATE, ELEVATED)
7. Missing-feature rejection with INSUFFICIENT_FEATURES
8. Insufficient features response fields (risk_probability=None, missing_features listed)
9. Unverified-input rejection (is_user_verified=False -> VERIFICATION_REQUIRED)
10. Invalid numeric input rejection (HTTP 422)
11. NaN / Inf rejection (HTTP 422)
12. Unknown categorical tolerance (handle_unknown='ignore' -> HTTP 200 OK)
13. Model loading and in-memory caching behavior
14. SHA-256 cryptographic integrity validation
15. Missing artifact handling (HTTP 500 error with descriptive message)
16. ML status / health check endpoint (GET /api/v1/ml/status)
17. Database persistence of predictions into SQLite predictions table
18. Persistence error on non-existent report_id (HTTP 404)
19. Non-diagnostic safety disclaimer presence and terminology audit
20. Backward compatibility with Phase 6 reference analysis endpoint
"""

import copy
import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure repository root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import Base, get_db
from app.main import app
from app.models.models import Prediction, Report, User
from app.services.ml_risk_service import MLRiskService, ml_risk_service
from ml.common.schemas import MANDATORY_ML_DISCLAIMER


@pytest.fixture
def test_client_and_db(tmp_path):
    """Create an isolated test client with a fresh temporary SQLite database."""
    db_path = tmp_path / "test_phase7_api.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    # Seed sample user and report
    seed_session = TestingSessionLocal()
    user = User(name="Test Patient", email="patient@example.com", language_preference="english")
    seed_session.add(user)
    seed_session.flush()

    report = Report(
        user_id=user.id,
        file_name="sample_lab.pdf",
        file_path="/data/sample_lab.pdf",
        file_type="pdf",
        document_type="lab_report",
        extraction_method="pdfplumber",
    )
    seed_session.add(report)
    seed_session.commit()
    report_id = report.id
    seed_session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, report_id, TestingSessionLocal

    app.dependency_overrides.clear()


# =====================================================================
# Valid Test Feature Payloads
# =====================================================================

VALID_DIABETES_PAYLOAD = {
    "Pregnancies": 1,
    "Glucose": 100,
    "BloodPressure": 70,
    "SkinThickness": 20,
    "Insulin": 80,
    "BMI": 25.0,
    "DiabetesPedigreeFunction": 0.5,
    "Age": 30,
    "is_user_verified": True,
}

VALID_HEART_PAYLOAD = {
    "age": 55,
    "sex": 1,
    "cp": 2,
    "trestbps": 130,
    "chol": 240,
    "fbs": 0,
    "restecg": 0,
    "thalach": 150,
    "exang": 0,
    "oldpeak": 1.0,
    "slope": 1,
    "ca": 0,
    "thal": 3,
    "is_user_verified": True,
}

VALID_CKD_PAYLOAD = {
    "age": 45,
    "bp": 80,
    "sg": 1.020,
    "al": 0,
    "su": 0,
    "rbc": "normal",
    "pc": "normal",
    "pcc": "notpresent",
    "ba": "notpresent",
    "bgr": 100,
    "bu": 25,
    "sc": 0.9,
    "sod": 140,
    "pot": 4.2,
    "hemo": 15.0,
    "pcv": 45,
    "wc": 7500,
    "rc": 5.2,
    "htn": "no",
    "dm": "no",
    "cad": "no",
    "appet": "good",
    "pe": "no",
    "ane": "no",
    "is_user_verified": True,
}


# =====================================================================
# Test Cases
# =====================================================================

def test_1_diabetes_risk_endpoint(test_client_and_db):
    """1. POST /api/v1/ml/diabetes-risk returns HTTP 200 with valid structure."""
    client, _, _ = test_client_and_db
    response = client.post("/api/v1/ml/diabetes-risk", json=VALID_DIABETES_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["condition"] == "diabetes"
    assert data["status"] == "OK"
    assert isinstance(data["risk_probability"], float)
    assert data["risk_band"] in {"LOW", "MODERATE", "ELEVATED"}
    assert data["required_features_count"] == 8
    assert data["supplied_features_count"] == 8


def test_2_heart_risk_endpoint(test_client_and_db):
    """2. POST /api/v1/ml/heart-risk returns HTTP 200 with valid structure."""
    client, _, _ = test_client_and_db
    response = client.post("/api/v1/ml/heart-risk", json=VALID_HEART_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["condition"] == "heart_disease"
    assert data["status"] == "OK"
    assert isinstance(data["risk_probability"], float)
    assert data["risk_band"] in {"LOW", "MODERATE", "ELEVATED"}
    assert data["required_features_count"] == 13
    assert data["supplied_features_count"] == 13


def test_3_kidney_risk_endpoint(test_client_and_db):
    """3. POST /api/v1/ml/kidney-risk returns HTTP 200 with valid structure."""
    client, _, _ = test_client_and_db
    response = client.post("/api/v1/ml/kidney-risk", json=VALID_CKD_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["condition"] == "kidney_disease"
    assert data["status"] == "OK"
    assert isinstance(data["risk_probability"], float)
    assert data["risk_band"] in {"LOW", "MODERATE", "ELEVATED"}
    assert data["required_features_count"] == 24
    assert data["supplied_features_count"] == 24


def test_4_successful_probability_range(test_client_and_db):
    """4. Predicted probabilities strictly lie within [0.0, 1.0]."""
    client, _, _ = test_client_and_db
    for ep, payload in [
        ("/api/v1/ml/diabetes-risk", VALID_DIABETES_PAYLOAD),
        ("/api/v1/ml/heart-risk", VALID_HEART_PAYLOAD),
        ("/api/v1/ml/kidney-risk", VALID_CKD_PAYLOAD),
    ]:
        resp = client.post(ep, json=payload)
        assert resp.status_code == 200
        prob = resp.json()["risk_probability"]
        assert 0.0 <= prob <= 1.0


def test_5_positive_class_probability_semantics(test_client_and_db):
    """5. Positive-class probability increases with higher risk indicators."""
    client, _, _ = test_client_and_db
    # Low glucose vs high glucose in diabetes
    low_glucose = copy.deepcopy(VALID_DIABETES_PAYLOAD)
    low_glucose["Glucose"] = 80
    resp_low = client.post("/api/v1/ml/diabetes-risk", json=low_glucose)

    high_glucose = copy.deepcopy(VALID_DIABETES_PAYLOAD)
    high_glucose["Glucose"] = 195
    resp_high = client.post("/api/v1/ml/diabetes-risk", json=high_glucose)

    assert resp_high.json()["risk_probability"] > resp_low.json()["risk_probability"]


def test_6_risk_band_calculation(test_client_and_db):
    """6. Risk bands correspond to display boundaries (<0.30 LOW, 0.30-0.70 MODERATE, >=0.70 ELEVATED)."""
    client, _, _ = test_client_and_db
    resp = client.post("/api/v1/ml/diabetes-risk", json=VALID_DIABETES_PAYLOAD)
    data = resp.json()
    p = data["risk_probability"]
    band = data["risk_band"]
    if p < 0.30:
        assert band == "LOW"
    elif p < 0.70:
        assert band == "MODERATE"
    else:
        assert band == "ELEVATED"


def test_7_missing_feature_rejection(test_client_and_db):
    """7. Missing a required feature returns HTTP 200 with status INSUFFICIENT_FEATURES."""
    client, _, _ = test_client_and_db
    incomplete = copy.deepcopy(VALID_DIABETES_PAYLOAD)
    del incomplete["Glucose"]

    resp = client.post("/api/v1/ml/diabetes-risk", json=incomplete)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "INSUFFICIENT_FEATURES"


def test_8_insufficient_features_response(test_client_and_db):
    """8. INSUFFICIENT_FEATURES returns risk_probability=None and identifies missing fields."""
    client, _, _ = test_client_and_db
    incomplete = copy.deepcopy(VALID_HEART_PAYLOAD)
    del incomplete["chol"]
    del incomplete["thalach"]

    resp = client.post("/api/v1/ml/heart-risk", json=incomplete)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "INSUFFICIENT_FEATURES"
    assert data["risk_probability"] is None
    assert data["risk_band"] is None
    assert "chol" in data["missing_features"]
    assert "thalach" in data["missing_features"]


def test_9_unverified_input_rejection(test_client_and_db):
    """9. is_user_verified=False triggers safety hold with status VERIFICATION_REQUIRED."""
    client, _, _ = test_client_and_db
    unverified = copy.deepcopy(VALID_CKD_PAYLOAD)
    unverified["is_user_verified"] = False

    resp = client.post("/api/v1/ml/kidney-risk", json=unverified)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "VERIFICATION_REQUIRED"
    assert data["risk_probability"] is None
    assert data["risk_band"] is None


def test_10_invalid_numeric_input_rejection(test_client_and_db):
    """10. Passing a string in a numeric field returns HTTP 422."""
    client, _, _ = test_client_and_db
    bad_payload = copy.deepcopy(VALID_DIABETES_PAYLOAD)
    bad_payload["Glucose"] = "not_a_number"

    resp = client.post("/api/v1/ml/diabetes-risk", json=bad_payload)
    assert resp.status_code == 422


def test_11_nan_inf_rejection(test_client_and_db):
    """11. NaN and Inf values are rejected with HTTP 422."""
    client, _, _ = test_client_and_db
    nan_payload = copy.deepcopy(VALID_DIABETES_PAYLOAD)
    nan_payload["Glucose"] = "NaN"

    resp = client.post("/api/v1/ml/diabetes-risk", json=nan_payload)
    assert resp.status_code == 422

    inf_payload = copy.deepcopy(VALID_DIABETES_PAYLOAD)
    inf_payload["Glucose"] = "Infinity"
    resp_inf = client.post("/api/v1/ml/diabetes-risk", json=inf_payload)
    assert resp_inf.status_code == 422


def test_12_unknown_categorical_behavior(test_client_and_db):
    """12. Unknown categorical value is safely handled without throwing an error."""
    client, _, _ = test_client_and_db
    payload = copy.deepcopy(VALID_CKD_PAYLOAD)
    payload["rbc"] = "unknown_category_xyz"

    resp = client.post("/api/v1/ml/kidney-risk", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "OK"
    assert 0.0 <= resp.json()["risk_probability"] <= 1.0


def test_13_model_loading_and_caching(test_client_and_db):
    """13. MLRiskService caches predictors in memory and reuses them."""
    pred1 = ml_risk_service.get_predictor("diabetes")
    pred2 = ml_risk_service.get_predictor("diabetes")
    assert pred1 is pred2


def test_14_sha_integrity_validation(tmp_path):
    """14. Tampered model artifact triggers cryptographic integrity failure (HTTP 500)."""
    # Create mock corrupted model directory
    mock_dir = tmp_path / "corrupted_models" / "diabetes"
    mock_dir.mkdir(parents=True)
    pipe_file = mock_dir / "pipeline.joblib"
    meta_file = mock_dir / "model_metadata.json"

    pipe_file.write_bytes(b"tampered dummy model binary data")
    meta_file.write_text(json.dumps({"pipeline_sha256": "expected_valid_sha256_hash"}), encoding="utf-8")

    corrupted_service = MLRiskService(models_dir=str(tmp_path / "corrupted_models"))
    with pytest.raises(Exception) as exc_info:
        corrupted_service.get_predictor("diabetes")
    assert exc_info.value.status_code == 500


def test_15_missing_artifact_handling(tmp_path):
    """15. Missing artifact directory raises HTTP 500."""
    empty_service = MLRiskService(models_dir=str(tmp_path / "empty_dir"))
    with pytest.raises(Exception) as exc_info:
        empty_service.get_predictor("diabetes")
    assert exc_info.value.status_code == 500


def test_16_ml_status_endpoint(test_client_and_db):
    """16. GET /api/v1/ml/status returns availability and integrity for all models."""
    client, _, _ = test_client_and_db
    resp = client.get("/api/v1/ml/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"OK", "DEGRADED"}
    assert "diabetes" in data["models"]
    assert "heart_disease" in data["models"]
    assert "kidney_disease" in data["models"]
    assert data["models"]["diabetes"]["available"] is True
    assert data["models"]["diabetes"]["integrity_verified"] is True


def test_17_database_persistence(test_client_and_db):
    """17. Providing report_id persists prediction record to the predictions table."""
    client, report_id, SessionFactory = test_client_and_db
    payload = copy.deepcopy(VALID_DIABETES_PAYLOAD)
    payload["report_id"] = report_id

    resp = client.post("/api/v1/ml/diabetes-risk", json=payload)
    assert resp.status_code == 200
    persisted_id = resp.json()["persisted_prediction_id"]
    assert persisted_id is not None

    # Verify directly in database
    session = SessionFactory()
    pred_row = session.query(Prediction).filter(Prediction.id == persisted_id).first()
    assert pred_row is not None
    assert pred_row.report_id == report_id
    assert pred_row.condition == "diabetes"
    assert pred_row.risk_score == resp.json()["risk_probability"]
    assert pred_row.disclaimer == MANDATORY_ML_DISCLAIMER
    session.close()


def test_18_persistence_error_on_missing_report(test_client_and_db):
    """18. Non-existent report_id returns HTTP 404."""
    client, _, _ = test_client_and_db
    payload = copy.deepcopy(VALID_DIABETES_PAYLOAD)
    payload["report_id"] = 999999

    resp = client.post("/api/v1/ml/diabetes-risk", json=payload)
    assert resp.status_code == 404


def test_19_safety_disclaimer_and_no_diagnostic_terms(test_client_and_db):
    """19. Responses enforce mandatory disclaimer and zero diagnostic declarations."""
    client, _, _ = test_client_and_db
    resp = client.post("/api/v1/ml/diabetes-risk", json=VALID_DIABETES_PAYLOAD)
    data = resp.json()
    assert data["disclaimer"] == MANDATORY_ML_DISCLAIMER
    assert "diagnosis" not in data["risk_band"].lower()
    assert "confirmed" not in data["status"].lower()


def test_20_existing_phase6_reference_api_still_works(test_client_and_db):
    """20. Phase 6 reference analysis endpoint continues to function independently."""
    client, _, _ = test_client_and_db
    meas_payload = {
        "measurements": [
            {"test_name": "Hemoglobin", "value": 14.2, "unit": "g/dL"}
        ],
        "is_user_verified": True,
    }
    resp = client.post("/api/v1/reference/analyze", json=meas_payload)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["classification"] == "NORMAL"
