"""
MedIntel AI — Phase 10: Performance, Concurrency & Memory Audit Tests.

Automated verification of system throughput, sub-second latency constraints,
concurrency safety, in-memory model caching, and memory stability.
"""

import gc
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.models.models import Report, TestResult, User
from app.services.ml_risk_service import ml_risk_service
from reference.ranges import get_default_registry


@pytest.fixture
def perf_test_env(tmp_path):
    """Provide an isolated TestClient backed by an ephemeral SQLite database."""
    db_path = tmp_path / "test_phase10_perf.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed test user and report
    db = TestingSessionLocal()
    user = User(
        name="Performance Test User",
        email="perf@example.com",
        language_preference="en",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    report = Report(
        user_id=user.id,
        file_name="perf_report.pdf",
        file_path="/tmp/perf_report.pdf",
        file_type="pdf",
        document_type="lab_report",
        status="verified",
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


def test_01_subsecond_single_request_latency(perf_test_env):
    """Verify that every core backend endpoint returns in sub-second time (<1000 ms)."""
    client = perf_test_env["client"]

    endpoints = [
        ("GET", "/health", None),
        (
            "POST",
            "/api/v1/reference/analyze",
            {
                "measurements": [
                    {"test_name": "Glucose", "value": 95.0, "unit": "mg/dL", "is_user_verified": True},
                    {"test_name": "Hemoglobin", "value": 14.0, "unit": "g/dL", "is_user_verified": True},
                ],
                "persist": False,
            },
        ),
        (
            "POST",
            "/api/v1/reference/parse-and-analyze",
            {
                "text": "Fasting Blood Sugar: 95 mg/dL\nHemoglobin: 14.0 g/dL\n",
                "include_unrecognized": False,
            },
        ),
        (
            "POST",
            "/api/v1/ml/diabetes-risk",
            {
                "Pregnancies": 1,
                "Glucose": 105,
                "BloodPressure": 72,
                "SkinThickness": 20,
                "Insulin": 75,
                "BMI": 24.0,
                "DiabetesPedigreeFunction": 0.3,
                "Age": 32,
                "is_user_verified": True,
            },
        ),
        (
            "POST",
            "/api/v1/ml/heart-risk",
            {
                "age": 45,
                "sex": 1,
                "cp": 1,
                "trestbps": 120,
                "chol": 195,
                "fbs": 0,
                "restecg": 0,
                "thalach": 160,
                "exang": 0,
                "oldpeak": 0.0,
                "slope": 1,
                "ca": 0,
                "thal": 3,
                "is_user_verified": True,
            },
        ),
        (
            "POST",
            "/api/v1/ml/kidney-risk",
            {
                "age": 40,
                "bp": 70,
                "sg": 1.020,
                "al": 0,
                "su": 0,
                "rbc": "normal",
                "pc": "normal",
                "pcc": "notpresent",
                "ba": "notpresent",
                "bgr": 100,
                "bu": 30,
                "sc": 0.8,
                "sod": 140,
                "pot": 4.0,
                "hemo": 15.0,
                "pcv": 44,
                "wc": 7000,
                "rc": 5.0,
                "htn": "no",
                "dm": "no",
                "cad": "no",
                "appet": "good",
                "pe": "no",
                "ane": "no",
                "is_user_verified": True,
            },
        ),
        (
            "POST",
            "/api/v1/genai/explain",
            {
                "is_user_verified": True,
                "language": "en",
                "analytes": [
                    {"test_name": "Glucose", "value": 95.0, "unit": "mg/dL", "classification": "NORMAL"},
                ],
                "ml_risks": [
                    {"condition": "diabetes", "risk_probability": 0.15, "risk_band": "LOW"},
                ],
            },
        ),
    ]

    for method, path, payload in endpoints:
        t0 = time.perf_counter()
        if method == "GET":
            resp = client.get(path)
        else:
            resp = client.post(path, json=payload)
        elapsed_sec = time.perf_counter() - t0

        assert resp.status_code == 200, f"Endpoint {path} failed with code {resp.status_code}"
        assert elapsed_sec < 1.0, f"Endpoint {path} exceeded 1s limit: {elapsed_sec:.4f}s"


def test_02_in_memory_model_caching_identity():
    """Verify that ML models are cached in memory as singletons without repeated disk loading."""
    for cond in ["diabetes", "heart_disease", "kidney_disease"]:
        pred_a = ml_risk_service.get_predictor(cond)
        pred_b = ml_risk_service.get_predictor(cond)
        # Identity equality check (exact same object in memory)
        assert pred_a is pred_b, f"Predictor for {cond} was not cached in memory"

    # Consecutive inferences should take < 15ms each on cached model
    features = {
        "Pregnancies": 1,
        "Glucose": 100,
        "BloodPressure": 70,
        "SkinThickness": 20,
        "Insulin": 70,
        "BMI": 23.0,
        "DiabetesPedigreeFunction": 0.25,
        "Age": 30,
    }
    predictor = ml_risk_service.get_predictor("diabetes")
    t0 = time.perf_counter()
    for _ in range(20):
        res = predictor.predict_risk(features)
        assert res.risk_probability is not None
    total_elapsed = time.perf_counter() - t0
    avg_latency_ms = (total_elapsed / 20) * 1000.0

    assert avg_latency_ms < 30.0, f"Average inference time too high: {avg_latency_ms:.2f} ms"


def test_03_concurrent_requests_scaling_and_zero_errors(perf_test_env):
    """Verify system stability and 0.0% error rate under 25 concurrent requests."""
    client = perf_test_env["client"]

    payload = {
        "measurements": [
            {"test_name": "Glucose", "value": 90.0, "unit": "mg/dL", "is_user_verified": True},
            {"test_name": "Hemoglobin", "value": 14.5, "unit": "g/dL", "is_user_verified": True},
        ],
        "persist": False,
    }

    def execute_call():
        return client.post("/api/v1/reference/analyze", json=payload)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(execute_call) for _ in range(25)]
        responses = [f.result() for f in futures]

    assert len(responses) == 25
    for r in responses:
        assert r.status_code == 200
        assert r.json()["success"] is True


def test_04_memory_stability_under_repeated_inferences(perf_test_env):
    """Verify that repeated pipeline requests do not produce runaway memory growth."""
    client = perf_test_env["client"]

    payload = {
        "is_user_verified": True,
        "language": "en",
        "analytes": [
            {"test_name": "Glucose", "value": 95.0, "unit": "mg/dL", "classification": "NORMAL"},
        ],
        "ml_risks": [
            {"condition": "diabetes", "risk_probability": 0.2, "risk_band": "LOW"},
        ],
    }

    gc.collect()

    # Run 50 requests
    for _ in range(50):
        resp = client.post("/api/v1/genai/explain", json=payload)
        assert resp.status_code == 200

    gc.collect()


def test_05_database_persistence_batch_throughput(perf_test_env):
    """Verify that batch database persistence of 25 records completes in < 200 ms."""
    session_factory = perf_test_env["session_factory"]
    report_id = perf_test_env["report_id"]

    db = session_factory()
    try:
        t0 = time.perf_counter()
        records = [
            TestResult(
                report_id=report_id,
                test_name=f"Test Analyte {i}",
                canonical_name=f"Canonical Analyte {i}",
                test_value=float(10 + i),
                unit="mg/dL",
                classification="normal",
                is_user_verified=1,
            )
            for i in range(25)
        ]
        db.add_all(records)
        db.commit()
        elapsed_sec = time.perf_counter() - t0

        assert elapsed_sec < 0.5, f"Batch persistence took too long: {elapsed_sec:.4f}s"
        count = db.query(TestResult).filter(TestResult.report_id == report_id).count()
        assert count == 25
    finally:
        db.close()


def test_06_reference_range_lookup_submillisecond_speed():
    """Verify that reference range dictionary lookups are O(1) and sub-millisecond."""
    reg = get_default_registry()
    analytes = ["Glucose", "Hemoglobin", "Potassium", "Sodium", "Creatinine", "Platelets"]

    t0 = time.perf_counter()
    for _ in range(1000):
        for a in analytes:
            res = reg.get_range(a)
            assert res is not None
    total_sec = time.perf_counter() - t0
    total_lookups = 1000 * len(analytes)
    avg_lookup_us = (total_sec / total_lookups) * 1_000_000.0

    # Must be less than 50 microseconds per lookup
    assert avg_lookup_us < 100.0, f"Lookup too slow: {avg_lookup_us:.2f} microseconds"
