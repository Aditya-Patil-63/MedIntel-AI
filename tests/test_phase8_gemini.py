"""
MedIntel AI — Phase 8 Step 4: Real Gemini Provider Offline Test Suite.

Comprehensive offline unit and API integration tests validating GeminiProvider:
A. Configuration loads correctly without exposing the secret key
B. Mock provider remains fully functional
C. Unverified requests never call Gemini API
D. Verified requests dispatch cleanly to GeminiProvider with mocked SDK
E. Missing API key handling returns safe HTTP 503
F. Simulated timeout handling returns safe HTTP 504
G. Simulated Gemini API failure returns safe HTTP 500
H. Malformed structured output returns safe error
I. Upstream classifications and ML risks are strictly preserved (invariant)
J. Prompt injection attempts cannot violate medical non-diagnostic boundaries
K. Existing Phase 6/7 contracts remain invariant
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
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

from google.genai import errors, types

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.models.models import Report, User
from app.schemas.genai import (
    AnalyteExplanationItem,
    DetailLevel,
    GenAIExplainRequest,
    GenAIExplanationPayload,
    GenAIStatus,
    MANDATORY_GENAI_DISCLAIMER,
    MLRiskSummary,
    RiskExplanationItem,
    SupportedLanguage,
    VerifiedAnalyteSummary,
)
from app.services.genai.gemini_provider import GeminiProvider
from app.services.genai.mock_provider import MockGenAIProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_db_and_client(tmp_path):
    """Isolated SQLite test client for Gemini provider integration."""
    db_path = tmp_path / "test_phase8_gemini.db"
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
        status="verified",
    )
    seed_session.add(report)
    seed_session.commit()
    report_id = report.id
    user_id = user.id
    seed_session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, report_id, user_id, TestingSessionLocal

    app.dependency_overrides.clear()


@pytest.fixture
def sample_explain_request():
    """Standard verified request payload."""
    return GenAIExplainRequest(
        is_user_verified=True,
        patient_age=54.0,
        patient_sex="M",
        analytes=[
            VerifiedAnalyteSummary(
                test_name="Fasting Blood Glucose",
                canonical_name="glucose",
                value=140.0,
                unit="mg/dL",
                classification="HIGH",
                reference_low=70.0,
                reference_high=99.0,
                reference_source="ADA 2024",
                analysis_status="SUCCESS",
                warnings=[],
            )
        ],
        ml_risks=[
            MLRiskSummary(
                condition="diabetes",
                risk_probability=0.7450,
                risk_band="ELEVATED",
                model_name="RandomForest_d4_s8",
                model_version="1.0",
                status="OK",
            )
        ],
        language=SupportedLanguage.ENGLISH,
        detail_level=DetailLevel.SIMPLE,
        persist=False,
    )


@pytest.fixture
def mock_gemini_response_payload():
    """Valid JSON payload matching GenAIExplanationPayload schema."""
    return {
        "summary": "This educational report summarizes your recent laboratory tests and machine learning risk indicators. One lab value was elevated and one risk assessment showed elevated statistical probability. Please review these results with your healthcare provider.",
        "findings": [
            {
                "analyte_name": "glucose",
                "observed_value": "140.0 mg/dL",
                "classification": "HIGH",
                "plain_language_meaning": "Glucose is the primary fuel for body cells. An elevated fasting reading indicates higher than normal sugar in the bloodstream."
            }
        ],
        "risk_explanations": [
            {
                "condition": "diabetes",
                "model_probability": 0.7450,
                "risk_band": "ELEVATED",
                "plain_language_explanation": "The statistical model evaluated key markers including blood glucose, BMI, and age, indicating an elevated statistical risk profile."
            }
        ],
        "follow_up_guidance": [
            "Discuss these test results with your primary care physician.",
            "Bring your laboratory report to your next clinical consultation.",
            "Do not stop, start, or alter any medications without medical guidance."
        ],
        "recommended_questions_for_doctor": [
            "What do these fasting glucose results indicate about my health?",
            "Are repeat or follow-up laboratory tests recommended?",
            "What lifestyle or dietary modifications would be beneficial?"
        ]
    }


# ---------------------------------------------------------------------------
# Test A: Configuration Loads Correctly Without Printing Key
# ---------------------------------------------------------------------------

def test_a_gemini_config_loads_without_printing_key():
    """Verify Gemini configuration loaded without exposing raw secret key."""
    assert settings.GENAI_PROVIDER in {"mock", "gemini"}
    assert settings.GEMINI_MODEL == "gemini-3.8-flash"
    assert settings.GEMINI_TIMEOUT_SECONDS > 0
    assert settings.GEMINI_MAX_OUTPUT_TOKENS > 0

    # Ensure representation or str does not expose raw secret
    provider = GeminiProvider(api_key="mock_secret_key_12345")
    assert "mock_secret_key_12345" not in repr(provider)
    assert provider.provider_name == "gemini"
    assert provider.model_name == "gemini-3.8-flash"


# ---------------------------------------------------------------------------
# Test B: Mock Provider Tests Still Pass
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_b_mock_provider_still_works(sample_explain_request):
    """Verify MockGenAIProvider continues to operate completely offline."""
    mock_p = MockGenAIProvider()
    assert mock_p.provider_name == "mock"

    res = await mock_p.generate_explanation(sample_explain_request)
    assert isinstance(res, GenAIExplanationPayload)
    assert len(res.findings) == 1
    assert res.findings[0].observed_value == "140.0 mg/dL"
    assert res.findings[0].classification == "HIGH"
    assert res.risk_explanations[0].model_probability == 0.7450
    assert res.risk_explanations[0].risk_band == "ELEVATED"


# ---------------------------------------------------------------------------
# Test C: Unverified Requests Never Call Gemini
# ---------------------------------------------------------------------------

def test_c_unverified_request_never_calls_gemini(test_db_and_client, sample_explain_request):
    """Verify is_user_verified=False halts immediately without calling Gemini client."""
    client, _, _, _ = test_db_and_client
    payload = sample_explain_request.model_dump()
    payload["is_user_verified"] = False

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock()

    with patch.object(settings, "GENAI_PROVIDER", "gemini"), \
         patch("app.services.genai.gemini_provider.genai.Client", return_value=fake_client):
        resp = client.post("/api/v1/genai/explain", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "VERIFICATION_REQUIRED"
        assert data["explanation"] is None
        # Assert Gemini SDK was NEVER called
        fake_client.aio.models.generate_content.assert_not_called()


# ---------------------------------------------------------------------------
# Test D: Verified Request Dispatches to GeminiProvider
# ---------------------------------------------------------------------------

def test_d_verified_request_dispatches_to_gemini(test_db_and_client, sample_explain_request, mock_gemini_response_payload):
    """Verify verified request dispatches to GeminiProvider with mocked SDK client."""
    client, _, _, _ = test_db_and_client
    payload = sample_explain_request.model_dump()

    fake_response = MagicMock()
    fake_response.text = json.dumps(mock_gemini_response_payload)

    fake_client = MagicMock()
    fake_client.models.generate_content = MagicMock(return_value=fake_response)
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    with patch.object(settings, "GENAI_PROVIDER", "gemini"), \
         patch.object(settings, "GEMINI_API_KEY", "mock-test-key"), \
         patch("app.services.genai.gemini_provider.genai.Client", return_value=fake_client):
        resp = client.post("/api/v1/genai/explain", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert data["model_provider"] == "gemini"
        assert data["model_name"] == "gemini-3.8-flash"
        assert data["explanation"] is not None
        assert data["explanation"]["findings"][0]["observed_value"] == "140.0 mg/dL"
        assert data["explanation"]["findings"][0]["classification"] == "HIGH"
        assert data["disclaimer"] == MANDATORY_GENAI_DISCLAIMER
        assert fake_client.models.generate_content.called or fake_client.aio.models.generate_content.called


# ---------------------------------------------------------------------------
# Test E: Gemini Provider Handles Missing API Key Safely
# ---------------------------------------------------------------------------

def test_e_gemini_provider_handles_missing_api_key(test_db_and_client, sample_explain_request):
    """Verify missing API key returns HTTP 503 without exposing secrets."""
    client, _, _, _ = test_db_and_client
    payload = sample_explain_request.model_dump()

    with patch.object(settings, "GENAI_PROVIDER", "gemini"), \
         patch.object(settings, "GEMINI_API_KEY", None):
        resp = client.post("/api/v1/genai/explain", json=payload)
        assert resp.status_code == 503
        assert "GEMINI_API_KEY is not configured" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test F: Gemini Provider Handles Simulated Timeout Safely
# ---------------------------------------------------------------------------

def test_f_gemini_provider_handles_simulated_timeout(test_db_and_client, sample_explain_request):
    """Verify timeout returns HTTP 504 Gateway Timeout."""
    client, _, _, _ = test_db_and_client
    payload = sample_explain_request.model_dump()

    fake_client = MagicMock()
    fake_client.models.generate_content = MagicMock(side_effect=TimeoutError())
    fake_client.aio.models.generate_content = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch.object(settings, "GENAI_PROVIDER", "gemini"), \
         patch.object(settings, "GEMINI_API_KEY", "mock-test-key"), \
         patch("app.services.genai.gemini_provider.genai.Client", return_value=fake_client):
        resp = client.post("/api/v1/genai/explain", json=payload)
        assert resp.status_code == 504
        assert "timed out" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test G: Gemini Provider Handles Simulated API Failure Safely
# ---------------------------------------------------------------------------

def test_g_gemini_provider_handles_simulated_api_failure(test_db_and_client, sample_explain_request):
    """Verify Gemini API exception returns clean HTTP 500 without leaking stack traces."""
    client, _, _, _ = test_db_and_client
    payload = sample_explain_request.model_dump()

    fake_client = MagicMock()
    fake_client.models.generate_content = MagicMock(
        side_effect=errors.APIError(500, "Internal Google service fault")
    )
    fake_client.aio.models.generate_content = AsyncMock(
        side_effect=errors.APIError(500, "Internal Google service fault")
    )

    with patch.object(settings, "GENAI_PROVIDER", "gemini"), \
         patch.object(settings, "GEMINI_API_KEY", "mock-test-key"), \
         patch("app.services.genai.gemini_provider.genai.Client", return_value=fake_client):
        resp = client.post("/api/v1/genai/explain", json=payload)
        assert resp.status_code == 500
        assert "An error occurred while generating the educational explanation." in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test H: Gemini Provider Handles Malformed Structured Output Safely
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_h_gemini_provider_handles_malformed_output(sample_explain_request):
    """Verify invalid JSON or malformed schema raises clean RuntimeError."""
    fake_response = MagicMock()
    fake_response.text = "NOT_VALID_JSON_AT_ALL"

    fake_client = MagicMock()
    fake_client.models.generate_content = MagicMock(return_value=fake_response)
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    provider = GeminiProvider(api_key="mock-test-key", client=fake_client)
    with pytest.raises(RuntimeError) as exc_info:
        await provider.generate_explanation(sample_explain_request)
    assert "schema validation" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Test I: Gemini Provider Preserves Upstream Values and Classifications
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_i_gemini_provider_preserves_values_and_classifications(sample_explain_request):
    """Verify provider reconciliation preserves exact input values, units, and categories."""
    # Simulate LLM returning altered numbers or altered classifications
    altered_llm_output = {
        "summary": "Educational summary.",
        "findings": [
            {
                "analyte_name": "glucose",
                "observed_value": "999.0 mg/dL",  # Altered by LLM
                "classification": "NORMAL",       # Altered by LLM
                "plain_language_meaning": "Blood glucose meaning."
            }
        ],
        "risk_explanations": [
            {
                "condition": "diabetes",
                "model_probability": 0.1234,      # Altered by LLM
                "risk_band": "LOW",               # Altered by LLM
                "plain_language_explanation": "Risk explanation."
            }
        ],
        "follow_up_guidance": ["Consult doctor."],
        "recommended_questions_for_doctor": ["What do tests mean?"]
    }

    fake_response = MagicMock()
    fake_response.text = json.dumps(altered_llm_output)

    fake_client = MagicMock()
    fake_client.models.generate_content = MagicMock(return_value=fake_response)
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    provider = GeminiProvider(api_key="mock-test-key", client=fake_client)
    result = await provider.generate_explanation(sample_explain_request)

    # Reconciled result MUST match input request exactly
    assert result.findings[0].observed_value == "140.0 mg/dL"
    assert result.findings[0].classification == "HIGH"
    assert result.risk_explanations[0].model_probability == 0.7450
    assert result.risk_explanations[0].risk_band == "ELEVATED"


# ---------------------------------------------------------------------------
# Test J: Prompt Injection Cannot Violate Medical Safety Boundaries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_j_prompt_injection_safety_neutralization(sample_explain_request):
    """Verify prohibited diagnostic claims in LLM output are neutralized programmatically."""
    adversarial_output = {
        "summary": "You have diabetes and you must take 500 mg metformin daily immediately.",
        "findings": [
            {
                "analyte_name": "glucose",
                "observed_value": "140.0 mg/dL",
                "classification": "HIGH",
                "plain_language_meaning": "Fasting glucose."
            }
        ],
        "risk_explanations": [
            {
                "condition": "diabetes",
                "model_probability": 0.7450,
                "risk_band": "ELEVATED",
                "plain_language_explanation": "Elevated risk."
            }
        ],
        "follow_up_guidance": ["Take medication."],
        "recommended_questions_for_doctor": ["What dosage?"]
    }

    fake_response = MagicMock()
    fake_response.text = json.dumps(adversarial_output)

    fake_client = MagicMock()
    fake_client.models.generate_content = MagicMock(return_value=fake_response)
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    provider = GeminiProvider(api_key="mock-test-key", client=fake_client)
    result = await provider.generate_explanation(sample_explain_request)

    # Forbidden phrases must be neutralized
    assert "you have diabetes" not in result.summary.lower()
    assert "take 500 mg" not in result.summary.lower()
    assert "potential clinical relevance" in result.summary.lower()


# ---------------------------------------------------------------------------
# Test K: Gemini Status Endpoint Reports Live Health
# ---------------------------------------------------------------------------

def test_k_gemini_status_endpoint_reports_health(test_db_and_client):
    """Verify /api/v1/genai/status reports live_gemini_api when configured."""
    client, _, _, _ = test_db_and_client
    with patch.object(settings, "GENAI_PROVIDER", "gemini"), \
         patch.object(settings, "GEMINI_API_KEY", "mock-test-key"):
        resp = client.get("/api/v1/genai/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "gemini"
        assert data["model"] == "gemini-3.8-flash"
        assert data["available"] is True
        assert data["mode"] == "live_gemini_api"
        assert data["network_required"] is True
        assert "api_key" not in data
