"""
MedIntel AI — Phase 6: Medical Reference Analysis Module.

Provides deterministic laboratory reference-interval analysis for extracted
and user-verified clinical measurements.

Safety Rules:
    - Never outputs disease diagnoses (e.g., 'Diabetes', 'Anemia', 'Hypertension').
    - Outputs strictly restricted to: LOW, NORMAL, HIGH, CRITICAL.
    - Mandatory medical safety disclaimer attached to every analysis result.
    - Zero silent unit conversions.
"""

from reference.analyzer import ReferenceAnalyzer
from reference.models import (
    AnalysisResult,
    AnalysisStatus,
    Classification,
    ParsedMeasurement,
    ParserStatus,
    PatientContext,
    ReferenceRange,
    ReferenceType,
    TestMeasurement,
    VerificationStatus,
)
from reference.normalizer import AnalyteNormalizer
from reference.parser import MedicalValueParser
from reference.ranges import ReferenceRangeRegistry, get_default_registry

__all__ = [
    "Classification",
    "AnalysisStatus",
    "ReferenceType",
    "VerificationStatus",
    "PatientContext",
    "ReferenceRange",
    "TestMeasurement",
    "AnalysisResult",
    "ParserStatus",
    "ParsedMeasurement",
    "AnalyteNormalizer",
    "ReferenceRangeRegistry",
    "get_default_registry",
    "ReferenceAnalyzer",
    "MedicalValueParser",
]
