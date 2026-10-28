"""
MedIntel AI — Phase 6: Deterministic Medical Analyte and Unit Normalizer.

Provides strict, deterministic string normalization and alias resolution
for medical laboratory tests and units of measurement.

Safety Guarantees:
    - NO fuzzy matching: Prevents dangerous cross-mapping between distinct medical tests
      (e.g., Sodium vs. Potassium, HDL vs. LDL).
    - Case-insensitive, whitespace-tolerant exact token matching only.
    - Strict unit compatibility verification with zero silent conversions.
"""

import re
from typing import Dict, List, Optional, Set, Tuple


class AnalyteNormalizer:
    """
    Deterministic alias resolver for medical laboratory test names.
    Maps extracted test name variations to authoritative canonical test names.
    """

    # Qualitative clinical test result indicator terms
    QUALITATIVE_TERMS: Set[str] = {
        "positive",
        "negative",
        "reactive",
        "non-reactive",
        "nonreactive",
        "detected",
        "not detected",
        "notdetected",
        "indeterminate",
        "equivocal",
        "trace",
        "nil",
        "present",
        "absent",
        "normal",
        "abnormal",
    }

    # Standard unit aliases mapping to canonical unit formatting
    UNIT_CANONICAL_MAP: Dict[str, str] = {
        "mg/dl": "mg/dL",
        "mg/l": "mg/L",
        "g/dl": "g/dL",
        "gm/dl": "g/dL",
        "gms/dl": "g/dL",
        "g/l": "g/L",
        "meq/l": "mEq/L",
        "mmol/l": "mmol/L",
        "umol/l": "umol/L",
        "cells/ul": "cells/uL",
        "cells/cumm": "cells/uL",
        "/cumm": "cells/uL",
        "/ul": "cells/uL",
        "x10^3/ul": "10^3/uL",
        "10^3/ul": "10^3/uL",
        "k/ul": "10^3/uL",
        "x10^6/ul": "10^6/uL",
        "10^6/ul": "10^6/uL",
        "millions/cmm": "10^6/uL",
        "fl": "fL",
        "pg": "pg",
        "%": "%",
        "percent": "%",
        "u/l": "U/L",
        "iu/l": "IU/L",
        "iu/ml": "IU/mL",
        "ng/ml": "ng/mL",
        "ug/dl": "ug/dL",
        "mmhg": "mmHg",
        "mm hg": "mmHg",
        "/min": "/min",
        "bpm": "bpm",
        "lakhs/cumm": "Lakhs/cumm",
        "lakh/cumm": "Lakhs/cumm",
        "lacs/cumm": "Lakhs/cumm",
        "lac/cumm": "Lakhs/cumm",
        "lakhs/ul": "Lakhs/cumm",
        "lakh/ul": "Lakhs/cumm",
        "lacs/ul": "Lakhs/cumm",
        "lac/ul": "Lakhs/cumm",
        "lakhs": "Lakhs/cumm",
        "lakh": "Lakhs/cumm",
        "lac": "Lakhs/cumm",
        "lacs": "Lakhs/cumm",
    }

    # Authoritative, certified clinical unit conversion factors:
    # (canonical_analyte, normalized_source_unit, normalized_target_unit) -> conversion_factor
    # such that: target_value = source_value * conversion_factor
    UNIT_CONVERSIONS: Dict[Tuple[str, str, str], float] = {
        # Platelet Count:
        # Reference unit is 'cells/uL'
        # In Indian labs: 1 Lakh/cumm = 100,000 cells/uL (since 1 cumm = 1 mm3 = 1 uL)
        ("Platelet Count", "lakhs/cumm", "cells/ul"): 100000.0,
        ("Platelet Count", "lakh/cumm", "cells/ul"): 100000.0,
        ("Platelet Count", "lacs/cumm", "cells/ul"): 100000.0,
        ("Platelet Count", "lac/cumm", "cells/ul"): 100000.0,
        ("Platelet Count", "lakhs/ul", "cells/ul"): 100000.0,
        ("Platelet Count", "lakh/ul", "cells/ul"): 100000.0,
        ("Platelet Count", "lacs/ul", "cells/ul"): 100000.0,
        ("Platelet Count", "lac/ul", "cells/ul"): 100000.0,
        ("Platelet Count", "lakhs", "cells/ul"): 100000.0,
        ("Platelet Count", "lakh", "cells/ul"): 100000.0,
        ("Platelet Count", "lac", "cells/ul"): 100000.0,
        ("Platelet Count", "lacs", "cells/ul"): 100000.0,
        ("Platelet Count", "10^5/cumm", "cells/ul"): 100000.0,
        ("Platelet Count", "10^5/ul", "cells/ul"): 100000.0,
        ("Platelet Count", "10^3/ul", "cells/ul"): 1000.0,
        ("Platelet Count", "k/ul", "cells/ul"): 1000.0,
        ("Platelet Count", "x10^3/ul", "cells/ul"): 1000.0,
        ("Platelet Count", "thou/ul", "cells/ul"): 1000.0,
        ("Platelet Count", "10^9/l", "cells/ul"): 1000.0,

        # White Blood Cell Count:
        ("White Blood Cell Count", "10^3/ul", "cells/ul"): 1000.0,
        ("White Blood Cell Count", "k/ul", "cells/ul"): 1000.0,
        ("White Blood Cell Count", "x10^3/ul", "cells/ul"): 1000.0,
        ("White Blood Cell Count", "thou/ul", "cells/ul"): 1000.0,
        ("White Blood Cell Count", "lakhs/cumm", "cells/ul"): 100000.0,
        ("White Blood Cell Count", "lakh/cumm", "cells/ul"): 100000.0,
        ("White Blood Cell Count", "10^9/l", "cells/ul"): 1000.0,

        # Hemoglobin:
        ("Hemoglobin", "g/l", "g/dl"): 0.1,
        ("Hemoglobin", "gm/l", "g/dl"): 0.1,
    }

    def __init__(self) -> None:
        """Initialize normalizer with empty alias map."""
        self._alias_map: Dict[str, str] = {}

    @staticmethod
    def clean_string(raw: Optional[str]) -> str:
        """
        Produce a normalized lookup key:
        - Lowercase
        - Strip leading/trailing whitespace
        - Collapse multiple spaces/hyphens/underscores/dots
        - Strip non-alphanumeric trailing punctuation
        """
        if not raw:
            return ""
        # Lowercase and replace punctuation separators with single spaces
        text = raw.lower().strip()
        # Remove internal dots (e.g., 'w.b.c.' -> 'wbc')
        text = text.replace(".", "")
        # Replace hyphens, underscores, slashes with spaces for test names
        text = re.sub(r"[\-_/]+", " ", text)
        # Collapse multiple whitespace characters
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def register_alias(self, alias: str, canonical_name: str) -> None:
        """
        Register an alias mapping to a canonical test name.
        Both the alias and canonical name itself are indexed as lookup keys.
        """
        key = self.clean_string(alias)
        if key:
            self._alias_map[key] = canonical_name

        canonical_key = self.clean_string(canonical_name)
        if canonical_key:
            self._alias_map[canonical_key] = canonical_name

    def register_aliases(self, canonical_name: str, aliases: List[str]) -> None:
        """Register multiple aliases for a canonical name."""
        self.register_alias(canonical_name, canonical_name)
        for alias in aliases:
            self.register_alias(alias, canonical_name)

    def get_canonical_name(self, test_name: Optional[str]) -> Optional[str]:
        """
        Resolve a raw test name string to its canonical test name.
        Uses exact deterministic lookup; returns None if not recognized.
        """
        if not test_name:
            return None
        key = self.clean_string(test_name)
        return self._alias_map.get(key)

    @classmethod
    def normalize_unit(cls, unit: Optional[str]) -> Optional[str]:
        """
        Normalize unit string casing and common equivalent expressions.
        Preserves unmapped units in stripped format without guessing.
        """
        if not unit:
            return None
        # Clean unit string: strip whitespace, remove internal extra spaces
        cleaned = re.sub(r"\s+", "", unit.strip().lower())
        return cls.UNIT_CANONICAL_MAP.get(cleaned, unit.strip())

    @classmethod
    def are_units_compatible(cls, unit1: Optional[str], unit2: Optional[str]) -> bool:
        """
        Check whether two units are equivalent after standard unit normalization.
        Does NOT perform unit conversion (e.g. mg/dL != mmol/L).
        """
        if not unit1 or not unit2:
            return False
        norm1 = cls.normalize_unit(unit1)
        norm2 = cls.normalize_unit(unit2)
        if not norm1 or not norm2:
            return False
        return norm1.lower() == norm2.lower()

    @classmethod
    def is_qualitative_result(cls, value_str: Optional[str]) -> bool:
        """
        Determine if an extracted value represents a qualitative result
        (e.g., 'Positive', 'Negative', 'Reactive', 'Trace') rather than
        a numerical measurement.
        """
        if not value_str:
            return False
        clean_val = value_str.strip().lower()
        return clean_val in cls.QUALITATIVE_TERMS

    @classmethod
    def convert_unit(
        cls,
        canonical_name: Optional[str],
        value: Optional[float],
        from_unit: Optional[str],
        to_unit: Optional[str],
    ) -> Optional[float]:
        """
        Convert a numerical value from a source unit to the authoritative reference unit
        using certified medical conversion tables.

        Returns:
            Converted numerical value if an authoritative conversion rule is registered,
            or None if the units cannot be safely converted.
        """
        if canonical_name is None or value is None or not from_unit or not to_unit:
            return None

        clean_from = re.sub(r"\s+", "", from_unit.strip().lower())
        clean_to = re.sub(r"\s+", "", to_unit.strip().lower())

        # If already equivalent, factor is 1.0
        if cls.are_units_compatible(from_unit, to_unit):
            return float(value)

        # Lookup in certified unit conversion table
        key = (canonical_name, clean_from, clean_to)
        if key in cls.UNIT_CONVERSIONS:
            factor = cls.UNIT_CONVERSIONS[key]
            return round(value * factor, 4)

        return None

