"""
MedIntel AI — Phase 6: Medical Reference Range Registry.

Manages authoritative reference intervals for laboratory analytes.
Supports context-aware resolution (biological sex and age) while enforcing
rigorous safety disclaimers, transparent audit citations, and clear distinction
between general educational baselines and lab-specific calibrated intervals.

Reference Policy:
    - Configured ranges are general educational references (GENERAL_REFERENCE).
    - Reference intervals vary across clinical laboratories, instrumentation,
      and assay methodologies (e.g., Jaffe vs. enzymatic creatinine).
    - No critical thresholds are invented where authoritative medical consensus
      does not support them (e.g., Total Cholesterol, HbA1c, adult Creatinine).
"""

from typing import Dict, List, Optional, Tuple

from reference.models import (
    PatientContext,
    ReferenceRange,
    ReferenceType,
    VerificationStatus,
)


class ReferenceRangeRegistry:
    """
    In-memory registry of laboratory reference intervals.
    Provides lookup by canonical analyte name and patient context.
    """

    def __init__(self) -> None:
        """Initialize empty registry indexed by canonical name."""
        # Key: canonical_name -> list of ReferenceRange entries (differentiated by sex/age)
        self._ranges: Dict[str, List[ReferenceRange]] = {}

    def register(self, range_def: ReferenceRange) -> None:
        """Register a reference range definition."""
        name = range_def.canonical_name
        if name not in self._ranges:
            self._ranges[name] = []
        self._ranges[name].append(range_def)

    def get_supported_analytes(self) -> List[str]:
        """Return list of all registered canonical analyte names."""
        return sorted(list(self._ranges.keys()))

    def get_all_ranges(self) -> List[ReferenceRange]:
        """Return all registered reference range definitions."""
        result = []
        for ranges in self._ranges.values():
            result.extend(ranges)
        return result

    def get_range(
        self,
        canonical_name: str,
        context: Optional[PatientContext] = None,
    ) -> Tuple[Optional[ReferenceRange], List[str]]:
        """
        Resolve the appropriate reference range for a canonical analyte name
        given optional patient context (sex, age).

        Returns:
            Tuple of (resolved ReferenceRange or None, list of warning messages)
        """
        warnings: List[str] = []
        candidates = self._ranges.get(canonical_name)

        if not candidates:
            return None, [f"No reference range configured for analyte '{canonical_name}'."]

        # 1. Single candidate case
        if len(candidates) == 1:
            ref = candidates[0]
            # Check if candidate requires a specific sex but context differs
            if ref.applicable_sex and context and context.sex:
                ctx_sex = context.sex.strip().upper()
                if ctx_sex != ref.applicable_sex.upper():
                    warnings.append(
                        f"Range for '{canonical_name}' is configured for sex '{ref.applicable_sex}', "
                        f"but patient sex is '{context.sex}'."
                    )
            return ref, warnings

        # 2. Multiple candidates: filter by biological sex
        patient_sex = context.sex.strip().upper() if (context and context.sex) else None

        if patient_sex in {"M", "F"}:
            for candidate in candidates:
                if candidate.applicable_sex and candidate.applicable_sex.upper() == patient_sex:
                    return candidate, warnings

        # 3. If sex-specific range not matched or context missing, check for general adult fallback
        general_candidate = None
        for candidate in candidates:
            if candidate.applicable_sex is None:
                general_candidate = candidate
                break

        if general_candidate:
            if not patient_sex:
                warnings.append(
                    f"Patient sex not specified; evaluated against broad adult reference interval for "
                    f"'{canonical_name}'. Sex-specific intervals exist."
                )
            return general_candidate, warnings

        # 4. If only sex-specific candidates exist and no general fallback is available
        available_sexes = [c.applicable_sex for c in candidates if c.applicable_sex]
        return None, [
            f"Patient biological sex ({'/'.join(available_sexes)}) is required to select the reference interval "
            f"for '{canonical_name}'."
        ]


# ---------------------------------------------------------------------------
# Default Reference Range Factory
# ---------------------------------------------------------------------------

def get_default_registry() -> ReferenceRangeRegistry:
    """
    Construct and populate a registry with verified core laboratory analytes.

    All ranges are audited against established medical consensus guidelines
    (ADA, WHO, National Kidney Foundation, NCEP ATP III, Mayo Clinic Laboratories, Tietz, Harrison's).
    """
    registry = ReferenceRangeRegistry()

    # 1. Fasting Blood Glucose
    registry.register(
        ReferenceRange(
            canonical_name="Fasting Blood Glucose",
            aliases=[
                "glucose",
                "fasting glucose",
                "fbs",
                "blood glucose fasting",
                "fbg",
                "fasting blood sugar",
                "serum glucose fasting",
            ],
            unit="mg/dL",
            normal_low=70.0,
            normal_high=99.0,
            critical_low=50.0,
            critical_high=400.0,
            applicable_sex=None,
            source="American Diabetes Association (ADA) 2024 / Mayo Clinic Laboratories",
            citation="Diabetes Care 2024;47(Suppl. 1):S20-S42; Mayo Clinic Laboratories Critical Values",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Requires 8-12 hours overnight fast. Serum or plasma. Critical thresholds < 50 and > 400 mg/dL based on institutional alert criteria.",
            is_physiologically_non_negative=True,
        )
    )

    # 2. Hemoglobin (Male)
    registry.register(
        ReferenceRange(
            canonical_name="Hemoglobin",
            aliases=["hb", "hgb", "haemoglobin", "blood hemoglobin"],
            unit="g/dL",
            normal_low=13.8,
            normal_high=17.2,
            critical_low=7.0,
            critical_high=20.0,
            applicable_sex="M",
            source="NIH / Harrison's Principles of Internal Medicine (21st ed.) / Mayo Clinic Laboratories",
            citation="Harrison's Principles of Internal Medicine, 21e, Appendix; Mayo Clinic Critical Values",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Whole blood (EDTA). Adult males. Critical low 7.0 g/dL transfusion alert trigger; critical high >= 20.0 g/dL hyperviscosity alert.",
            is_physiologically_non_negative=True,
        )
    )

    # 2. Hemoglobin (Female)
    registry.register(
        ReferenceRange(
            canonical_name="Hemoglobin",
            aliases=["hb", "hgb", "haemoglobin", "blood hemoglobin"],
            unit="g/dL",
            normal_low=12.1,
            normal_high=15.1,
            critical_low=7.0,
            critical_high=20.0,
            applicable_sex="F",
            source="NIH / Harrison's Principles of Internal Medicine (21st ed.) / Mayo Clinic Laboratories",
            citation="Harrison's Principles of Internal Medicine, 21e, Appendix; Mayo Clinic Critical Values",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Whole blood (EDTA). Adult non-pregnant females. Critical low 7.0 g/dL transfusion alert trigger.",
            is_physiologically_non_negative=True,
        )
    )

    # 2. Hemoglobin (General Adult Fallback)
    registry.register(
        ReferenceRange(
            canonical_name="Hemoglobin",
            aliases=["hb", "hgb", "haemoglobin", "blood hemoglobin"],
            unit="g/dL",
            normal_low=12.0,
            normal_high=17.5,
            critical_low=7.0,
            critical_high=20.0,
            applicable_sex=None,
            source="WHO / Tietz Clinical Guide to Laboratory Tests (4th ed.) / Mayo Clinic",
            citation="WHO/NHD/01.3; Tietz Clinical Guide to Laboratory Tests, 4e",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Broad general adult reference interval without sex stratification.",
            is_physiologically_non_negative=True,
        )
    )

    # 3. Serum Creatinine (Male)
    registry.register(
        ReferenceRange(
            canonical_name="Serum Creatinine",
            aliases=["creatinine", "creat", "serum creat", "cr", "s creatinine"],
            unit="mg/dL",
            normal_low=0.7,
            normal_high=1.3,
            critical_low=None,
            critical_high=None,
            applicable_sex="M",
            source="National Kidney Foundation (NKF) / American Kidney Fund / Tietz (6th ed.)",
            citation="NKF KDIGO Clinical Practice Guideline; Tietz Textbook, 6e",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Serum. Adult males. Method: enzymatic IDMS-traceable. No universal adult critical threshold is established; adult renal impairment is staged by eGFR/delta.",
            is_physiologically_non_negative=True,
        )
    )

    # 3. Serum Creatinine (Female)
    registry.register(
        ReferenceRange(
            canonical_name="Serum Creatinine",
            aliases=["creatinine", "creat", "serum creat", "cr", "s creatinine"],
            unit="mg/dL",
            normal_low=0.6,
            normal_high=1.1,
            critical_low=None,
            critical_high=None,
            applicable_sex="F",
            source="National Kidney Foundation (NKF) / American Kidney Fund / Tietz (6th ed.)",
            citation="NKF KDIGO Clinical Practice Guideline; Tietz Textbook, 6e",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Serum. Adult females. Method: enzymatic IDMS-traceable. No universal adult critical threshold is established.",
            is_physiologically_non_negative=True,
        )
    )

    # 3. Serum Creatinine (General Adult Fallback)
    registry.register(
        ReferenceRange(
            canonical_name="Serum Creatinine",
            aliases=["creatinine", "creat", "serum creat", "cr", "s creatinine"],
            unit="mg/dL",
            normal_low=0.6,
            normal_high=1.3,
            critical_low=None,
            critical_high=None,
            applicable_sex=None,
            source="National Kidney Foundation (NKF) / American Kidney Fund / Tietz (6th ed.)",
            citation="Tietz Textbook of Clinical Chemistry and Molecular Diagnostics, 6e",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="General adult range without sex stratification.",
            is_physiologically_non_negative=True,
        )
    )

    # 4. White Blood Cell Count (WBC / TLC)
    registry.register(
        ReferenceRange(
            canonical_name="White Blood Cell Count",
            aliases=[
                "wbc",
                "tlc",
                "total leukocyte count",
                "white blood cells",
                "leukocyte count",
                "total wbc count",
            ],
            unit="cells/uL",
            normal_low=4000.0,
            normal_high=11000.0,
            critical_low=2000.0,
            critical_high=30000.0,
            applicable_sex=None,
            source="Harrison's Principles of Internal Medicine (21st ed.) / CAP Critical Values Survey",
            citation="Harrison's Principles of Internal Medicine, 21e, Appendix; CAP Q-Probes Survey",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Whole blood (EDTA). Automated hemocytometer. Critical thresholds vary by institution (Mayo Clinic lists >= 100,000 cells/uL).",
            is_physiologically_non_negative=True,
        )
    )

    # 5. Platelet Count
    registry.register(
        ReferenceRange(
            canonical_name="Platelet Count",
            aliases=[
                "platelets",
                "plt",
                "total platelet count",
                "thrombocyte count",
                "platelet",
            ],
            unit="cells/uL",
            normal_low=150000.0,
            normal_high=450000.0,
            critical_low=50000.0,
            critical_high=1000000.0,
            applicable_sex=None,
            source="Harrison's Principles of Internal Medicine (21st ed.) / Mayo Clinic Laboratories",
            citation="Harrison's Principles of Internal Medicine, 21e, Appendix; Mayo Clinic Critical Values",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Whole blood (EDTA). Values < 50,000 cells/uL represent critical bleeding risk alert thresholds (Mayo uses <= 40,000 cells/uL).",
            is_physiologically_non_negative=True,
        )
    )

    # 6. Serum Potassium
    registry.register(
        ReferenceRange(
            canonical_name="Serum Potassium",
            aliases=["potassium", "k+", "k", "serum k", "serum potassium k"],
            unit="mEq/L",
            normal_low=3.5,
            normal_high=5.0,
            critical_low=2.8,
            critical_high=6.2,
            applicable_sex=None,
            source="Tietz Textbook of Clinical Chemistry (6th ed.) / Harrison's (21st ed.) / CAP",
            citation="Tietz Textbook of Clinical Chemistry, 6e; CAP Critical Values Survey; Mayo Clinic (<3.0, >5.9 mmol/L)",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Serum. Hemolyzed specimens yield falsely elevated results. Critical boundaries represent acute cardiac dysrhythmia risk.",
            is_physiologically_non_negative=True,
        )
    )

    # 7. Serum Sodium
    registry.register(
        ReferenceRange(
            canonical_name="Serum Sodium",
            aliases=["sodium", "na+", "na", "serum na", "serum sodium na"],
            unit="mEq/L",
            normal_low=135.0,
            normal_high=145.0,
            critical_low=120.0,
            critical_high=160.0,
            applicable_sex=None,
            source="Tietz Textbook of Clinical Chemistry (6th ed.) / Harrison's (21st ed.) / Mayo Clinic Laboratories",
            citation="Tietz Textbook of Clinical Chemistry, 6e; Mayo Clinic Laboratories Critical Values",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Serum. Critical boundaries (<120, >160 mEq/L) represent severe neurological risk (seizures, osmotic demyelination, cerebral edema).",
            is_physiologically_non_negative=True,
        )
    )

    # 8. Total Cholesterol (No Critical Thresholds)
    registry.register(
        ReferenceRange(
            canonical_name="Total Cholesterol",
            aliases=["cholesterol", "serum cholesterol", "total chol", "t chol"],
            unit="mg/dL",
            normal_low=125.0,
            normal_high=200.0,
            critical_low=None,
            critical_high=None,
            applicable_sex=None,
            source="NCEP ATP III / American Heart Association (AHA)",
            citation="Circulation 2002;106(25):3143-3421 (NCEP ATP III Final Report)",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Fasting preferred (9-12 hours). Total cholesterol has no acute critical panic values in clinical medicine.",
            is_physiologically_non_negative=True,
        )
    )

    # 9. Blood Urea Nitrogen (BUN)
    registry.register(
        ReferenceRange(
            canonical_name="Blood Urea Nitrogen",
            aliases=["bun", "blood urea", "urea nitrogen", "serum urea", "urea"],
            unit="mg/dL",
            normal_low=7.0,
            normal_high=20.0,
            critical_low=None,
            critical_high=None,
            applicable_sex=None,
            source="Tietz Textbook of Clinical Chemistry (6th ed.) / Mayo Clinic Laboratories",
            citation="Tietz Textbook of Clinical Chemistry and Molecular Diagnostics, 6e; Mayo Clinic (adult normal 6-21 mg/dL)",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Serum. Acute critical threshold is lab-specific and not uniformly consensus-defined (some inpatient facilities alert at > 100 mg/dL).",
            is_physiologically_non_negative=True,
        )
    )

    # 10. Glycated Hemoglobin (HbA1c) (No Critical Thresholds)
    registry.register(
        ReferenceRange(
            canonical_name="Glycated Hemoglobin",
            aliases=["hba1c", "a1c", "glycohemoglobin", "glycosylated hemoglobin"],
            unit="%",
            normal_low=4.0,
            normal_high=5.6,
            critical_low=None,
            critical_high=None,
            applicable_sex=None,
            source="American Diabetes Association (ADA) Standards of Care (2024)",
            citation="Diabetes Care 2024;47(Suppl. 1):S20-S42",
            reference_type=ReferenceType.GENERAL_REFERENCE,
            verification_status=VerificationStatus.VERIFIED,
            notes="Non-diabetic normal: < 5.7%. Prediabetes: 5.7-6.4%; Diabetes threshold: >= 6.5%. HbA1c is a chronic 3-month marker with no acute panic value.",
            is_physiologically_non_negative=True,
        )
    )

    return registry
