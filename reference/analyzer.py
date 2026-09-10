"""
MedIntel AI — Phase 6: Deterministic Medical Reference Analyzer.

Evaluates extracted or verified laboratory measurements against authoritative
reference intervals.

Guarantees:
    - Strictly non-diagnostic: Outputs ONLY LOW, NORMAL, HIGH, CRITICAL.
    - Zero disease predictions or treatment advice.
    - Transparent boundary logic with explicit boundary inclusivity.
    - Full audit trail preserved on every analysis result.
    - Mandatory medical disclaimer included on every response.
"""

from typing import Any, Dict, List, Optional, Union

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


class ReferenceAnalyzer:
    """
    Deterministic reference-range classification engine.
    """

    MANDATORY_DISCLAIMER: str = (
        "This is not a medical diagnosis. Please consult a qualified healthcare professional."
    )

    def __init__(
        self,
        registry: Optional[ReferenceRangeRegistry] = None,
        normalizer: Optional[AnalyteNormalizer] = None,
        critical_inclusive: bool = False,
    ) -> None:
        """
        Initialize the analyzer with a range registry and normalizer.

        Args:
            registry: ReferenceRangeRegistry containing analyte definitions.
                      Defaults to get_default_registry().
            normalizer: AnalyteNormalizer for test and unit alias resolution.
                        If None, builds a normalizer pre-populated with all registry aliases.
            critical_inclusive: If True, values exactly on critical boundaries are classified
                                as CRITICAL (<= critical_low, >= critical_high).
                                If False (default), values must be strictly beyond critical
                                boundaries (< critical_low, > critical_high).
        """
        self.registry = registry or get_default_registry()
        self.critical_inclusive = critical_inclusive

        if normalizer is not None:
            self.normalizer = normalizer
        else:
            self.normalizer = AnalyteNormalizer()
            # Auto-register all aliases from the registry
            for range_def in self.registry.get_all_ranges():
                self.normalizer.register_aliases(
                    range_def.canonical_name,
                    range_def.aliases,
                )

    def classify_value(
        self,
        value: float,
        ref_range: ReferenceRange,
    ) -> Classification:
        """
        Classify a valid numerical value against a configured reference interval.

        Deterministic boundary rules:
            - When critical_inclusive is False (default):
                value < critical_low                  -> CRITICAL
                critical_low <= value < normal_low    -> LOW
                normal_low <= value <= normal_high    -> NORMAL
                normal_high < value <= critical_high  -> HIGH
                value > critical_high                 -> CRITICAL

            - When critical_inclusive is True:
                value <= critical_low                 -> CRITICAL
                critical_low < value < normal_low     -> LOW
                normal_low <= value <= normal_high    -> NORMAL
                normal_high < value < critical_high   -> HIGH
                value >= critical_high                -> CRITICAL

            - When critical thresholds are not configured:
                value < normal_low                    -> LOW
                normal_low <= value <= normal_high    -> NORMAL
                value > normal_high                   -> HIGH
        """
        c_low = ref_range.critical_low
        c_high = ref_range.critical_high
        n_low = ref_range.normal_low
        n_high = ref_range.normal_high

        # 1. Critical Low evaluation
        if c_low is not None:
            if self.critical_inclusive:
                if value <= c_low:
                    return Classification.CRITICAL
            else:
                if value < c_low:
                    return Classification.CRITICAL

        # 2. Normal Low evaluation (values below normal_low)
        if n_low is not None and value < n_low:
            return Classification.LOW

        # 3. Normal Interval evaluation (inclusive boundaries)
        is_above_or_eq_low = (n_low is None) or (value >= n_low)
        is_below_or_eq_high = (n_high is None) or (value <= n_high)

        if is_above_or_eq_low and is_below_or_eq_high:
            return Classification.NORMAL

        # 4. Critical High & High evaluation
        if c_high is not None:
            if self.critical_inclusive:
                if value >= c_high:
                    return Classification.CRITICAL
                return Classification.HIGH
            else:
                if value > c_high:
                    return Classification.CRITICAL
                return Classification.HIGH

        # 5. Elevated without critical threshold
        return Classification.HIGH

    def analyze(
        self,
        measurement: Optional[Union[TestMeasurement, Dict[str, Any]]] = None,
        *,
        test_name: Optional[str] = None,
        value: Any = None,
        unit: Optional[str] = None,
        context: Optional[Union[PatientContext, Dict[str, Any]]] = None,
    ) -> AnalysisResult:
        """
        Analyze an individual medical test measurement against configured reference ranges.

        Accepts either a TestMeasurement instance, a dictionary, or keyword arguments.
        """
        # Unpack input parameters
        raw_test_name = test_name
        raw_val = value
        raw_unit = unit
        raw_ctx = context

        if measurement is not None:
            if isinstance(measurement, TestMeasurement):
                raw_test_name = measurement.test_name
                raw_val = measurement.value
                raw_unit = measurement.unit
                raw_ctx = measurement.context
            elif isinstance(measurement, dict):
                raw_test_name = measurement.get("test_name", raw_test_name)
                raw_val = measurement.get("value", raw_val)
                raw_unit = measurement.get("unit", raw_unit)
                raw_ctx = measurement.get("context", raw_ctx)

        # Normalize patient context
        parsed_context: Optional[PatientContext] = None
        if isinstance(raw_ctx, PatientContext):
            parsed_context = raw_ctx
        elif isinstance(raw_ctx, dict):
            parsed_context = PatientContext(**raw_ctx)

        # Initialize tracking variables
        warnings: List[str] = []
        original_name_str = str(raw_test_name) if raw_test_name is not None else ""
        original_val_str = str(raw_val) if raw_val is not None else None

        # 1. Validate test name
        if not raw_test_name or not original_name_str.strip():
            return AnalysisResult(
                canonical_name=None,
                original_test_name=original_name_str,
                numeric_value=None,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=None,
                classification=None,
                reference_range=None,
                reference_source=None,
                status=AnalysisStatus.REFERENCE_NOT_AVAILABLE,
                warnings=["Test name was not provided or is empty."],
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        # 2. Resolve canonical analyte name
        canonical_name = self.normalizer.get_canonical_name(original_name_str)
        if not canonical_name:
            return AnalysisResult(
                canonical_name=None,
                original_test_name=original_name_str,
                numeric_value=None,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=None,
                classification=None,
                reference_range=None,
                reference_source=None,
                status=AnalysisStatus.REFERENCE_NOT_AVAILABLE,
                warnings=[f"No reference range configured for test '{original_name_str}'."],
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        # 3. Check for missing / empty value
        if raw_val is None or (isinstance(raw_val, str) and not raw_val.strip()):
            return AnalysisResult(
                canonical_name=canonical_name,
                original_test_name=original_name_str,
                numeric_value=None,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=None,
                classification=None,
                reference_range=None,
                reference_source=None,
                status=AnalysisStatus.VALUE_MISSING,
                warnings=["Test value is missing or empty."],
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        # 4. Check for qualitative result
        if isinstance(raw_val, str) and self.normalizer.is_qualitative_result(raw_val):
            return AnalysisResult(
                canonical_name=canonical_name,
                original_test_name=original_name_str,
                numeric_value=None,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=None,
                classification=None,
                reference_range=None,
                reference_source=None,
                status=AnalysisStatus.QUALITATIVE_RESULT,
                warnings=[
                    f"Qualitative result '{raw_val}' cannot be evaluated against numeric reference interval."
                ],
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        # 5. Parse numerical value
        try:
            num_value = float(str(raw_val).strip())
        except (ValueError, TypeError):
            return AnalysisResult(
                canonical_name=canonical_name,
                original_test_name=original_name_str,
                numeric_value=None,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=None,
                classification=None,
                reference_range=None,
                reference_source=None,
                status=AnalysisStatus.VALUE_NON_NUMERIC,
                warnings=[f"Test value '{raw_val}' cannot be parsed as a numeric value."],
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        # 6. Resolve Reference Range for canonical name and context
        ref_range, range_warnings = self.registry.get_range(canonical_name, parsed_context)
        warnings.extend(range_warnings)

        if ref_range is None:
            # Determine if context was strictly required
            status = (
                AnalysisStatus.CONTEXT_REQUIRED
                if any("required" in w.lower() for w in range_warnings)
                else AnalysisStatus.REFERENCE_NOT_AVAILABLE
            )
            return AnalysisResult(
                canonical_name=canonical_name,
                original_test_name=original_name_str,
                numeric_value=num_value,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=None,
                classification=None,
                reference_range=None,
                reference_source=None,
                status=status,
                warnings=warnings,
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        # 7. Check physiological non-negativity
        if ref_range.is_physiologically_non_negative and num_value < 0.0:
            return AnalysisResult(
                canonical_name=canonical_name,
                original_test_name=original_name_str,
                numeric_value=num_value,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=None,
                classification=None,
                reference_range=ref_range,
                reference_source=ref_range.source,
                status=AnalysisStatus.INVALID_VALUE,
                warnings=warnings
                + [f"Value {num_value} is negative, which is physiologically invalid for '{canonical_name}'."],
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        # 8. Check Unit Compatibility
        normalized_unit = self.normalizer.normalize_unit(raw_unit)

        if not raw_unit or not str(raw_unit).strip():
            return AnalysisResult(
                canonical_name=canonical_name,
                original_test_name=original_name_str,
                numeric_value=num_value,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=None,
                classification=None,
                reference_range=ref_range,
                reference_source=ref_range.source,
                status=AnalysisStatus.UNKNOWN_UNIT,
                warnings=warnings
                + [f"No unit provided. Configured reference unit is '{ref_range.unit}'."],
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        if not self.normalizer.are_units_compatible(raw_unit, ref_range.unit):
            return AnalysisResult(
                canonical_name=canonical_name,
                original_test_name=original_name_str,
                numeric_value=num_value,
                original_value_text=original_val_str,
                unit=raw_unit,
                normalized_value=None,
                normalized_unit=normalized_unit,
                classification=None,
                reference_range=ref_range,
                reference_source=ref_range.source,
                status=AnalysisStatus.UNIT_MISMATCH,
                warnings=warnings
                + [
                    f"Supplied unit '{raw_unit}' does not match reference unit '{ref_range.unit}'. "
                    f"Automatic unit conversion is not enabled."
                ],
                disclaimer=self.MANDATORY_DISCLAIMER,
            )

        # 9. Perform Deterministic Classification
        classification = self.classify_value(num_value, ref_range)

        return AnalysisResult(
            canonical_name=canonical_name,
            original_test_name=original_name_str,
            numeric_value=num_value,
            original_value_text=original_val_str,
            unit=raw_unit,
            normalized_value=num_value,
            normalized_unit=normalized_unit,
            classification=classification,
            reference_range=ref_range,
            reference_source=ref_range.source,
            status=AnalysisStatus.SUCCESS,
            warnings=warnings,
            disclaimer=self.MANDATORY_DISCLAIMER,
        )

    def analyze_many(
        self,
        measurements: List[Union[TestMeasurement, Dict[str, Any]]],
        context: Optional[Union[PatientContext, Dict[str, Any]]] = None,
    ) -> List[AnalysisResult]:
        """
        Analyze a batch of test measurements, optionally applying shared patient context.
        """
        results = []
        for m in measurements:
            if isinstance(m, dict) and context and "context" not in m:
                m_copy = dict(m)
                m_copy["context"] = context
                results.append(self.analyze(m_copy))
            elif isinstance(m, TestMeasurement) and context and m.context is None:
                parsed_ctx = (
                    context if isinstance(context, PatientContext) else PatientContext(**context)
                )
                m_copy = m.model_copy(update={"context": parsed_ctx})
                results.append(self.analyze(m_copy))
            else:
                results.append(self.analyze(m))
        return results
