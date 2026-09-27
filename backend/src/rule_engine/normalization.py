"""Unit conversion and normalization engine for packaging materials permeability data."""

import math
from typing import Optional, Tuple


def normalize_wvtr(
    value: Optional[float],
    unit: Optional[str],
    thickness_um: Optional[float] = None,
) -> Tuple[Optional[float], str]:
    """Normalize Water Vapor Transmission Rate (WVTR) to canonical unit: g/m2/day.

    Returns:
        Tuple[normalized_value, status]
        where status is one of: 'CANONICAL', 'CONVERTED', 'INCOMPARABLE', 'INVALID', 'MISSING'
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None, "MISSING"

    try:
        val_float = float(value)
    except (ValueError, TypeError):
        return None, "INVALID"

    if val_float < 0:
        return None, "INVALID"

    if not unit or not isinstance(unit, str) or not unit.strip():
        # Unit is missing/ambiguous. Do not guess raw numbers.
        return None, "INCOMPARABLE"

    unit_clean = unit.strip().lower().replace(" ", "").replace("²", "2")

    # Canonical g/m2/day variations
    canonical_units = {
        "g/m2/day",
        "g/m2day",
        "g/m2/24h",
        "g/m2-day",
        "g/(m2.day)",
        "g/m2.day",
        "g/m2/d",
    }
    if unit_clean in canonical_units:
        return val_float, "CANONICAL"

    if unit_clean in ("g/m2s", "g/m2/s"):
        return val_float * 86400.0, "CONVERTED"

    # Convertible 100 in2 units (1 m2 = 15.500031 100-in2)
    imperial_units = {
        "g/100in2/day",
        "g/100in2/24h",
        "g/100sqin/day",
    }
    if unit_clean in imperial_units:
        return val_float * 15.5, "CONVERTED"

    # Thickness-normalized units e.g. g*mil/m2/day or g*mm/m2/day
    if "mil" in unit_clean and ("g" in unit_clean and "m2" in unit_clean):
        if thickness_um is not None and thickness_um > 0:
            thickness_mil = thickness_um / 25.4
            return val_float / thickness_mil, "CONVERTED"
        return None, "INCOMPARABLE"

    return None, "INCOMPARABLE"


def normalize_otr(
    value: Optional[float],
    unit: Optional[str],
    thickness_um: Optional[float] = None,
) -> Tuple[Optional[float], str]:
    """Normalize Oxygen Transmission Rate (OTR) to canonical unit: cm3/m2/day.

    Returns:
        Tuple[normalized_value, status]
        where status is one of: 'CANONICAL', 'CONVERTED', 'INCOMPARABLE', 'INVALID', 'MISSING'
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None, "MISSING"

    try:
        val_float = float(value)
    except (ValueError, TypeError):
        return None, "INVALID"

    if val_float < 0:
        return None, "INVALID"

    if not unit or not isinstance(unit, str) or not unit.strip():
        # Unit is missing/ambiguous.
        return None, "INCOMPARABLE"

    unit_clean = unit.strip().lower().replace(" ", "").replace("²", "2").replace("³", "3")

    # Canonical cm3/m2/day variations (1 cm3 = 1 cc = 1 mL)
    canonical_units = {
        "cm3/m2/day",
        "cm3/m2day",
        "cc/m2/day",
        "cc/m2day",
        "ml/m2/day",
        "cm3/m2/24h",
        "cc/m2/24h",
        "ml/m2/24h",
        "cm3/m2-day",
        "cm3.m-2.day-1",
        "cm3/(m2.day)",
        "cm3/m2.day",
    }
    if unit_clean in canonical_units:
        return val_float, "CANONICAL"

    if unit_clean in ("cm3/m2s", "cc/m2s", "ml/m2s", "cm3/m2/s"):
        return val_float * 86400.0, "CONVERTED"

    # Convertible 100 in2 units
    imperial_units = {
        "cm3/100in2/day",
        "cc/100in2/day",
        "ml/100in2/day",
        "cc/100in2/24h",
    }
    if unit_clean in imperial_units:
        return val_float * 15.5, "CONVERTED"

    # Permeability coefficient e.g. cm3*mm/m2/day or cm3*um/m2/day
    if "mm" in unit_clean and ("cm3" in unit_clean or "cc" in unit_clean or "ml" in unit_clean):
        if thickness_um is not None and thickness_um > 0:
            thickness_mm = thickness_um / 1000.0
            return val_float / thickness_mm, "CONVERTED"
        return None, "INCOMPARABLE"

    return None, "INCOMPARABLE"


def canonicalize_material_name(name: Optional[str]) -> str:
    """Canonicalize material string for matching against rules."""
    if not name:
        return ""
    return name.strip().lower()
