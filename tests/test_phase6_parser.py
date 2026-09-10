"""
MedIntel AI — Phase 6 Unit Tests: Deterministic Medical Value Parser.

Tests verify:
    1. "FBS: 92 mg/dL"
    2. "Fasting Blood Glucose 105 mg/dL"
    3. "Hb 14.2 g/dL"
    4. "Hemoglobin - 11.5 g/dL"
    5. "WBC 8500 cells/uL"
    6. "Platelet Count: 220000 /uL"
    7. "Potassium 4.2 mEq/L"
    8. "Sodium 140 mEq/L"
    9. "Creatinine 1.0 mg/dL"
    10. "BUN 15 mg/dL"
    11. "HbA1c 5.4 %"
    12. Leading decimal parsing (".95")
    13. Uppercase/lowercase unit variants ("mg/dl", "MG/DL", "mg / dL")
    14. Spacing variations around units ("14.2 g/dL", "14.2g/dL", "14.2  g / dL")
    15. Colon separator
    16. Hyphen separator
    17. Equals separator
    18. Reference ranges present on the same line ("Glucose 92 mg/dL 70-99", "Hemoglobin 14.2 g/dL (13.8-17.2)")
    19. Missing value handling
    20. Missing unit handling
    21. Qualitative results handling ("Positive", "Negative", "Reactive")
    22. Unsupported analyte handling
    23. Ambiguous multiple candidate numeric values
    24. OCR whitespace and tab noise
    25. Full deterministic pipeline (raw text -> parser -> analyzer -> AnalysisResult)
    26. Absolute non-diagnostic guarantee across the entire pipeline
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
    ParsedMeasurement,
    ParserStatus,
    PatientContext,
)
from reference.parser import MedicalValueParser


@pytest.fixture
def parser() -> MedicalValueParser:
    """Default MedicalValueParser instance."""
    return MedicalValueParser()


@pytest.fixture
def analyzer() -> ReferenceAnalyzer:
    """Default ReferenceAnalyzer instance."""
    return ReferenceAnalyzer()


# ---------------------------------------------------------------------------
# 1-11. Standard Clinical Measurement Line Patterns
# ---------------------------------------------------------------------------

class TestStandardMeasurementPatterns:
    """Verifies parsing of the 11 core clinical formats."""

    def test_case_01_fbs_colon(self, parser: MedicalValueParser):
        res = parser.parse_line("FBS: 92 mg/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Fasting Blood Glucose"
        assert res.value == 92.0
        assert res.normalized_unit == "mg/dL"

    def test_case_02_fasting_blood_glucose_space(self, parser: MedicalValueParser):
        res = parser.parse_line("Fasting Blood Glucose 105 mg/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Fasting Blood Glucose"
        assert res.value == 105.0
        assert res.normalized_unit == "mg/dL"

    def test_case_03_hb_space(self, parser: MedicalValueParser):
        res = parser.parse_line("Hb 14.2 g/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Hemoglobin"
        assert res.value == 14.2
        assert res.normalized_unit == "g/dL"

    def test_case_04_hemoglobin_hyphen(self, parser: MedicalValueParser):
        res = parser.parse_line("Hemoglobin - 11.5 g/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Hemoglobin"
        assert res.value == 11.5
        assert res.normalized_unit == "g/dL"

    def test_case_05_wbc_cells_ul(self, parser: MedicalValueParser):
        res = parser.parse_line("WBC 8500 cells/uL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "White Blood Cell Count"
        assert res.value == 8500.0
        assert res.normalized_unit == "cells/uL"

    def test_case_06_platelet_count_slash_ul(self, parser: MedicalValueParser):
        res = parser.parse_line("Platelet Count: 220000 /uL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Platelet Count"
        assert res.value == 220000.0
        assert res.normalized_unit == "cells/uL"

    def test_case_07_potassium_meq_l(self, parser: MedicalValueParser):
        res = parser.parse_line("Potassium 4.2 mEq/L")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Serum Potassium"
        assert res.value == 4.2
        assert res.normalized_unit == "mEq/L"

    def test_case_08_sodium_meq_l(self, parser: MedicalValueParser):
        res = parser.parse_line("Sodium 140 mEq/L")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Serum Sodium"
        assert res.value == 140.0
        assert res.normalized_unit == "mEq/L"

    def test_case_09_creatinine_mg_dl(self, parser: MedicalValueParser):
        res = parser.parse_line("Creatinine 1.0 mg/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Serum Creatinine"
        assert res.value == 1.0
        assert res.normalized_unit == "mg/dL"

    def test_case_10_bun_mg_dl(self, parser: MedicalValueParser):
        res = parser.parse_line("BUN 15 mg/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Blood Urea Nitrogen"
        assert res.value == 15.0
        assert res.normalized_unit == "mg/dL"

    def test_case_11_hba1c_percent(self, parser: MedicalValueParser):
        res = parser.parse_line("HbA1c 5.4 %")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Glycated Hemoglobin"
        assert res.value == 5.4
        assert res.normalized_unit == "%"


# ---------------------------------------------------------------------------
# 12-17. Formatting Variations: Decimals, Separators, Spacing, Units
# ---------------------------------------------------------------------------

class TestFormattingVariations:
    """Verifies numeric notation, separators, and OCR unit noise tolerance."""

    def test_case_12_leading_decimal(self, parser: MedicalValueParser):
        res = parser.parse_line("Creatinine .95 mg/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.value == 0.95
        assert res.canonical_name == "Serum Creatinine"

    def test_case_13_unit_casing_variants(self, parser: MedicalValueParser):
        for line, expected_norm in [
            ("Glucose: 95 mg/dl", "mg/dL"),
            ("Glucose: 95 MG/DL", "mg/dL"),
            ("Glucose: 95 Mg/dL", "mg/dL"),
            ("WBC: 6000 CELLS/UL", "cells/uL"),
            ("WBC: 6000 /cumm", "cells/uL"),
        ]:
            res = parser.parse_line(line)
            assert res.status == ParserStatus.SUCCESS
            assert res.normalized_unit == expected_norm

    def test_case_14_unit_spacing_variations(self, parser: MedicalValueParser):
        # Spacing around units: normal space, no space, multi-space
        res_no_space = parser.parse_line("Hb 14.2g/dL")
        assert res_no_space.status == ParserStatus.SUCCESS
        assert res_no_space.value == 14.2
        assert res_no_space.normalized_unit == "g/dL"

        res_wide_space = parser.parse_line("Hb 14.2   g / dL")
        assert res_wide_space.status == ParserStatus.SUCCESS
        assert res_wide_space.value == 14.2
        assert res_wide_space.normalized_unit == "g/dL"

    def test_case_15_colon_separator(self, parser: MedicalValueParser):
        res = parser.parse_line("Total Cholesterol: 185 mg/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Total Cholesterol"
        assert res.value == 185.0

    def test_case_16_hyphen_separator(self, parser: MedicalValueParser):
        res = parser.parse_line("Total Cholesterol - 185 mg/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Total Cholesterol"
        assert res.value == 185.0

    def test_case_17_equals_separator(self, parser: MedicalValueParser):
        res = parser.parse_line("Creatinine = 1.05 mg/dL")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Serum Creatinine"
        assert res.value == 1.05

    def test_comma_in_large_numbers(self, parser: MedicalValueParser):
        res_platelets = parser.parse_line("Platelets: 220,000 /uL")
        assert res_platelets.status == ParserStatus.SUCCESS
        assert res_platelets.value == 220000.0


# ---------------------------------------------------------------------------
# 18. Range-Text Segregation
# ---------------------------------------------------------------------------

class TestRangeTextSegregation:
    """Verifies printed reference ranges are captured without corrupting measured value."""

    def test_case_18_trailing_range(self, parser: MedicalValueParser):
        res = parser.parse_line("Glucose 92 mg/dL 70-99")
        assert res.status == ParserStatus.SUCCESS
        assert res.value == 92.0
        assert res.normalized_unit == "mg/dL"
        assert res.extracted_reference_range == "70-99"

    def test_case_18_parenthesized_range(self, parser: MedicalValueParser):
        res = parser.parse_line("Hemoglobin 14.2 g/dL (13.8-17.2)")
        assert res.status == ParserStatus.SUCCESS
        assert res.value == 14.2
        assert res.normalized_unit == "g/dL"
        assert res.extracted_reference_range == "(13.8-17.2)"

    def test_case_18_wbc_trailing_range(self, parser: MedicalValueParser):
        res = parser.parse_line("WBC 8500 /uL 4000-11000")
        assert res.status == ParserStatus.SUCCESS
        assert res.value == 8500.0
        assert res.normalized_unit == "cells/uL"
        assert res.extracted_reference_range == "4000-11000"

    def test_case_18_bracketed_range(self, parser: MedicalValueParser):
        res = parser.parse_line("Serum Potassium: 4.2 mEq/L [3.5 - 5.0]")
        assert res.status == ParserStatus.SUCCESS
        assert res.value == 4.2
        assert res.extracted_reference_range == "[3.5 - 5.0]"

    def test_case_18_inequality_bound_range(self, parser: MedicalValueParser):
        res = parser.parse_line("Total Cholesterol: 190 mg/dL < 200")
        assert res.status == ParserStatus.SUCCESS
        assert res.value == 190.0
        assert res.extracted_reference_range == "< 200"


# ---------------------------------------------------------------------------
# 19-24. Edge Cases: Missing, Qualitative, Unsupported, Ambiguity, Noise
# ---------------------------------------------------------------------------

class TestEdgeCasesAndAmbiguity:
    """Verifies boundary conditions, incomplete lines, and noise."""

    def test_case_19_missing_value(self, parser: MedicalValueParser):
        res = parser.parse_line("Glucose: ")
        assert res.status == ParserStatus.VALUE_MISSING
        assert res.value is None
        assert res.canonical_name == "Fasting Blood Glucose"

    def test_case_20_missing_unit(self, parser: MedicalValueParser):
        res = parser.parse_line("Glucose 92")
        assert res.status == ParserStatus.UNKNOWN_UNIT
        assert res.value == 92.0
        assert res.unit is None
        assert any("no unit" in w.lower() for w in res.warnings)

    def test_case_21_qualitative_results(self, parser: MedicalValueParser):
        for term in ["Negative", "Positive", "Reactive", "Non-reactive", "Trace", "Nil"]:
            res = parser.parse_line(f"Glucose: {term}")
            assert res.status == ParserStatus.QUALITATIVE_RESULT
            assert res.value is None
            assert res.value_text == term

    def test_case_22_unsupported_analyte(self, parser: MedicalValueParser):
        res = parser.parse_line("UnknownEnzyme: 12.5 U/L")
        assert res.status == ParserStatus.UNRECOGNIZED_ANALYTE
        assert res.raw_analyte == "UnknownEnzyme"
        assert res.canonical_name is None

    def test_case_23_ambiguous_multiple_numeric_values(self, parser: MedicalValueParser):
        # Line with two conflicting numbers that do not match reference range patterns
        res = parser.parse_line("FBS: 92 105 mg/dL")
        assert res.status == ParserStatus.AMBIGUOUS
        assert res.value is None
        assert any("multiple candidate" in w.lower() for w in res.warnings)
        assert res.extraction_confidence == 0.5

    def test_case_24_ocr_whitespace_and_tab_noise(self, parser: MedicalValueParser):
        res = parser.parse_line("  \t Hb  :   14.2   g / dL  \t ")
        assert res.status == ParserStatus.SUCCESS
        assert res.canonical_name == "Hemoglobin"
        assert res.value == 14.2
        assert res.normalized_unit == "g/dL"


# ---------------------------------------------------------------------------
# 25-26. Full Deterministic Pipeline & Non-Diagnostic Guarantee
# ---------------------------------------------------------------------------

class TestFullDeterministicPipeline:
    """Verifies end-to-end processing: raw text -> parser -> analyzer -> classification."""

    def test_end_to_end_single_line_pipeline(
        self,
        parser: MedicalValueParser,
        analyzer: ReferenceAnalyzer,
    ):
        raw_text = "FBS: 105 mg/dL"
        parsed = parser.parse_line(raw_text)
        assert parsed.status == ParserStatus.SUCCESS

        measurement_input = parsed.to_test_measurement()
        analysis = analyzer.analyze(measurement_input)

        assert analysis.status == AnalysisStatus.SUCCESS
        assert analysis.canonical_name == "Fasting Blood Glucose"
        assert analysis.classification == Classification.HIGH
        assert analysis.reference_range is not None
        assert analysis.reference_source is not None

    def test_end_to_end_multiline_document(self, parser: MedicalValueParser):
        document_text = """
        METABOLIC & HEMATOLOGY REPORT
        =============================
        1. Fasting Blood Glucose: 92.0 mg/dL (70-99)
        2. Hb 14.2 g/dL (13.8-17.2)
        3. WBC: 8500 cells/uL [4000 - 11000]
        4. Serum Potassium - 4.2 mEq/L
        5. Serum Sodium 140 mEq/L
        6. Creatinine: 1.0 mg/dL
        7. BUN = 15 mg/dL
        8. Total Cholesterol: 185 mg/dL
        9. Platelet Count: 220000 /uL
        10. HbA1c: 5.4 %
        """
        pipeline_results = parser.parse_and_analyze(
            document_text,
            context=PatientContext(sex="M"),
        )

        assert len(pipeline_results) == 10

        expected_classifications = {
            "Fasting Blood Glucose": Classification.NORMAL,
            "Hemoglobin": Classification.NORMAL,
            "White Blood Cell Count": Classification.NORMAL,
            "Serum Potassium": Classification.NORMAL,
            "Serum Sodium": Classification.NORMAL,
            "Serum Creatinine": Classification.NORMAL,
            "Blood Urea Nitrogen": Classification.NORMAL,
            "Total Cholesterol": Classification.NORMAL,
            "Platelet Count": Classification.NORMAL,
            "Glycated Hemoglobin": Classification.NORMAL,
        }

        for parsed, analysis in pipeline_results:
            assert parsed.status == ParserStatus.SUCCESS
            assert analysis.status == AnalysisStatus.SUCCESS
            assert analysis.classification == expected_classifications[analysis.canonical_name]

    def test_strict_non_diagnostic_guarantee_end_to_end(self, parser: MedicalValueParser):
        # Even with critically elevated values, pipeline must never emit diagnoses
        crit_text = "FBS: 520 mg/dL"
        results = parser.parse_and_analyze(crit_text)
        assert len(results) == 1
        parsed, analysis = results[0]

        assert analysis.classification == Classification.CRITICAL

        full_json = analysis.model_dump_json().lower()
        forbidden_phrases = [
            "you have diabetes",
            "diabetes mellitus diagnosis",
            "you have kidney disease",
            "prescribe",
            "take medication",
            "treatment recommendation",
        ]
        for phrase in forbidden_phrases:
            assert phrase not in full_json

        # Must always have the safety disclaimer
        assert analysis.disclaimer == (
            "This is not a medical diagnosis. Please consult a qualified healthcare professional."
        )
