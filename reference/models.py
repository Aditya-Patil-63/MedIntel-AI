"""
MedIntel AI — Phase 6: Medical Reference Analysis Data Models.

Defines the schemas, enumerations, and data containers for deterministic
laboratory reference-range analysis.

Core Safety Guarantees:
    - Non-diagnostic: Evaluates numerical measurements against reference intervals.
    - No disease names or treatment recommendations in classification outputs.
    - Mandatory medical disclaimer included on every analysis result.
"""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Classification & Status Enumerations
# ---------------------------------------------------------------------------

class Classification(str, Enum):
    """
    Deterministic classification of a test value against a reference interval.

    Allowed outputs are strictly limited to the four standard clinical categories.
    The engine must NEVER output clinical diagnoses (e.g., 'Diabetes', 'Anemia').
    """
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnalysisStatus(str, Enum):
    """
    Operational status of a reference analysis attempt.

    Identifies whether the analysis succeeded or why it could not be performed.
    """
    SUCCESS = "SUCCESS"
    REFERENCE_NOT_AVAILABLE = "REFERENCE_NOT_AVAILABLE"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    UNKNOWN_UNIT = "UNKNOWN_UNIT"
    VALUE_MISSING = "VALUE_MISSING"
    VALUE_NON_NUMERIC = "VALUE_NON_NUMERIC"
    INVALID_VALUE = "INVALID_VALUE"
    CONTEXT_REQUIRED = "CONTEXT_REQUIRED"
    QUALITATIVE_RESULT = "QUALITATIVE_RESULT"


class ReferenceType(str, Enum):
    """
    Distinguishes general baseline reference intervals from lab-specific calibrated intervals.
    """
    GENERAL_REFERENCE = "GENERAL_REFERENCE"
    LAB_SPECIFIC_REFERENCE = "LAB_SPECIFIC_REFERENCE"


class VerificationStatus(str, Enum):
    """
    Audit verification status of a reference interval definition against clinical literature.
    """
    VERIFIED = "VERIFIED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


# ---------------------------------------------------------------------------
# Patient Context
# ---------------------------------------------------------------------------

class PatientContext(BaseModel):
    """
    Demographic context necessary for resolving demographic-specific reference intervals.

    Reference intervals for certain analytes (e.g., Hemoglobin, Creatinine)
    depend legitimately on biological sex or age.
    """
    age: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=130.0,
        description="Patient age in years",
    )
    sex: Optional[str] = Field(
        default=None,
        description="Biological sex for laboratory reference lookup ('M', 'F', 'OTHER', or None)",
    )


# ---------------------------------------------------------------------------
# Reference Range Definition
# ---------------------------------------------------------------------------

class ReferenceRange(BaseModel):
    """
    Configured laboratory reference interval for a specific analyte and demographic context.

    Note on Laboratory Ranges:
        Reference ranges vary across laboratories, instrumentation, analytical
        methodologies, and geographic populations. Configured ranges serve as
        general educational references and must never be treated as universally valid.
    """
    canonical_name: str = Field(
        ...,
        description="Canonical medical name of the analyte (e.g., 'Fasting Blood Glucose')",
    )
    aliases: List[str] = Field(
        default_factory=list,
        description="Recognized common aliases and abbreviations for this analyte",
    )
    unit: str = Field(
        ...,
        description="Standard unit of measurement for this reference interval (e.g., 'mg/dL', 'g/dL')",
    )
    normal_low: Optional[float] = Field(
        default=None,
        description="Lower bound of normal reference interval (inclusive)",
    )
    normal_high: Optional[float] = Field(
        default=None,
        description="Upper bound of normal reference interval (inclusive)",
    )
    critical_low: Optional[float] = Field(
        default=None,
        description="Critical low threshold (values below this represent critical alert values)",
    )
    critical_high: Optional[float] = Field(
        default=None,
        description="Critical high threshold (values above this represent critical alert values)",
    )
    applicable_sex: Optional[str] = Field(
        default=None,
        description="Applicable biological sex ('M', 'F', or None if applicable to all)",
    )
    min_age_years: Optional[float] = Field(
        default=None,
        description="Minimum age in years for which this interval is valid",
    )
    max_age_years: Optional[float] = Field(
        default=None,
        description="Maximum age in years for which this interval is valid",
    )
    source: str = Field(
        ...,
        description="Authoritative medical guideline or textbook source (e.g., 'ADA 2024', 'WHO')",
    )
    citation: Optional[str] = Field(
        default=None,
        description="Detailed publication citation or DOI for reference validation",
    )
    reference_type: ReferenceType = Field(
        default=ReferenceType.GENERAL_REFERENCE,
        description="Distinguishes general educational references from lab-specific calibrated intervals",
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.VERIFIED,
        description="Audit verification status of this reference definition",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Clinical methodology notes, specimen type, or fasting requirements",
    )
    is_physiologically_non_negative: bool = Field(
        default=True,
        description="Whether negative values are physiologically impossible for this analyte",
    )
    disclaimer: str = Field(
        default=(
            "This reference interval is provided for educational and general reference purposes only. "
            "Actual clinical reference intervals vary by laboratory, instrumentation, and patient demographics."
        ),
        description="Educational disclaimer associated with this reference interval",
    )


# ---------------------------------------------------------------------------
# Measurement Input & Analysis Result Containers
# ---------------------------------------------------------------------------

class TestMeasurement(BaseModel):
    """
    Extracted or user-verified medical measurement submitted for reference analysis.
    """
    __test__ = False

    test_name: str = Field(..., description="Extracted or reported test name")
    value: Any = Field(..., description="Measured value (numeric, string, or None)")
    unit: Optional[str] = Field(default=None, description="Reported unit of measurement")
    context: Optional[PatientContext] = Field(
        default=None,
        description="Optional patient context (age, sex) for demographic range resolution",
    )


class AnalysisResult(BaseModel):
    """
    Structured outcome of deterministic reference range classification.

    Guarantees:
        - Never outputs clinical disease diagnoses or treatment instructions.
        - Provides full transparency on the reference range and source utilized.
        - Preserves audit trail from raw input to canonical form.
    """
    canonical_name: Optional[str] = Field(
        default=None,
        description="Resolved canonical analyte name, or None if unrecognized",
    )
    original_test_name: str = Field(
        ...,
        description="Original test name string provided in the input",
    )
    numeric_value: Optional[float] = Field(
        default=None,
        description="Parsed numerical value used for comparison, or None if unparseable",
    )
    original_value_text: Optional[str] = Field(
        default=None,
        description="Original raw value string before numerical parsing",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Input unit of measurement provided",
    )
    normalized_value: Optional[float] = Field(
        default=None,
        description="Value following explicit, certified unit conversion, if applicable",
    )
    normalized_unit: Optional[str] = Field(
        default=None,
        description="Unit after canonical unit normalization",
    )
    classification: Optional[Classification] = Field(
        default=None,
        description="Deterministic classification (LOW, NORMAL, HIGH, CRITICAL), or None if unclassified",
    )
    reference_range: Optional[ReferenceRange] = Field(
        default=None,
        description="The reference range definition applied during classification",
    )
    reference_source: Optional[str] = Field(
        default=None,
        description="Authoritative source citation of the applied reference range",
    )
    status: AnalysisStatus = Field(
        ...,
        description="Status code indicating outcome of analysis attempt",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings or context notices generated during evaluation",
    )
    disclaimer: str = Field(
        default="This is not a medical diagnosis. Please consult a qualified healthcare professional.",
        description="Mandatory medical safety disclaimer required on all outputs",
    )


# ---------------------------------------------------------------------------
# Value Parser Models
# ---------------------------------------------------------------------------

class ParserStatus(str, Enum):
    """
    Extraction outcome for an individual text line or candidate measurement.
    """
    SUCCESS = "SUCCESS"
    VALUE_MISSING = "VALUE_MISSING"
    UNKNOWN_UNIT = "UNKNOWN_UNIT"
    AMBIGUOUS = "AMBIGUOUS"
    UNRECOGNIZED_ANALYTE = "UNRECOGNIZED_ANALYTE"
    QUALITATIVE_RESULT = "QUALITATIVE_RESULT"


class ParsedMeasurement(BaseModel):
    """
    Structured extraction outcome from parsing medical report text.

    Guarantees:
        - Extraction confidence represents text/optical parsing fidelity only.
        - NEVER represents clinical, diagnostic, or disease certainty.
    """
    raw_line: str = Field(..., description="Original raw line from document or OCR")
    raw_analyte: Optional[str] = Field(default=None, description="Original matched analyte string")
    canonical_name: Optional[str] = Field(default=None, description="Canonical analyte name resolved via normalizer")
    value: Optional[float] = Field(default=None, description="Parsed numeric value")
    value_text: Optional[str] = Field(default=None, description="Original string representation of value")
    unit: Optional[str] = Field(default=None, description="Parsed unit of measurement")
    normalized_unit: Optional[str] = Field(default=None, description="Normalized canonical unit")
    extracted_reference_range: Optional[str] = Field(default=None, description="Printed reference range extracted from line, if any")
    status: ParserStatus = Field(..., description="Extraction outcome status")
    warnings: List[str] = Field(default_factory=list, description="Parsing warnings or ambiguity notices")
    extraction_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in text parsing only. NEVER represents clinical or diagnostic confidence.",
    )

    def to_test_measurement(self, context: Optional[PatientContext] = None) -> TestMeasurement:
        """Convert parsed measurement to TestMeasurement for ReferenceAnalyzer."""
        return TestMeasurement(
            test_name=self.canonical_name or self.raw_analyte or "Unknown",
            value=self.value if self.value is not None else self.value_text,
            unit=self.normalized_unit or self.unit,
            context=context,
        )

