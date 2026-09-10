"""
MedIntel AI — Phase 8: Generative AI & Explanation Schemas.

Pydantic schemas for the GenAI explanation and translation subsystem.
Enforces non-diagnostic semantics, strict feature and probability validation,
user verification safety gates, and structured educational communication.

Safety Invariants:
    - Never calculates or alters medical reference ranges or classifications.
    - Never recalculates or modifies ML probabilities or risk bands.
    - Strictly non-diagnostic and non-prescriptive.
    - No raw unverified document text or arbitrary prompt injections permitted.
    - Mandatory medical disclaimer on every generated explanation.
"""

from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


MANDATORY_GENAI_DISCLAIMER: str = (
    "This explanation is generated for educational and informational purposes only. "
    "It is NOT a medical diagnosis, clinical prognosis, or treatment recommendation. "
    "Always consult a qualified healthcare professional regarding any medical tests, "
    "symptoms, or health decisions."
)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SupportedLanguage(str, Enum):
    """Supported output languages for patient-facing explanations."""
    ENGLISH = "en"
    HINDI = "hi"
    MARATHI = "mr"
    GUJARATI = "gu"


class DetailLevel(str, Enum):
    """Detail level for explanation complexity."""
    SIMPLE = "simple"        # Everyday language, 6th-grade reading level
    DETAILED = "detailed"    # More technical clinical context for inquisitive patients


class GenAIStatus(str, Enum):
    """Operational status codes for the GenAI subsystem."""
    SUCCESS = "SUCCESS"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"


# ---------------------------------------------------------------------------
# Upstream Findings Models (Input to GenAI)
# ---------------------------------------------------------------------------

class VerifiedAnalyteSummary(BaseModel):
    """Represents an already-verified deterministic laboratory finding from Phase 6.

    GenAI NEVER determines classifications; it strictly accepts pre-evaluated findings.
    """
    test_name: str = Field(..., description="Original or recognized test name (e.g. 'FBS')")
    canonical_name: Optional[str] = Field(None, description="Standardized analyte name (e.g. 'Fasting Blood Glucose')")
    display_name: Optional[str] = Field(None, description="Patient-friendly display label")
    value: Optional[float] = Field(None, description="Verified numeric test value")
    unit: Optional[str] = Field(None, description="Reported unit of measurement (e.g. 'mg/dL')")
    classification: Optional[str] = Field(
        None,
        description="Deterministic classification from Phase 6: LOW, NORMAL, HIGH, or CRITICAL",
    )
    reference_low: Optional[float] = Field(None, description="Lower reference bound applied by Phase 6")
    reference_high: Optional[float] = Field(None, description="Upper reference bound applied by Phase 6")
    reference_source: Optional[str] = Field(None, description="Authoritative reference source citation")
    analysis_status: Optional[str] = Field(None, description="Phase 6 status (e.g. 'SUCCESS')")
    warnings: List[str] = Field(default_factory=list, description="Any warnings from reference analysis")

    @field_validator("value", "reference_low", "reference_high", mode="before")
    @classmethod
    def check_finite(cls, v: Any) -> Any:
        if v is not None:
            try:
                f_val = float(v)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Value must be a valid number: {v}") from exc
            if math.isnan(f_val) or math.isinf(f_val):
                raise ValueError("Analyte values and reference bounds must be finite numbers.")
            return f_val
        return None


class MLRiskSummary(BaseModel):
    """Represents an already-computed disease risk estimation from Phase 7.

    GenAI NEVER calculates or recalibrates probabilities; it consumes Phase 7 outputs.
    """
    condition: str = Field(..., description="Target disease: diabetes, heart_disease, kidney_disease")
    risk_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model-estimated positive class probability P(target=1) strictly in [0.0, 1.0]",
    )
    risk_band: str = Field(..., description="Educational display band: LOW, MODERATE, ELEVATED")
    model_name: Optional[str] = Field(None, description="Champion model architecture identifier")
    model_version: Optional[str] = Field(None, description="Trained model artifact version timestamp")
    status: str = Field("OK", description="Phase 7 execution status (OK, INSUFFICIENT_FEATURES)")

    @field_validator("risk_probability", mode="before")
    @classmethod
    def validate_probability(cls, v: Any) -> float:
        try:
            val = float(v)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Risk probability must be a valid float: {v}") from exc
        if math.isnan(val) or math.isinf(val):
            raise ValueError("Risk probability must be a finite number.")
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"Risk probability must be strictly between 0.0 and 1.0 (got {val}).")
        return val


# ---------------------------------------------------------------------------
# Request Model
# ---------------------------------------------------------------------------

class GenAIExplainRequest(BaseModel):
    """Structured request payload for generating patient-friendly explanations.

    Accepts ONLY structured, verified findings. Rejects raw document text,
    unverified OCR extractions, and arbitrary prompt directives.
    """
    report_id: Optional[int] = Field(
        None,
        description="Optional Report ID for audit database persistence into SQLite summaries",
    )
    persist: bool = Field(
        default=False,
        description="Whether to persist generated summary to SQLite database (requires valid report_id)",
    )
    is_user_verified: bool = Field(
        ...,
        description="Mandatory safety gate: True if user/clinician confirmed extracted values",
    )
    patient_age: Optional[float] = Field(
        None,
        ge=0.0,
        le=130.0,
        description="Optional patient age in years for contextual explanation tailoring",
    )
    patient_sex: Optional[str] = Field(
        None,
        description="Optional patient biological sex ('M', 'F', or None)",
    )
    analytes: List[VerifiedAnalyteSummary] = Field(
        default_factory=list,
        description="Verified laboratory findings evaluated by Phase 6",
    )
    ml_risks: List[MLRiskSummary] = Field(
        default_factory=list,
        description="Disease risk probabilities computed by Phase 7",
    )
    language: SupportedLanguage = Field(
        default=SupportedLanguage.ENGLISH,
        description="Requested language for patient explanation: en, hi, mr, gu",
    )
    detail_level: DetailLevel = Field(
        default=DetailLevel.SIMPLE,
        description="Target explanation complexity: simple or detailed",
    )

    @field_validator("patient_sex", mode="before")
    @classmethod
    def normalize_sex(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip().upper()
        if s in {"M", "MALE"}:
            return "M"
        if s in {"F", "FEMALE"}:
            return "F"
        return "OTHER"


# ---------------------------------------------------------------------------
# Response & Payload Models
# ---------------------------------------------------------------------------

class AnalyteExplanationItem(BaseModel):
    """Educational breakdown of an individual verified laboratory measurement."""
    analyte_name: str = Field(..., description="Analyte name")
    observed_value: Optional[str] = Field(None, description="Observed numeric value with unit (e.g. '145.0 mg/dL')")
    classification: Optional[str] = Field(None, description="Deterministic classification (LOW/NORMAL/HIGH/CRITICAL)")
    plain_language_meaning: str = Field(..., description="Educational summary of what this analyte does in the body")


class RiskExplanationItem(BaseModel):
    """Educational breakdown of an individual ML risk estimation."""
    condition: str = Field(..., description="Condition name (e.g. 'diabetes')")
    model_probability: Optional[float] = Field(None, description="Positive class probability (e.g. 0.28)")
    risk_band: Optional[str] = Field(None, description="Educational band (LOW, MODERATE, ELEVATED)")
    plain_language_explanation: str = Field(..., description="Non-diagnostic plain-language explanation of risk indicator")


class GenAIExplanationPayload(BaseModel):
    """Structured clinical explanation payload generated by the GenAI provider.

    Strictly separates factual findings from educational guidance.
    Contains NO diagnosis, prescription, or therapeutic directives.
    """
    summary: str = Field(..., description="Plain-language educational overview of overall report findings")
    findings: List[AnalyteExplanationItem] = Field(
        default_factory=list,
        description="Analyte-by-analyte educational breakdown",
    )
    risk_explanations: List[RiskExplanationItem] = Field(
        default_factory=list,
        description="Disease risk indicator explanations",
    )
    follow_up_guidance: List[str] = Field(
        default_factory=list,
        description="General lifestyle/educational talking points to discuss with a healthcare professional",
    )
    recommended_questions_for_doctor: List[str] = Field(
        default_factory=list,
        description="Suggested questions the patient may bring to their physician appointment",
    )


class GenAIExplainResponse(BaseModel):
    """Top-level response model for the GenAI explanation service."""
    status: GenAIStatus = Field(..., description="Subsystem operational status")
    report_id: Optional[int] = Field(None, description="Associated Report ID")
    language: SupportedLanguage = Field(default=SupportedLanguage.ENGLISH, description="Output language code")
    explanation: Optional[GenAIExplanationPayload] = Field(
        None,
        description="Structured explanation payload; null if verification is required or provider fails",
    )
    translated_summary: Optional[str] = Field(
        None,
        description="Translated summary text if requested language is not English",
    )
    model_provider: str = Field(..., description="Provider identifier (e.g. 'mock', 'gemini')")
    model_name: Optional[str] = Field(None, description="Model identifier (e.g. 'gemini-3.8-flash', 'mock-v1')")
    disclaimer: str = Field(
        default=MANDATORY_GENAI_DISCLAIMER,
        description="Mandatory non-diagnostic medical disclaimer",
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 generation timestamp",
    )
    persisted_summary_id: Optional[int] = Field(
        None,
        description="Primary key in SQLite summaries table if persisted",
    )


class GenAIStatusResponse(BaseModel):
    """Health and status of the GenAI explanation service."""
    status: str = Field(..., description="Overall status: OK, DEGRADED, or ERROR")
    provider: str = Field(..., description="Active provider name (e.g. 'mock', 'gemini')")
    model: str = Field(..., description="Active model name")
    available: bool = Field(..., description="Whether provider is available and functional")
    mode: str = Field(..., description="Operating mode (e.g. 'offline_deterministic_mock')")
    network_required: bool = Field(..., description="Whether external network connectivity is required")

