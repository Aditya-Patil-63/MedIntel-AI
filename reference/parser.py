"""
MedIntel AI — Phase 6: Deterministic Medical Value Parser.

Extracts structured clinical measurements (analyte, value, unit, reference-range text)
from unstructured OCR and document text lines.

Guarantees:
    - Strictly deterministic parsing: NO LLMs, NO fuzzy matching.
    - Explicit ambiguity detection when multiple candidate numbers exist on a line.
    - Clean segregation of patient measurement from printed laboratory reference ranges.
    - Zero medical diagnoses: Extraction confidence represents text parsing quality only.
"""

import re
from typing import Dict, List, Optional, Tuple, Union

from reference.analyzer import ReferenceAnalyzer
from reference.models import (
    AnalysisResult,
    ParsedMeasurement,
    ParserStatus,
    PatientContext,
)
from reference.normalizer import AnalyteNormalizer
from reference.ranges import ReferenceRangeRegistry, get_default_registry


class MedicalValueParser:
    """
    Deterministic parser for extracting medical laboratory measurements from text.
    """

    # Reference range text patterns appearing on clinical report lines
    RANGE_PATTERNS = [
        # Parenthesized range: (70-99), (13.8 - 17.2), ( < 200 )
        r"\(\s*(?:(?:<|<=|>|>=)\s*)?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:[-–—to]+\s*\d+(?:,\d{3})*(?:\.\d+)?)?\s*\)",
        # Bracketed range: [70-99], [3.5 - 5.0]
        r"\[\s*(?:(?:<|<=|>|>=)\s*)?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:[-–—to]+\s*\d+(?:,\d{3})*(?:\.\d+)?)?\s*\]",
        # Explicit ref/range label: Ref: 70-99, Range: 4000-11000, Normal: 150000-450000
        r"(?:ref(?:erence)?|range|normal)\s*[:=]?\s*(?:(?:<|<=|>|>=)\s*)?\d+(?:,\d{3})*(?:\.\d+)?(?:\s*[-–—to]+\s*\d+(?:,\d{3})*(?:\.\d+)?)?",
        # Trailing range at end of line: e.g. " 70-99", " 70 - 99", " 4000-11000", " < 200"
        r"(?<=\s)(?:\d+(?:,\d{3})*(?:\.\d+)?\s*[-–—]\s*\d+(?:,\d{3})*(?:\.\d+)?|(?:<|<=|>|>=)\s*\d+(?:,\d{3})*(?:\.\d+)?)\s*$",
    ]

    # Regex for numerical value extraction (integers, commas, floats, leading decimals, negative)
    NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)")

    def __init__(
        self,
        normalizer: Optional[AnalyteNormalizer] = None,
        registry: Optional[ReferenceRangeRegistry] = None,
    ) -> None:
        """
        Initialize parser with normalizer and range registry.
        Compiles deterministic prefix patterns from all registered analyte aliases.
        """
        self.registry = registry or get_default_registry()
        self.normalizer = normalizer or AnalyteNormalizer()

        # Ensure all aliases from the registry are indexed in normalizer
        for range_def in self.registry.get_all_ranges():
            self.normalizer.register_aliases(
                range_def.canonical_name,
                range_def.aliases,
            )

        # Build compiled regex for registered analytes, sorted by descending length
        all_terms = set()
        for range_def in self.registry.get_all_ranges():
            all_terms.add(range_def.canonical_name)
            for alias in range_def.aliases:
                all_terms.add(alias)

        # Sort terms by length in descending order to prioritize longer phrases
        sorted_terms = sorted(list(all_terms), key=lambda x: len(x), reverse=True)
        escaped_terms = [re.escape(t) for t in sorted_terms]

        # Regex matching analyte at beginning of line (allowing list numbers/bullets)
        # Matches boundaries: word boundary or start of line, followed by separator, number, or space
        term_group = "|".join(escaped_terms)
        self._analyte_pattern = re.compile(
            r"^\s*(?:[\*\-\#]\s*|\d+[\.\)]\s*)?("
            + term_group
            + r")(?=\s*[:=]|(?:\s*-\s+)|(?:\s+[-+]?\d)|(?:\s+[-+]?\.\d)|(?:\s+(?:positive|negative|reactive|trace|nil))|\s*$)",
            re.IGNORECASE,
        )

        # General unknown analyte prefix: e.g. "UnknownTest: 12.5 U/L"
        self._generic_prefix_pattern = re.compile(
            r"^\s*(?:[\*\-\#]\s*|\d+[\.\)]\s*)?([A-Za-z0-9\+\-\s\.\(\)/]+?)\s*[:=]\s*",
            re.IGNORECASE,
        )

    def parse_line(self, line: str) -> ParsedMeasurement:
        """
        Deterministically parse a single clinical report text line.
        """
        raw_line = line
        clean_line = line.strip()

        if not clean_line:
            return ParsedMeasurement(
                raw_line=raw_line,
                status=ParserStatus.UNRECOGNIZED_ANALYTE,
                warnings=["Empty line."],
                extraction_confidence=0.0,
            )

        # 1. Match Analyte Prefix
        analyte_match = self._analyte_pattern.search(clean_line)
        raw_analyte: Optional[str] = None
        canonical_name: Optional[str] = None
        remainder: str = ""

        if analyte_match:
            raw_analyte = analyte_match.group(1).strip()
            canonical_name = self.normalizer.get_canonical_name(raw_analyte)
            remainder = clean_line[analyte_match.end():].strip()
        else:
            # Check for generic colon/equals separator with unrecognized analyte
            generic_match = self._generic_prefix_pattern.search(clean_line)
            if generic_match:
                candidate_analyte = generic_match.group(1).strip()
                canonical_name = self.normalizer.get_canonical_name(candidate_analyte)
                raw_analyte = candidate_analyte
                candidate_remainder = clean_line[generic_match.end():].strip()
                clean_candidate_remainder = re.sub(r"^(?:[:=]|\s*-\s+)\s*", "", candidate_remainder).strip()
                is_qualitative = any(
                    re.search(rf"^{re.escape(term)}(?:\b|\Z)", clean_candidate_remainder, re.IGNORECASE)
                    for term in self.normalizer.QUALITATIVE_TERMS
                )
                if canonical_name or is_qualitative:
                    remainder = candidate_remainder
                else:
                    return ParsedMeasurement(
                        raw_line=raw_line,
                        raw_analyte=candidate_analyte,
                        canonical_name=None,
                        status=ParserStatus.UNRECOGNIZED_ANALYTE,
                        warnings=[f"Unrecognized analyte '{candidate_analyte}'."],
                        extraction_confidence=0.0,
                    )
            else:
                return ParsedMeasurement(
                    raw_line=raw_line,
                    status=ParserStatus.UNRECOGNIZED_ANALYTE,
                    warnings=["No recognizable medical analyte prefix found on line."],
                    extraction_confidence=0.0,
                )

        # 2. Strip standard punctuation separators from start of remainder (:, =, - with space)
        remainder = re.sub(r"^(?:[:=]|\s*-\s+)\s*", "", remainder).strip()

        # 3. Check for Qualitative Value
        for qual_term in self.normalizer.QUALITATIVE_TERMS:
            qual_pattern = re.compile(rf"^{re.escape(qual_term)}(?:\b|\Z)", re.IGNORECASE)
            qual_match = qual_pattern.search(remainder)
            if qual_match:
                matched_term = qual_match.group(0)
                return ParsedMeasurement(
                    raw_line=raw_line,
                    raw_analyte=raw_analyte,
                    canonical_name=canonical_name,
                    value=None,
                    value_text=matched_term,
                    unit=None,
                    normalized_unit=None,
                    extracted_reference_range=None,
                    status=ParserStatus.QUALITATIVE_RESULT,
                    warnings=[f"Qualitative result '{matched_term}' detected."],
                    extraction_confidence=1.0,
                )

        # 4. Extract printed Reference Range Text from line, if present
        extracted_range: Optional[str] = None
        for pattern in self.RANGE_PATTERNS:
            range_match = re.search(pattern, remainder, re.IGNORECASE)
            if range_match:
                extracted_range = range_match.group(0).strip()
                # Remove range text from remainder so its numbers don't collide with the measured value
                remainder = remainder[:range_match.start()] + " " + remainder[range_match.end():]
                remainder = remainder.strip()
                break

        # 5. Check for Missing Value
        if not remainder:
            return ParsedMeasurement(
                raw_line=raw_line,
                raw_analyte=raw_analyte,
                canonical_name=canonical_name,
                value=None,
                value_text=None,
                unit=None,
                normalized_unit=None,
                extracted_reference_range=extracted_range,
                status=ParserStatus.VALUE_MISSING,
                warnings=["Measurement value is missing for recognized analyte."],
                extraction_confidence=0.0,
            )

        # 6. Parse Numerical Candidate Values
        num_matches = self.NUMBER_PATTERN.findall(remainder)

        if len(num_matches) == 0:
            return ParsedMeasurement(
                raw_line=raw_line,
                raw_analyte=raw_analyte,
                canonical_name=canonical_name,
                value=None,
                value_text=remainder,
                unit=None,
                normalized_unit=None,
                extracted_reference_range=extracted_range,
                status=ParserStatus.VALUE_MISSING,
                warnings=[f"No numeric value found in text: '{remainder}'."],
                extraction_confidence=0.0,
            )

        if len(num_matches) > 1:
            # Ambiguity: multiple candidate numbers on line outside of recognized reference range
            return ParsedMeasurement(
                raw_line=raw_line,
                raw_analyte=raw_analyte,
                canonical_name=canonical_name,
                value=None,
                value_text=" / ".join(num_matches),
                unit=None,
                normalized_unit=None,
                extracted_reference_range=extracted_range,
                status=ParserStatus.AMBIGUOUS,
                warnings=["Multiple candidate numeric values detected on line; cannot unambiguously determine measurement."],
                extraction_confidence=0.5,
            )

        # Exactly 1 numerical value found
        num_str = num_matches[0]
        try:
            cleaned_num_str = num_str.replace(",", "")
            numeric_value = float(cleaned_num_str)
        except ValueError:
            return ParsedMeasurement(
                raw_line=raw_line,
                raw_analyte=raw_analyte,
                canonical_name=canonical_name,
                value=None,
                value_text=num_str,
                unit=None,
                normalized_unit=None,
                extracted_reference_range=extracted_range,
                status=ParserStatus.VALUE_MISSING,
                warnings=[f"Failed to parse '{num_str}' as float."],
                extraction_confidence=0.0,
            )

        # 7. Extract Unit Candidate from Remainder
        # Replace the matched number token with empty string
        unit_text = self.NUMBER_PATTERN.sub("", remainder, count=1).strip()
        # Clean unit candidate (remove leading/trailing separators)
        unit_text = re.sub(r"^[:=\-\s]+", "", unit_text).strip()

        if not unit_text:
            return ParsedMeasurement(
                raw_line=raw_line,
                raw_analyte=raw_analyte,
                canonical_name=canonical_name,
                value=numeric_value,
                value_text=num_str,
                unit=None,
                normalized_unit=None,
                extracted_reference_range=extracted_range,
                status=ParserStatus.UNKNOWN_UNIT,
                warnings=["No unit detected for measurement on line."],
                extraction_confidence=0.85,
            )

        # Normalize unit
        normalized_unit = self.normalizer.normalize_unit(unit_text)

        return ParsedMeasurement(
            raw_line=raw_line,
            raw_analyte=raw_analyte,
            canonical_name=canonical_name,
            value=numeric_value,
            value_text=num_str,
            unit=unit_text,
            normalized_unit=normalized_unit,
            extracted_reference_range=extracted_range,
            status=ParserStatus.SUCCESS,
            warnings=[],
            extraction_confidence=1.0,
        )

    def parse_text(
        self,
        document_text: str,
        include_unrecognized: bool = False,
    ) -> List[ParsedMeasurement]:
        """
        Parse multi-line document text into structured measurements.
        """
        results: List[ParsedMeasurement] = []
        for line in document_text.splitlines():
            clean = line.strip()
            if not clean:
                continue
            parsed = self.parse_line(line)
            if parsed.status == ParserStatus.UNRECOGNIZED_ANALYTE and not include_unrecognized:
                continue
            results.append(parsed)
        return results

    def parse_and_analyze(
        self,
        document_text: str,
        analyzer: Optional[ReferenceAnalyzer] = None,
        context: Optional[PatientContext] = None,
    ) -> List[Tuple[ParsedMeasurement, AnalysisResult]]:
        """
        End-to-end deterministic pipeline:
        Raw Text Line -> ParsedMeasurement -> ReferenceAnalyzer -> AnalysisResult
        """
        active_analyzer = analyzer or ReferenceAnalyzer(
            registry=self.registry,
            normalizer=self.normalizer,
        )

        pipeline_results: List[Tuple[ParsedMeasurement, AnalysisResult]] = []
        parsed_measurements = self.parse_text(document_text, include_unrecognized=False)

        for parsed in parsed_measurements:
            meas_input = parsed.to_test_measurement(context=context)
            analysis = active_analyzer.analyze(meas_input)
            pipeline_results.append((parsed, analysis))

        return pipeline_results
