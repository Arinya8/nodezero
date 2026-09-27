"""Unit tests for Group 2 Physics & Barrier Rules and Constraint Evaluator."""

import pytest
from src.rule_engine.constraints import ConstraintEvaluator
from src.rule_engine.models import Constraint, FoodProfile, Material, PackagingContext
from src.rule_engine.rules.physics import HighFatOxidationRule, HygroscopicMoistureRule, FreshProduceRespirationRule


def test_high_fat_rule_emits_otr_constraint():
    rule = HighFatOxidationRule()
    food = FoodProfile(code="1", name="Fried Peanuts", fat_pct=48.0)
    mat = Material(material_id="m1")
    ctx = PackagingContext()

    res = rule.evaluate(food, mat, ctx)
    assert res.status == "PASS"
    c = res.evidence["constraint"]
    assert c.metric == "otr_cm3_m2_day"
    assert c.operator == "<="
    assert c.value == 10.0


def test_fresh_produce_respiration_window():
    rule = FreshProduceRespirationRule()
    food = FoodProfile(code="2", name="Fresh Apples", food_category="Fruits and Vegetables")
    mat = Material(material_id="m2")
    ctx = PackagingContext(is_fresh_produce=True)

    res = rule.evaluate(food, mat, ctx)
    assert res.status == "PASS"
    c = res.evidence["constraint"]
    assert c.operator == "between"
    assert c.value == (10000.0, 100000.0)


def test_constraint_evaluator_pass_and_fail():
    c = Constraint(metric="otr_cm3_m2_day", operator="<=", value=10.0, source_rule="R2.1", reason="test")

    mat_pass = Material(material_id="m1", otr_cm3_m2_day=1.5, otr_status="CANONICAL")
    status_pass, reason = ConstraintEvaluator.evaluate_constraint(c, mat_pass)
    assert status_pass == "PASS"

    mat_fail = Material(material_id="m2", otr_cm3_m2_day=50.0, otr_status="CANONICAL")
    status_fail, reason = ConstraintEvaluator.evaluate_constraint(c, mat_fail)
    assert status_fail == "FAIL"

    mat_missing = Material(material_id="m3", otr_cm3_m2_day=None, otr_status="MISSING")
    status_missing, reason = ConstraintEvaluator.evaluate_constraint(c, mat_missing)
    assert status_missing == "UNKNOWN"
