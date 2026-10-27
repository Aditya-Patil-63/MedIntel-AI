"""
MedIntel AI — Unit Tests for Authentication & User-Partitioned Reports.

Verifies:
1. User registration, password hashing, and token issuance.
2. Duplicate email prevention.
3. Login credential verification and rejection of invalid passwords.
4. Token authentication and /auth/me profile inspection.
5. Strict user-scoped isolation of medical report records:
   - User 1's reports are never visible to User 2.
   - User 2 cannot access or delete User 1's reports.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(app)


def test_user_registration_and_login(client: TestClient):
    """Verify user registration and subsequent login."""
    unique_suffix = uuid.uuid4().hex[:8]
    test_email = f"patient_alice_{unique_suffix}@example.com"
    test_password = "SecurePassword123!"

    # 1. Register Alice
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice Smith",
            "email": test_email,
            "password": test_password,
            "language_preference": "english",
        },
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["name"] == "Alice Smith"

    # 2. Reject duplicate email
    dup_res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice Duplicate",
            "email": test_email,
            "password": "AnotherPassword456",
        },
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Login with wrong password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_email,
            "password": "WrongPassword",
        },
    )
    assert bad_login.status_code == 401

    # 4. Login with correct password
    good_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_email,
            "password": test_password,
        },
    )
    assert good_login.status_code == 200
    login_data = good_login.json()
    token = login_data["access_token"]
    assert token

    # 5. Access /me endpoint
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == test_email


def test_user_reports_isolation(client: TestClient):
    """Verify that reports are strictly partitioned by authenticated user."""
    s1 = uuid.uuid4().hex[:8]
    s2 = uuid.uuid4().hex[:8]
    # Register User 1 (Bob)
    bob_res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bob Jones",
            "email": f"bob_jones_{s1}@example.com",
            "password": "PasswordBob123",
        },
    )
    assert bob_res.status_code == 201
    bob_token = bob_res.json()["access_token"]

    # Register User 2 (Charlie)
    charlie_res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Charlie Brown",
            "email": f"charlie_brown_{s2}@example.com",
            "password": "PasswordCharlie123",
        },
    )
    assert charlie_res.status_code == 201
    charlie_token = charlie_res.json()["access_token"]

    # Bob initially has 0 reports
    bob_reports_initial = client.get(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert bob_reports_initial.status_code == 200
    assert bob_reports_initial.json() == []

    # Bob saves Report 1
    bob_report_payload = {
        "id": "bob_report_001",
        "document_name": "Bob_Lab_Results.pdf",
        "created_at": "2026-10-18T10:00:00Z",
        "verified_measurement_count": 2,
        "reference_results": [
            {
                "test_name": "Fasting Blood Glucose",
                "value": 110.0,
                "unit": "mg/dL",
                "reference_low": 70.0,
                "reference_high": 99.0,
                "classification": "high",
            }
        ],
        "total_classified": 1,
        "disclaimer": "This is not a medical diagnosis.",
    }
    save_res = client.post(
        "/api/v1/reports",
        json=bob_report_payload,
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert save_res.status_code == 201

    # Bob checks reports: sees 1 report
    bob_reports = client.get(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert len(bob_reports.json()) == 1
    assert bob_reports.json()[0]["document_name"] == "Bob_Lab_Results.pdf"

    # Charlie checks reports: MUST BE 0 (strictly isolated!)
    charlie_reports = client.get(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {charlie_token}"},
    )
    assert len(charlie_reports.json()) == 0

    # Charlie attempts to delete Bob's report: must return 404 (unauthorized resource)
    del_res = client.delete(
        "/api/v1/reports/bob_report_001",
        headers={"Authorization": f"Bearer {charlie_token}"},
    )
    assert del_res.status_code == 404

    # Charlie saves their own report
    charlie_payload = {
        "id": "charlie_report_001",
        "document_name": "Charlie_Checkup.pdf",
        "created_at": "2026-10-18T11:00:00Z",
        "verified_measurement_count": 1,
        "reference_results": [],
        "total_classified": 0,
    }
    client.post(
        "/api/v1/reports",
        json=charlie_payload,
        headers={"Authorization": f"Bearer {charlie_token}"},
    )

    # Now Charlie sees 1 report (theirs), Bob still sees 1 report (theirs)
    charlie_reports_after = client.get(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {charlie_token}"},
    )
    assert len(charlie_reports_after.json()) == 1
    assert charlie_reports_after.json()[0]["document_name"] == "Charlie_Checkup.pdf"

    bob_reports_after = client.get(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert len(bob_reports_after.json()) == 1
    assert bob_reports_after.json()[0]["document_name"] == "Bob_Lab_Results.pdf"


def test_google_login(client: TestClient):
    """Verify Google login auto-creates new account and logs in existing account."""
    suffix = uuid.uuid4().hex[:8]
    google_email = f"google_user_{suffix}@gmail.com"
    google_id = f"gid_{suffix}"

    # 1. First time Google login (auto-provisions account)
    res1 = client.post(
        "/api/v1/auth/google",
        json={
            "email": google_email,
            "name": "Google Test User",
            "google_id": google_id,
            "language_preference": "english",
        },
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert "access_token" in data1
    token1 = data1["access_token"]
    assert data1["user"]["email"] == google_email
    assert data1["user"]["name"] == "Google Test User"

    # 2. Access /me with token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == google_email

    # 3. Subsequent Google login (reuses existing account)
    res2 = client.post(
        "/api/v1/auth/google",
        json={
            "email": google_email,
            "name": "Google Test User",
            "google_id": google_id,
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["user"]["id"] == data1["user"]["id"]
    assert "access_token" in data2
