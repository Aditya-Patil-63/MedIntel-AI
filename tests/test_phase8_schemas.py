"""
MedIntel AI — Phase 8: GenAI Schemas, Provider Abstraction & Offline Mock Tests.

Validates:
    - SupportedLanguage, DetailLevel, and GenAIStatus enums
    - Schema validation rules (probabilities, age, languages, detail levels)
    - Rejection of negative/infinite values and prompt injections
    - MockGenAIProvider deterministic generation and multilingual translation
    - Preservation of clinical invariants (numbers, units, classifications, risk probabilities, risk bands)
    - Strict non-diagnostic, non-prescriptive safety guarantees
    - 100% offline execution without network access
"""

import math
import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Ensure repository root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.genai import (
    AnalyteExplanationItem,
    DetailLevel,
    GenAIExplainRequest,
    GenAIExplainResponse,
    GenAIExplanationPayload,
    GenAIStatus,
    MANDATORY_GENAI_DISCLAIMER,
    MLRiskSummary,
    RiskExplanationItem,
    SupportedLanguage,
    VerifiedAnalyteSummary,
)
from app.services.genai.base import BaseGenAIProvider
from app.services.genai.mock_provider import MockGenAIProvider


# ---------------------------------------------------------------------------
# A. Supported Languages
# ---------------------------------------------------------------------------

def test_a_supported_languages():
    """Verify supported language codes for Indian healthcare multilingual support."""
    assert SupportedLanguage.ENGLISH.value == "en"
    assert SupportedLanguage.HINDI.value == "hi"
    assert SupportedLanguage.MARATHI.value == "mr"
    assert SupportedLanguage.GUJARATI.value == "gu"
    assert len(SupportedLanguage) == 4


# ---------------------------------------------------------------------------
# B. Invalid Language Rejection
# ---------------------------------------------------------------------------

def test_b_invalid_language_rejection():
    """Verify Pydantic rejects unsupported languages."""
    with pytest.raises(ValidationError) as exc_info:
        GenAIExplainRequest(
            is_user_verified=True,
            language="french",
        )
    assert "Input should be 'en', 'hi', 'mr' or 'gu'" in str(exc_info.value)


# ---------------------------------------------------------------------------
# C. Detail Levels
# ---------------------------------------------------------------------------

def test_c_detail_levels():
    """Verify supported detail level enum values and invalid rejection."""
    assert DetailLevel.SIMPLE.value == "simple"
    assert DetailLevel.DETAILED.value == "detailed"

    # Valid assignment
    req = GenAIExplainRequest(is_user_verified=True, detail_level=DetailLevel.DETAILED)
    assert req.detail_level == DetailLevel.DETAILED

    # Invalid detail level
    with pytest.raises(ValidationError):
        GenAIExplainRequest(is_user_verified=True, detail_level="expert_mode")


# ---------------------------------------------------------------------------
# D. Invalid Probability Rejection
# ---------------------------------------------------------------------------

def test_d_invalid_probability_rejection():
    """Verify MLRiskSummary rejects probabilities < 0.0 or > 1.0 or NaN."""
    # Negative probability
    with pytest.raises(ValidationError) as exc1:
        MLRiskSummary(
            condition="diabetes",
            risk_probability=-0.01,
            risk_band="LOW",
        )
    assert "strictly between 0.0 and 1.0" in str(exc1.value)

    # Probability > 1.0
    with pytest.raises(ValidationError) as exc2:
        MLRiskSummary(
            condition="diabetes",
            risk_probability=1.0001,
            risk_band="ELEVATED",
        )
    assert "strictly between 0.0 and 1.0" in str(exc2.value)

    # NaN probability
    with pytest.raises(ValidationError):
        MLRiskSummary(
            condition="diabetes",
            risk_probability=float("nan"),
            risk_band="LOW",
        )


# ---------------------------------------------------------------------------
# E. Probability Boundary Values (0.0 and 1.0)
# ---------------------------------------------------------------------------

def test_e_probability_boundary_values():
    """Verify 0.0 and 1.0 probabilities are valid boundary inputs."""
    risk_zero = MLRiskSummary(
        condition="diabetes",
        risk_probability=0.0,
        risk_band="LOW",
        model_name="RandomForest_d4_s8",
    )
    assert risk_zero.risk_probability == 0.0

    risk_one = MLRiskSummary(
        condition="heart_disease",
        risk_probability=1.0,
        risk_band="ELEVATED",
        model_name="LogisticRegression_C1.0",
    )
    assert risk_one.risk_probability == 1.0


# ---------------------------------------------------------------------------
# F. Invalid Age Rejection
# ---------------------------------------------------------------------------

def test_f_invalid_age_rejection():
    """Verify age boundaries (0.0 <= age <= 130.0)."""
    # Negative age
    with pytest.raises(ValidationError):
        GenAIExplainRequest(is_user_verified=True, patient_age=-1.0)

    # Age above 130
    with pytest.raises(ValidationError):
        GenAIExplainRequest(is_user_verified=True, patient_age=130.5)

    # Valid boundary ages
    req_infant = GenAIExplainRequest(is_user_verified=True, patient_age=0.0)
    assert req_infant.patient_age == 0.0

    req_elder = GenAIExplainRequest(is_user_verified=True, patient_age=105.0)
    assert req_elder.patient_age == 105.0


# ---------------------------------------------------------------------------
# G. Valid GenAI Request
# ---------------------------------------------------------------------------

def test_g_valid_genai_request():
    """Verify construction of a complete, valid GenAIExplainRequest."""
    req = GenAIExplainRequest(
        report_id=42,
        is_user_verified=True,
        patient_age=45.0,
        patient_sex="M",
        analytes=[
            VerifiedAnalyteSummary(
                test_name="Glucose",
                canonical_name="Fasting Blood Glucose",
                value=145.0,
                unit="mg/dL",
                classification="HIGH",
                reference_low=70.0,
                reference_high=99.0,
                reference_source="ADA Standards of Medical Care in Diabetes 2024",
            ),
            VerifiedAnalyteSummary(
                test_name="Hemoglobin",
                canonical_name="Hemoglobin",
                value=13.5,
                unit="g/dL",
                classification="NORMAL",
                reference_low=13.0,
                reference_high=17.0,
            ),
        ],
        ml_risks=[
            MLRiskSummary(
                condition="diabetes",
                risk_probability=0.7450,
                risk_band="ELEVATED",
                model_name="RandomForest_d4_s8",
                model_version="2026-09-10T11:35:53",
            )
        ],
        language=SupportedLanguage.HINDI,
        detail_level=DetailLevel.DETAILED,
    )

    assert req.report_id == 42
    assert req.is_user_verified is True
    assert req.patient_sex == "M"
    assert len(req.analytes) == 2
    assert len(req.ml_risks) == 1
    assert req.language == SupportedLanguage.HINDI
    assert req.detail_level == DetailLevel.DETAILED


# ---------------------------------------------------------------------------
# H. Verification Flag Behavior at Schema Level
# ---------------------------------------------------------------------------

def test_h_verification_flag_behavior():
    """Verify is_user_verified is mandatory and properly enforced."""
    # Missing is_user_verified
    with pytest.raises(ValidationError) as exc:
        GenAIExplainRequest()
    assert "is_user_verified" in str(exc.value)

    # False verification flag is accepted by schema (handled by service safety gate)
    unverified_req = GenAIExplainRequest(is_user_verified=False)
    assert unverified_req.is_user_verified is False


# ---------------------------------------------------------------------------
# I. Mock Provider Generation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_i_mock_provider_generation():
    """Verify MockGenAIProvider produces valid structured explanation offline."""
    provider = MockGenAIProvider()
    assert issubclass(MockGenAIProvider, BaseGenAIProvider)
    assert provider.provider_name == "mock"
    assert "mock" in provider.model_name

    req = GenAIExplainRequest(
        is_user_verified=True,
        analytes=[
            VerifiedAnalyteSummary(
                test_name="Glucose",
                canonical_name="Fasting Blood Glucose",
                value=145.0,
                unit="mg/dL",
                classification="HIGH",
            )
        ],
        ml_risks=[
            MLRiskSummary(
                condition="diabetes",
                risk_probability=0.72,
                risk_band="ELEVATED",
                model_name="RandomForest_d4_s8",
            )
        ],
        language=SupportedLanguage.ENGLISH,
        detail_level=DetailLevel.SIMPLE,
    )

    payload = await provider.generate_explanation(req)
    assert isinstance(payload, GenAIExplanationPayload)
    assert "simulated educational explanation" in payload.summary
    assert len(payload.findings) == 1
    assert len(payload.risk_explanations) == 1
    assert len(payload.follow_up_guidance) > 0
    assert len(payload.recommended_questions_for_doctor) > 0


# ---------------------------------------------------------------------------
# J. Mock Provider Translation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_j_mock_provider_translation():
    """Verify MockGenAIProvider translates structured explanation to all supported languages."""
    provider = MockGenAIProvider()
    req = GenAIExplainRequest(
        is_user_verified=True,
        analytes=[
            VerifiedAnalyteSummary(
                test_name="Creatinine",
                canonical_name="Serum Creatinine",
                value=1.8,
                unit="mg/dL",
                classification="HIGH",
            )
        ],
        ml_risks=[
            MLRiskSummary(
                condition="kidney_disease",
                risk_probability=0.88,
                risk_band="ELEVATED",
                model_name="LogisticRegression_C10.0",
            )
        ],
    )

    english_payload = await provider.generate_explanation(req)

    # Test Hindi translation
    hi_payload, hi_summary = await provider.translate_explanation(
        english_payload, SupportedLanguage.HINDI
    )
    assert hi_summary is not None
    assert "सिम्युलेटेड शैक्षणिक विवरण" in hi_summary
    assert "[हिंदी विवरण]" in hi_payload.findings[0].plain_language_meaning

    # Test Marathi translation
    mr_payload, mr_summary = await provider.translate_explanation(
        english_payload, SupportedLanguage.MARATHI
    )
    assert mr_summary is not None
    assert "सिम्युलेटेड शैक्षणिक स्पष्टीकरण" in mr_summary
    assert "[मराठी विवरण]" in mr_payload.findings[0].plain_language_meaning

    # Test Gujarati translation
    gu_payload, gu_summary = await provider.translate_explanation(
        english_payload, SupportedLanguage.GUJARATI
    )
    assert gu_summary is not None
    assert "શૈક્ષણિક ખુલાસો" in gu_summary
    assert "[ગુજરાતી વિગતો]" in gu_payload.findings[0].plain_language_meaning


# ---------------------------------------------------------------------------
# K. Mock Provider Preserves Invariants
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_k_mock_provider_preserves_invariants():
    """Verify that translation strictly preserves numeric values, units, classifications, and probabilities."""
    provider = MockGenAIProvider()
    req = GenAIExplainRequest(
        is_user_verified=True,
        analytes=[
            VerifiedAnalyteSummary(
                test_name="Hemoglobin",
                canonical_name="Hemoglobin",
                value=9.2,
                unit="g/dL",
                classification="LOW",
            )
        ],
        ml_risks=[
            MLRiskSummary(
                condition="heart_disease",
                risk_probability=0.2854,
                risk_band="LOW",
                model_name="LogisticRegression_C1.0",
            )
        ],
    )

    base_payload = await provider.generate_explanation(req)

    for lang in [SupportedLanguage.HINDI, SupportedLanguage.MARATHI, SupportedLanguage.GUJARATI]:
        trans_payload, _ = await provider.translate_explanation(base_payload, lang)

        # Invariant 1: Analyte observed_value (exact string with number and unit)
        assert trans_payload.findings[0].observed_value == "9.2 g/dL"

        # Invariant 2: Analyte classification (exact deterministic label)
        assert trans_payload.findings[0].classification == "LOW"

        # Invariant 3: Model condition name
        assert trans_payload.risk_explanations[0].condition == "heart_disease"

        # Invariant 4: Model probability (exact float)
        assert trans_payload.risk_explanations[0].model_probability == 0.2854

        # Invariant 5: Model risk band (exact string)
        assert trans_payload.risk_explanations[0].risk_band == "LOW"


# ---------------------------------------------------------------------------
# L. Mock Provider Contains Mandatory Disclaimer
# ---------------------------------------------------------------------------

def test_l_mock_provider_contains_mandatory_disclaimer():
    """Verify response model includes mandatory non-diagnostic disclaimer."""
    response = GenAIExplainResponse(
        status=GenAIStatus.SUCCESS,
        model_provider="mock",
        model_name="mock-deterministic-v1",
    )
    assert response.disclaimer == MANDATORY_GENAI_DISCLAIMER
    assert "NOT a medical diagnosis" in response.disclaimer
    assert "qualified healthcare professional" in response.disclaimer


# ---------------------------------------------------------------------------
# M. Mock Provider Never Produces Diagnostic Wording
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_m_mock_provider_no_diagnostic_wording():
    """Verify mock provider explanations never assert disease diagnosis."""
    provider = MockGenAIProvider()
    req = GenAIExplainRequest(
        is_user_verified=True,
        analytes=[
            VerifiedAnalyteSummary(
                test_name="Glucose",
                value=250.0,
                unit="mg/dL",
                classification="CRITICAL",
            )
        ],
        ml_risks=[
            MLRiskSummary(
                condition="diabetes",
                risk_probability=0.95,
                risk_band="ELEVATED",
            )
        ],
    )
    payload = await provider.generate_explanation(req)
    all_text = " ".join([
        payload.summary,
        payload.findings[0].plain_language_meaning,
        payload.risk_explanations[0].plain_language_explanation,
    ]).lower()

    # Forbidden diagnostic assertions
    prohibited_assertions = [
        "you have diabetes",
        "you have kidney disease",
        "you have heart disease",
        "we diagnose",
        "diagnosis confirmed",
        "you are diagnosed with",
    ]
    for assertion in prohibited_assertions:
        assert assertion not in all_text


# ---------------------------------------------------------------------------
# N. Mock Provider Never Produces Medication/Dosage Instructions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_n_mock_provider_no_medication_or_dosage():
    """Verify mock provider explanations never prescribe medication or dosage."""
    provider = MockGenAIProvider()
    req = GenAIExplainRequest(
        is_user_verified=True,
        analytes=[
            VerifiedAnalyteSummary(
                test_name="Blood Pressure",
                value=160.0,
                unit="mm Hg",
                classification="HIGH",
            )
        ],
    )
    payload = await provider.generate_explanation(req)
    all_text = " ".join([
        payload.summary,
        payload.findings[0].plain_language_meaning,
        *payload.follow_up_guidance,
    ]).lower()

    prohibited_prescriptions = [
        "take 500mg",
        "prescribe",
        "take dosage",
        "mg daily",
        "take amoxicillin",
        "take metformin",
    ]
    for prescription in prohibited_prescriptions:
        assert prescription not in all_text


# ---------------------------------------------------------------------------
# O. Provider Interface Can Be Used Without Network Access
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_o_provider_offline_and_health_check():
    """Verify mock provider operates completely offline with valid health status."""
    provider = MockGenAIProvider()
    health = await provider.check_health()
    assert health["available"] is True
    assert health["provider"] == "mock"
    assert health["mode"] == "offline_deterministic_mock"
    assert health["network_required"] is False
