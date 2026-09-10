"""
MedIntel AI — Phase 6 Unit Tests: Medical Reference Analysis.

Tests verify:
    1. Normal result classification
    2. Low result classification
    3. High result classification
    4. Critical low result classification
    5. Critical high result classification
    6. Exact lower normal boundary inclusivity
    7. Exact upper normal boundary inclusivity
    8. Exact critical boundaries (default vs. inclusive mode)
    9. Missing value handling (None, empty string, whitespace)
    10. Non-numeric value handling ("pending", "N/A", text)
    11. Qualitative result handling ("Positive", "Negative", "Reactive", "Trace")
    12. Unsupported / unrecognized test name
    13. Missing / empty test name
    14. Unsupported and mismatched unit (zero silent conversions)
    15. Unit normalization tolerance (casing, spacing, standard equivalents)
    16. Deterministic alias normalization (Hb, Hgb, WBC, TLC, FBS, Plt)
    17. Prohibition of fuzzy matching (Sodium != Potassium)
    18. Negative value physiological rejection
    19. Demographic context resolution (Male vs. Female ranges for Hb and Creatinine)
    20. Missing context fallback with audit warnings
    21. Analytes with no acute critical thresholds (Total Cholesterol, HbA1c)
    22. Batch analysis (analyze_many) with shared context
    23. Mandatory medical safety disclaimer presence
    24. Strict non-diagnostic safety guarantee (no disease names or treatment advice)
"""

import sys
from pathlib import Path
import pytest

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from reference.analyzer import ReferenceAnalyzer
from reference.models import (
    AnalysisResult,
    AnalysisStatus,
    Classification,
    PatientContext,
    ReferenceRange,
    TestMeasurement,
)
from reference.normalizer import AnalyteNormalizer
from reference.ranges import ReferenceRangeRegistry, get_default_registry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer() -> ReferenceAnalyzer:
    """Default ReferenceAnalyzer fixture with core 10 analytes."""
    return ReferenceAnalyzer()


@pytest.fixture
def inclusive_analyzer() -> ReferenceAnalyzer:
    """Analyzer with critical_inclusive=True."""
    return ReferenceAnalyzer(critical_inclusive=True)


# ---------------------------------------------------------------------------
# 1-5. Classification Categories: Normal, Low, High, Critical
# ---------------------------------------------------------------------------

class TestClassificationCategories:
    """Tests standard clinical interval classifications."""

    def test_normal_glucose(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=85.0, unit="mg/dL")
        assert res.status == AnalysisStatus.SUCCESS
        assert res.classification == Classification.NORMAL
        assert res.canonical_name == "Fasting Blood Glucose"

    def test_low_glucose(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=62.0, unit="mg/dL")
        assert res.status == AnalysisStatus.SUCCESS
        assert res.classification == Classification.LOW

    def test_high_glucose(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=145.0, unit="mg/dL")
        assert res.status == AnalysisStatus.SUCCESS
        assert res.classification == Classification.HIGH

    def test_critical_low_glucose(self, analyzer: ReferenceAnalyzer):
        # Critical low threshold is 50.0 mg/dL
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=42.0, unit="mg/dL")
        assert res.status == AnalysisStatus.SUCCESS
        assert res.classification == Classification.CRITICAL

    def test_critical_high_glucose(self, analyzer: ReferenceAnalyzer):
        # Critical high threshold is 400.0 mg/dL
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=480.0, unit="mg/dL")
        assert res.status == AnalysisStatus.SUCCESS
        assert res.classification == Classification.CRITICAL

    def test_critical_potassium(self, analyzer: ReferenceAnalyzer):
        # Potassium critical low < 2.8, critical high > 6.2
        crit_low = analyzer.analyze(test_name="Potassium", value=2.4, unit="mEq/L")
        assert crit_low.classification == Classification.CRITICAL

        crit_high = analyzer.analyze(test_name="Potassium", value=6.8, unit="mEq/L")
        assert crit_high.classification == Classification.CRITICAL

    def test_critical_platelets(self, analyzer: ReferenceAnalyzer):
        # Platelets critical low < 50,000
        crit_low = analyzer.analyze(test_name="Platelets", value=35000, unit="cells/uL")
        assert crit_low.classification == Classification.CRITICAL


# ---------------------------------------------------------------------------
# 6-8. Boundary Inclusivity (Normal and Critical Boundaries)
# ---------------------------------------------------------------------------

class TestBoundaryInclusivity:
    """Verifies exact numerical boundary behaviors."""

    def test_exact_normal_low_boundary_is_normal(self, analyzer: ReferenceAnalyzer):
        # Normal low for Fasting Glucose is 70.0 mg/dL
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=70.0, unit="mg/dL")
        assert res.classification == Classification.NORMAL

    def test_just_below_normal_low_is_low(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=69.9, unit="mg/dL")
        assert res.classification == Classification.LOW

    def test_exact_normal_high_boundary_is_normal(self, analyzer: ReferenceAnalyzer):
        # Normal high for Fasting Glucose is 99.0 mg/dL
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=99.0, unit="mg/dL")
        assert res.classification == Classification.NORMAL

    def test_just_above_normal_high_is_high(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Fasting Blood Glucose", value=99.1, unit="mg/dL")
        assert res.classification == Classification.HIGH

    def test_default_exact_critical_boundaries(self, analyzer: ReferenceAnalyzer):
        # Default: critical_low is < c_low; exact c_low falls into LOW
        res_low = analyzer.analyze(test_name="Fasting Blood Glucose", value=50.0, unit="mg/dL")
        assert res_low.classification == Classification.LOW

        # Default: critical_high is > c_high; exact c_high falls into HIGH (<= c_high)
        res_high = analyzer.analyze(test_name="Fasting Blood Glucose", value=400.0, unit="mg/dL")
        assert res_high.classification == Classification.HIGH

    def test_inclusive_exact_critical_boundaries(self, inclusive_analyzer: ReferenceAnalyzer):
        # Inclusive mode: <= c_low is CRITICAL
        res_low = inclusive_analyzer.analyze(test_name="Fasting Blood Glucose", value=50.0, unit="mg/dL")
        assert res_low.classification == Classification.CRITICAL

        # Inclusive mode: >= c_high is CRITICAL
        res_high = inclusive_analyzer.analyze(test_name="Fasting Blood Glucose", value=400.0, unit="mg/dL")
        assert res_high.classification == Classification.CRITICAL


# ---------------------------------------------------------------------------
# 9-11. Edge Cases: Missing, Non-Numeric, and Qualitative Results
# ---------------------------------------------------------------------------

class TestEdgeCasesValueParsing:
    """Verifies robust handling of missing, unparseable, and qualitative inputs."""

    def test_missing_value_none(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Glucose", value=None, unit="mg/dL")
        assert res.status == AnalysisStatus.VALUE_MISSING
        assert res.classification is None
        assert "missing or empty" in res.warnings[0].lower()

    def test_missing_value_empty_string(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Glucose", value="", unit="mg/dL")
        assert res.status == AnalysisStatus.VALUE_MISSING

        res_spaces = analyzer.analyze(test_name="Glucose", value="   ", unit="mg/dL")
        assert res_spaces.status == AnalysisStatus.VALUE_MISSING

    def test_non_numeric_value_string(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Glucose", value="pending", unit="mg/dL")
        assert res.status == AnalysisStatus.VALUE_NON_NUMERIC
        assert res.classification is None
        assert "cannot be parsed" in res.warnings[0].lower()

    def test_qualitative_result_detection(self, analyzer: ReferenceAnalyzer):
        for term in ["Positive", "negative", "Reactive", "Non-reactive", "Trace", "Nil"]:
            res = analyzer.analyze(test_name="Glucose", value=term, unit="mg/dL")
            assert res.status == AnalysisStatus.QUALITATIVE_RESULT
            assert res.classification is None
            assert "qualitative result" in res.warnings[0].lower()


# ---------------------------------------------------------------------------
# 12-13. Unsupported and Missing Test Names
# ---------------------------------------------------------------------------

class TestUnsupportedAnalytes:
    """Verifies handling when analyte is unknown or unspecified."""

    def test_unsupported_test_name(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="UnknownEnzyme42", value=12.5, unit="U/L")
        assert res.status == AnalysisStatus.REFERENCE_NOT_AVAILABLE
        assert res.classification is None
        assert "no reference range configured" in res.warnings[0].lower()

    def test_missing_test_name(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="", value=12.5, unit="mg/dL")
        assert res.status == AnalysisStatus.REFERENCE_NOT_AVAILABLE

        res_none = analyzer.analyze(test_name=None, value=12.5, unit="mg/dL")
        assert res_none.status == AnalysisStatus.REFERENCE_NOT_AVAILABLE


# ---------------------------------------------------------------------------
# 14-15. Unit Handling & Zero Silent Conversions
# ---------------------------------------------------------------------------

class TestUnitHandling:
    """Verifies strict unit matching, normalization, and prohibition of silent conversion."""

    def test_unit_mismatch_rejection(self, analyzer: ReferenceAnalyzer):
        # Glucose configured in mg/dL; user provides mmol/L
        res = analyzer.analyze(test_name="Glucose", value=5.5, unit="mmol/L")
        assert res.status == AnalysisStatus.UNIT_MISMATCH
        assert res.classification is None
        assert "does not match reference unit" in res.warnings[0]
        assert "automatic unit conversion is not enabled" in res.warnings[0].lower()

    def test_missing_unit_rejection(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Glucose", value=85.0, unit=None)
        assert res.status == AnalysisStatus.UNKNOWN_UNIT
        assert res.classification is None
        assert "no unit provided" in res.warnings[0].lower()

    def test_unit_normalization_tolerance(self, analyzer: ReferenceAnalyzer):
        # Case, space, and format tolerance without altering dimensionality
        for unit_str in ["mg/dl", "MG/DL", "mg / dL", "mg/dL "]:
            res = analyzer.analyze(test_name="Glucose", value=85.0, unit=unit_str)
            assert res.status == AnalysisStatus.SUCCESS
            assert res.classification == Classification.NORMAL
            assert res.normalized_unit == "mg/dL"

    def test_wbc_unit_synonyms(self, analyzer: ReferenceAnalyzer):
        for unit_str in ["cells/ul", "cells/cumm", "/cumm", "/uL"]:
            res = analyzer.analyze(test_name="WBC", value=6500, unit=unit_str)
            assert res.status == AnalysisStatus.SUCCESS
            assert res.classification == Classification.NORMAL
            assert res.normalized_unit == "cells/uL"


# ---------------------------------------------------------------------------
# 16-17. Alias Normalization and No-Fuzzy-Matching Safety
# ---------------------------------------------------------------------------

class TestAliasNormalization:
    """Verifies deterministic alias matching and absence of dangerous fuzzy matching."""

    def test_hemoglobin_aliases(self, analyzer: ReferenceAnalyzer):
        for alias in ["Hb", "Hgb", "haemoglobin", "blood hemoglobin", "HB", "hgb"]:
            res = analyzer.analyze(test_name=alias, value=14.5, unit="g/dL")
            assert res.status == AnalysisStatus.SUCCESS
            assert res.canonical_name == "Hemoglobin"

    def test_glucose_aliases(self, analyzer: ReferenceAnalyzer):
        for alias in ["FBS", "fbs", "fasting glucose", "fbg", "fasting blood sugar"]:
            res = analyzer.analyze(test_name=alias, value=85.0, unit="mg/dL")
            assert res.status == AnalysisStatus.SUCCESS
            assert res.canonical_name == "Fasting Blood Glucose"

    def test_wbc_aliases(self, analyzer: ReferenceAnalyzer):
        for alias in ["WBC", "wbc", "TLC", "tlc", "total leukocyte count", "white blood cells"]:
            res = analyzer.analyze(test_name=alias, value=7000, unit="cells/uL")
            assert res.status == AnalysisStatus.SUCCESS
            assert res.canonical_name == "White Blood Cell Count"

    def test_strictly_no_fuzzy_matching(self, analyzer: ReferenceAnalyzer):
        # Sodium and Potassium are dangerously similar in text but opposite electrolytes
        normalizer = analyzer.normalizer
        assert normalizer.get_canonical_name("Sodum") is None  # Typo must not match Sodium
        assert normalizer.get_canonical_name("Potasium") is None  # Typo must not match Potassium
        assert normalizer.get_canonical_name("Sodium") == "Serum Sodium"
        assert normalizer.get_canonical_name("Potassium") == "Serum Potassium"


# ---------------------------------------------------------------------------
# 18. Physiological Sanity Checking (Negative Values)
# ---------------------------------------------------------------------------

class TestPhysiologicalSanity:
    """Verifies negative values are rejected for non-negative analytes."""

    def test_negative_glucose_rejected(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Glucose", value=-15.0, unit="mg/dL")
        assert res.status == AnalysisStatus.INVALID_VALUE
        assert res.classification is None
        assert "physiologically invalid" in res.warnings[0].lower()

    def test_negative_hemoglobin_rejected(self, analyzer: ReferenceAnalyzer):
        res = analyzer.analyze(test_name="Hemoglobin", value=-2.0, unit="g/dL")
        assert res.status == AnalysisStatus.INVALID_VALUE
        assert res.classification is None


# ---------------------------------------------------------------------------
# 19-20. Demographic Context Resolution (Sex and Age)
# ---------------------------------------------------------------------------

class TestDemographicContext:
    """Verifies resolution of sex-specific reference ranges."""

    def test_hemoglobin_male_context(self, analyzer: ReferenceAnalyzer):
        # Male normal: 13.8 - 17.2 g/dL
        res_m = analyzer.analyze(
            test_name="Hemoglobin",
            value=13.0,
            unit="g/dL",
            context=PatientContext(sex="M"),
        )
        assert res_m.classification == Classification.LOW  # Below 13.8

    def test_hemoglobin_female_context(self, analyzer: ReferenceAnalyzer):
        # Female normal: 12.1 - 15.1 g/dL
        res_f = analyzer.analyze(
            test_name="Hemoglobin",
            value=13.0,
            unit="g/dL",
            context=PatientContext(sex="F"),
        )
        assert res_f.classification == Classification.NORMAL  # Within 12.1 - 15.1

    def test_hemoglobin_missing_context_fallback(self, analyzer: ReferenceAnalyzer):
        # General adult fallback: 12.0 - 17.5 g/dL with warning
        res = analyzer.analyze(test_name="Hemoglobin", value=13.0, unit="g/dL")
        assert res.classification == Classification.NORMAL
        assert any("sex not specified" in w.lower() for w in res.warnings)

    def test_creatinine_sex_stratification(self, analyzer: ReferenceAnalyzer):
        # Male normal: 0.7 - 1.3; Female normal: 0.6 - 1.1
        # 1.2 mg/dL is NORMAL for male, but HIGH for female
        res_m = analyzer.analyze(
            test_name="Creatinine",
            value=1.2,
            unit="mg/dL",
            context={"sex": "M"},
        )
        assert res_m.classification == Classification.NORMAL

        res_f = analyzer.analyze(
            test_name="Creatinine",
            value=1.2,
            unit="mg/dL",
            context={"sex": "F"},
        )
        assert res_f.classification == Classification.HIGH

    def test_strict_context_required_without_fallback(self):
        # Test case: custom registry where an analyte ONLY has sex-specific ranges and NO fallback
        custom_registry = ReferenceRangeRegistry()
        custom_registry.register(
            ReferenceRange(
                canonical_name="CustomTest",
                unit="mg/dL",
                normal_low=10.0,
                normal_high=20.0,
                applicable_sex="M",
                source="Custom Guidelines",
            )
        )
        custom_registry.register(
            ReferenceRange(
                canonical_name="CustomTest",
                unit="mg/dL",
                normal_low=5.0,
                normal_high=15.0,
                applicable_sex="F",
                source="Custom Guidelines",
            )
        )
        custom_analyzer = ReferenceAnalyzer(registry=custom_registry)

        res_missing = custom_analyzer.analyze(test_name="CustomTest", value=12.0, unit="mg/dL")
        assert res_missing.status == AnalysisStatus.CONTEXT_REQUIRED
        assert res_missing.classification is None
        assert "biological sex" in res_missing.warnings[0].lower()


# ---------------------------------------------------------------------------
# 21. Analytes Without Acute Critical Thresholds
# ---------------------------------------------------------------------------

class TestNonCriticalAnalytes:
    """Confirms no critical thresholds are fabricated for chronic risk analytes."""

    def test_total_cholesterol_elevated_never_critical(self, analyzer: ReferenceAnalyzer):
        # Total cholesterol normal <= 200 mg/dL. 380 mg/dL is extremely high, but NOT acute panic value
        res = analyzer.analyze(test_name="Total Cholesterol", value=380.0, unit="mg/dL")
        assert res.classification == Classification.HIGH
        assert res.reference_range.critical_high is None
        assert res.reference_range.critical_low is None

    def test_hba1c_elevated_never_critical(self, analyzer: ReferenceAnalyzer):
        # HbA1c normal <= 5.6%. 11.5% is high, but not acute critical panic threshold
        res = analyzer.analyze(test_name="HbA1c", value=11.5, unit="%")
        assert res.classification == Classification.HIGH
        assert res.reference_range.critical_high is None


# ---------------------------------------------------------------------------
# 22. Batch Analysis (analyze_many)
# ---------------------------------------------------------------------------

class TestBatchAnalysis:
    """Verifies batch evaluation of multiple measurements."""

    def test_analyze_many_with_shared_context(self, analyzer: ReferenceAnalyzer):
        measurements = [
            {"test_name": "FBS", "value": 90.0, "unit": "mg/dL"},
            {"test_name": "Hb", "value": 14.5, "unit": "g/dL"},
            {"test_name": "WBC", "value": 6500, "unit": "cells/uL"},
            {"test_name": "Creatinine", "value": 1.0, "unit": "mg/dL"},
        ]
        results = analyzer.analyze_many(measurements, context={"sex": "M"})
        assert len(results) == 4
        for r in results:
            assert r.status == AnalysisStatus.SUCCESS
            assert r.classification == Classification.NORMAL


# ---------------------------------------------------------------------------
# 23-24. Medical Safety and Non-Diagnostic Guarantees
# ---------------------------------------------------------------------------

class TestMedicalSafetyGuarantees:
    """Verifies absolute compliance with project safety rules."""

    def test_mandatory_disclaimer_present_on_all_results(self, analyzer: ReferenceAnalyzer):
        results = [
            analyzer.analyze(test_name="Glucose", value=85.0, unit="mg/dL"),
            analyzer.analyze(test_name="Glucose", value=None, unit="mg/dL"),
            analyzer.analyze(test_name="Unknown", value=10.0, unit="mg/dL"),
            analyzer.analyze(test_name="Glucose", value=5.5, unit="mmol/L"),
        ]
        expected_disclaimer = (
            "This is not a medical diagnosis. Please consult a qualified healthcare professional."
        )
        for r in results:
            assert r.disclaimer == expected_disclaimer

    def test_classification_enum_strictly_restricted(self):
        allowed_classifications = {"LOW", "NORMAL", "HIGH", "CRITICAL"}
        for c in Classification:
            assert c.value in allowed_classifications

    def test_zero_disease_diagnosis_outputs(self, analyzer: ReferenceAnalyzer):
        # Even with extreme values, the engine must NEVER diagnose
        extreme_res = analyzer.analyze(test_name="Glucose", value=550.0, unit="mg/dL")
        full_repr = extreme_res.model_dump_json().lower()

        # Must not contain disease diagnostic statements
        forbidden_phrases = [
            "you have diabetes",
            "diabetes mellitus diagnosis",
            "you have kidney disease",
            "you have anemia",
            "prescribe",
            "take medication",
            "treatment recommendation",
        ]
        for phrase in forbidden_phrases:
            assert phrase not in full_repr
