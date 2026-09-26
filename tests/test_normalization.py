"""Unit tests for permeability unit normalization and conversion module."""

import math
import pytest
from src.rule_engine.normalization import normalize_otr, normalize_wvtr, canonicalize_material_name


def test_wvtr_canonical():
    val, status = normalize_wvtr(1.5, "g/m2/day")
    assert val == 1.5
    assert status == "CANONICAL"

    val, status = normalize_wvtr(2.0, "g/m2/24h")
    assert val == 2.0
    assert status == "CANONICAL"


def test_wvtr_convertible_imperial():
    val, status = normalize_wvtr(1.0, "g/100in2/day")
    assert val == 15.5
    assert status == "CONVERTED"


def test_wvtr_missing_unit_or_value():
    val, status = normalize_wvtr(None, "g/m2/day")
    assert val is None
    assert status == "MISSING"

    val, status = normalize_wvtr(1.5, None)
    assert val is None
    assert status == "INCOMPARABLE"

    val, status = normalize_wvtr(1.5, "")
    assert val is None
    assert status == "INCOMPARABLE"


def test_wvtr_invalid_negative():
    val, status = normalize_wvtr(-5.0, "g/m2/day")
    assert val is None
    assert status == "INVALID"


def test_otr_canonical():
    val, status = normalize_otr(10.0, "cm3/m2/day")
    assert val == 10.0
    assert status == "CANONICAL"

    val, status = normalize_otr(5.0, "cc/m2/day")
    assert val == 5.0
    assert status == "CANONICAL"


def test_otr_convertible_imperial():
    val, status = normalize_otr(2.0, "cc/100in2/day")
    assert val == 31.0
    assert status == "CONVERTED"


def test_otr_unknown_unit():
    val, status = normalize_otr(10.0, "unknown_unit_xyz")
    assert val is None
    assert status == "INCOMPARABLE"


def test_canonicalize_material_name():
    assert canonicalize_material_name("  PolyEthylene ") == "polyethylene"
    assert canonicalize_material_name(None) == ""
