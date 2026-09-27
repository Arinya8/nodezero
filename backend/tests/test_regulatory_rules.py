"""Unit tests for Group 1 Regulatory Rules."""

import pytest
from src.rule_engine.models import FoodProfile, Material, PackagingContext
from src.rule_engine.rules.regulatory import (
    PanMasalaProhibitionRule,
    RecycledPlasticRule,
    RPETDecontaminationRule,
    ThicknessFloorRule,
)


def test_pan_masala_prohibition_rejects_polyethylene():
    rule = PanMasalaProhibitionRule()
    food = FoodProfile(code="1", name="Pan Masala Premium", food_category="Pan Masala")
    mat = Material(material_id="m1", base_material="Polyethylene", structure_type="Film")
    ctx = PackagingContext()

    res = rule.evaluate(food, mat, ctx)
    assert res.status == "FAIL"
    assert res.severity == "HARD"
    assert "Prohibited material component" in res.reason


def test_pan_masala_prohibition_allows_tin():
    rule = PanMasalaProhibitionRule()
    food = FoodProfile(code="1", name="Pan Masala Premium", food_category="Pan Masala")
    mat = Material(material_id="m2", base_material="Tin", structure_type="Can")
    ctx = PackagingContext()

    res = rule.evaluate(food, mat, ctx)
    assert res.status == "PASS"


def test_pan_masala_prohibition_short_tokens_do_not_match_inside_words():
    rule = PanMasalaProhibitionRule()
    food = FoodProfile(code="1", name="Pan Masala", food_category="Pan Masala")
    material = Material(material_id="m1", base_material="Paper")
    assert rule.evaluate(food, material, PackagingContext()).status == "PASS"


def test_recycled_plastic_rule_unknown():
    rule = RecycledPlasticRule()
    food = FoodProfile(code="1", name="Peanuts")
    mat = Material(material_id="m3", base_material="Recycled PET", is_recycled_plastic=True, is_recycled_plastic_fcm_rpet=None)
    ctx = PackagingContext()

    res = rule.evaluate(food, mat, ctx)
    assert res.status == "UNKNOWN"


def test_rpet_decontamination_pass():
    rule = RPETDecontaminationRule()
    food = FoodProfile(code="1", name="Water")
    mat = Material(material_id="m4", base_material="rPET", has_rpet_decontamination_proof=True)
    ctx = PackagingContext()

    res = rule.evaluate(food, mat, ctx)
    assert res.status == "PASS"


def test_thickness_floor_fail():
    rule = ThicknessFloorRule()
    food = FoodProfile(code="1", name="Apples")
    mat = Material(material_id="m5", base_material="PE", thickness_um=30.0, compostable_is17088=False)
    ctx = PackagingContext(packaging_format="Carry Bag")

    res = rule.evaluate(food, mat, ctx)
    assert res.status == "FAIL"
    assert "below regulatory threshold" in res.reason


def test_pan_masala_token_boundaries_do_not_reject_paper():
    rule = PanMasalaProhibitionRule()
    food = FoodProfile(code="1", name="Pan Masala", food_category="Pan Masala")
    material = Material(material_id="m1", base_material="Paper")
    assert rule.evaluate(food, material, PackagingContext()).status == "PASS"
