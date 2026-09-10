"""
MedIntel AI — Phase 6: Reference Analysis API Schemas.

Pydantic schemas for the Reference Analysis API endpoints.
Provides request and response validation for deterministic reference range
classification and document value extraction.

Safety Guarantees:
    - Never outputs medical disease diagnoses or clinical treatment advice.
    - Classifications strictly restricted to LOW, NORMAL, HIGH, CRITICAL.
    - Preserves verification status (EXTRACTED vs. VERIFIED) to enforce safety gate.
    - Mandatory medical disclaimer included on every response model.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class PatientContextSchema(BaseModel):
    """Demographic context for reference range resolution."""
    age: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=130.0,
        description="Patient age in years",
    )
    sex: Optional[str] = Field(
        default=None,
        description="Biological sex ('M', 'F', or None)",
    )


class MeasurementInputSchema(BaseModel):
    """Individual medical measurement submitted for reference analysis."""
    test_name: str = Field(
        ...,
        min_length=1,
        description="Medical test name or alias (e.g., 'FBS', 'Hemoglobin')",
    )
    value: Optional[Any] = Field(
        default=None,
        description="Measured value (numeric, string, or None)",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Reported unit of measurement (e.g., 'mg/dL', 'g/dL')",
    )
    test_value_text: Optional[str] = Field(
        default=None,
        description="Original text value for qualitative results",
    )
    is_user_verified: bool = Field(
        default=False,
        description="Safety gate flag: True if verified by a user/clinician, False if unverified raw OCR extraction",
    )
    context: Optional[PatientContextSchema] = Field(
        default=None,
        description="Optional per-measurement patient context override",
    )


class BatchAnalysisRequest(BaseModel):
    """Request payload for POST /api/v1/reference/analyze."""
    measurements: List[MeasurementInputSchema] = Field(
        ...,
        min_length=1,
        description="List of clinical measurements to analyze",
    )
    patient_context: Optional[PatientContextSchema] = Field(
        default=None,
        description="Shared patient demographic context applied to all measurements",
    )
    report_id: Optional[int] = Field(
        default=None,
        description="Optional Report ID for associating results in the database",
    )
    persist: bool = Field(
        default=False,
        description="Whether to persist results into SQLite database (requires valid report_id)",
    )


class ParseAndAnalyzeRequest(BaseModel):
    """Request payload for POST /api/v1/reference/parse-and-analyze."""
    text: str = Field(
        ...,
        min_length=1,
        description="Unstructured document or OCR text to parse and classify",
    )
    patient_context: Optional[PatientContextSchema] = Field(
        default=None,
        description="Shared patient demographic context",
    )
    report_id: Optional[int] = Field(
        default=None,
        description="Optional Report ID for persistence",
    )
    persist: bool = Field(
        default=False,
        description="Whether to persist extracted test results into SQLite database",
    )
    is_user_verified: bool = Field(
        default=False,
        description="Safety gate flag: must be False for unreviewed raw OCR extractions",
    )
    include_unrecognized: bool = Field(
        default=False,
        description="Whether to include unrecognized text lines in the response",
    )


class ReferenceRangeSummarySchema(BaseModel):
    """Summary of the applied reference range."""
    canonical_name: str
    unit: str
    normal_low: Optional[float] = None
    normal_high: Optional[float] = None
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None
    source: str
    citation: Optional[str] = None
    reference_type: str = "GENERAL_REFERENCE"
    verification_status: str = "VERIFIED"


class AnalysisResultSchema(BaseModel):
    """Structured analysis outcome for an individual measurement."""
    original_test_name: str
    canonical_name: Optional[str] = None
    numeric_value: Optional[float] = None
    original_value_text: Optional[str] = None
    unit: Optional[str] = None
    normalized_unit: Optional[str] = None
    classification: Optional[str] = Field(
        default=None,
        description="Deterministic classification: LOW, NORMAL, HIGH, CRITICAL or None",
    )
    analysis_status: str = Field(
        ...,
        description="Operational status code (SUCCESS, REFERENCE_NOT_AVAILABLE, UNIT_MISMATCH, etc.)",
    )
    reference_range: Optional[ReferenceRangeSummarySchema] = None
    reference_source: Optional[str] = None
    is_user_verified: bool = False
    persisted_test_result_id: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default="This is not a medical diagnosis. Please consult a qualified healthcare professional.",
        description="Mandatory medical disclaimer",
    )


class BatchAnalysisResponse(BaseModel):
    """Response payload for POST /api/v1/reference/analyze."""
    success: bool = True
    total_submitted: int
    total_classified: int
    report_id: Optional[int] = None
    results: List[AnalysisResultSchema]
    disclaimer: str = (
        "This is not a medical diagnosis. Please consult a qualified healthcare professional."
    )


class ParsedAndAnalyzedItemSchema(BaseModel):
    """Item in ParseAndAnalyzeResponse."""
    parsed_line: str
    parsed_analyte: Optional[str] = None
    canonical_name: Optional[str] = None
    parser_status: str
    extracted_reference_range: Optional[str] = None
    extraction_confidence: float = Field(
        ...,
        description="Text extraction confidence score (0.0 to 1.0). NEVER represents clinical certainty.",
    )
    analysis: Optional[AnalysisResultSchema] = None


class ParseAndAnalyzeResponse(BaseModel):
    """Response payload for POST /api/v1/reference/parse-and-analyze."""
    success: bool = True
    total_lines_parsed: int
    total_measurements_analyzed: int
    report_id: Optional[int] = None
    items: List[ParsedAndAnalyzedItemSchema]
    disclaimer: str = (
        "This is not a medical diagnosis. Please consult a qualified healthcare professional."
    )
