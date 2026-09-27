"""Integration tests for Rule Engine MVP covering the 4 synthetic scenarios."""

import pytest
from src.rule_engine.engine import RuleEngine
from src.rule_engine.models import FoodProfile, Material, PackagingContext


@pytest.fixture
def engine():
    return RuleEngine.from_config()


def test_scenario_a_high_fat_food(engine):
    """Scenario A: High-fat food (fat = 48%, OTR requirement <= 10).

    Material A (OTR = 1.5) -> Feasible
    Material B (OTR = 50.0) -> Rejected by R2.1
    """
    food = FoodProfile(code="F_FAT", name="Fried Peanuts", fat_pct=48.0)
    mat_a = Material(
        material_id="mat_a",
        base_material="Aluminium Foil Laminate",
        otr_cm3_m2_day=1.5,
        otr_status="CANONICAL",
        wvtr_g_m2_day=0.5,
        wvtr_status="CANONICAL",
        is_recycled_plastic=False,
        has_migration_test_data=True,
    )
    mat_b = Material(
        material_id="mat_b",
        base_material="Low Density Polyethylene",
        otr_cm3_m2_day=50.0,
        otr_status="CANONICAL",
        wvtr_g_m2_day=1.0,
        wvtr_status="CANONICAL",
        is_recycled_plastic=False,
        has_migration_test_data=True,
    )

    res_a = engine.evaluate_material(food, mat_a)
    assert res_a.status == "FEASIBLE"
    assert res_a.score is not None

    res_b = engine.evaluate_material(food, mat_b)
    assert res_b.status == "REJECTED_BARRIER"


def test_scenario_b_hygroscopic_product(engine):
    """Scenario B: Hygroscopic product (moisture < 10, aw < 0.3, WVTR <= 1.0).

    Material A (WVTR = 0.5) -> Feasible
    Material B (WVTR = 5.0) -> Rejected
    """
    food = FoodProfile(code="F_HYGRO", name="Instant Coffee", water_pct=3.0, moisture_barrier_requirement="High")
    ctx = PackagingContext(water_activity=0.2)

    mat_pass = Material(
        material_id="mat_p",
        base_material="High Barrier PET",
        wvtr_g_m2_day=0.5,
        wvtr_status="CANONICAL",
        otr_cm3_m2_day=2.0,
        otr_status="CANONICAL",
        is_recycled_plastic=False,
        has_migration_test_data=True,
    )
    mat_fail = Material(
        material_id="mat_f",
        base_material="Paper Uncoated",
        wvtr_g_m2_day=5.0,
        wvtr_status="CANONICAL",
        otr_cm3_m2_day=10.0,
        otr_status="CANONICAL",
        is_recycled_plastic=False,
        has_migration_test_data=True,
    )

    res_p = engine.evaluate_material(food, mat_pass, ctx)
    assert res_p.status == "FEASIBLE"

    res_f = engine.evaluate_material(food, mat_fail, ctx)
    assert res_f.status == "REJECTED_BARRIER"


def test_scenario_c_fresh_produce(engine):
    """Scenario C: Fresh produce respiration window (10,000 <= OTR <= 100,000).

    OTR = 5,000 -> Fail (below lower bound)
    OTR = 20,000 -> Pass
    OTR = 120,000 -> Fail (above upper bound)
    """
    food = FoodProfile(code="F_PROD", name="Fresh Spinach", food_category="Fruits, Vegetables, Salads")
    ctx = PackagingContext(is_fresh_produce=True)

    mat_low = Material(material_id="m_low", base_material="BOPP High Barrier", otr_cm3_m2_day=5000.0, otr_status="CANONICAL", wvtr_g_m2_day=2.0, wvtr_status="CANONICAL", is_recycled_plastic=False, has_migration_test_data=True)
    mat_win = Material(material_id="m_win", base_material="Perforated PE", otr_cm3_m2_day=20000.0, otr_status="CANONICAL", wvtr_g_m2_day=10.0, wvtr_status="CANONICAL", is_recycled_plastic=False, has_migration_test_data=True)
    mat_high = Material(material_id="m_high", base_material="Ultra Perforated Netting", otr_cm3_m2_day=120000.0, otr_status="CANONICAL", wvtr_g_m2_day=20.0, wvtr_status="CANONICAL", is_recycled_plastic=False, has_migration_test_data=True)

    assert engine.evaluate_material(food, mat_low, ctx).status == "REJECTED_BARRIER"
    assert engine.evaluate_material(food, mat_win, ctx).status == "FEASIBLE"
    assert engine.evaluate_material(food, mat_high, ctx).status == "REJECTED_BARRIER"


def test_scenario_d_regulatory_rejection(engine):
    """Scenario D: Regulatory rejection.

    Prohibited material for Pan Masala -> REJECTED_REGULATORY regardless of barrier score.
    """
    food = FoodProfile(code="F_PAN", name="Pan Masala Sachet", food_category="Pan Masala")
    mat_prohibited = Material(
        material_id="m_poly",
        base_material="Polyethylene",
        structure_type="Film",
        otr_cm3_m2_day=0.1,  # Excellent barrier score!
        otr_status="CANONICAL",
        wvtr_g_m2_day=0.1,
        wvtr_status="CANONICAL",
        is_recycled_plastic=False,
        has_migration_test_data=True,
    )

    res = engine.evaluate_material(food, mat_prohibited)
    assert res.status == "REJECTED_REGULATORY"
    assert res.score is None  # Cannot be scored or rescued by barrier score


def test_recommend_and_data_quality_report(engine):
    food = FoodProfile(code="F_1", name="Cashew Nuts", fat_pct=45.0, food_category="Peanuts")
    mats = [
        Material(material_id="m1", base_material="Tin", otr_cm3_m2_day=1.0, otr_status="CANONICAL", wvtr_g_m2_day=3.0, wvtr_status="CANONICAL", is_recycled_plastic=False, has_migration_test_data=True),
        Material(material_id="m2", base_material="Polyethylene", otr_cm3_m2_day=100.0, otr_status="CANONICAL", wvtr_g_m2_day=10.0, wvtr_status="CANONICAL", is_recycled_plastic=False, has_migration_test_data=True),
    ]

    res = engine.recommend(food, mats, top_k=5)
    assert len(res.candidates) == 1
    assert res.candidates[0].material_id == "m1"
    assert len(res.rejected_candidates) == 1

    report = engine.data_quality_report([food], mats)
    assert report["total_food_records"] == 1
    assert report["total_materials"] == 2


def test_food_record_category_bounds_override_missing_yaml_category(engine):
    food = FoodProfile(code="F_CUSTOM", name="Sample", food_category="Dataset category", min_otr=2, max_otr=4, min_wvtr=1, max_wvtr=3)
    constraints = engine.get_category_constraints(food.food_category, food)
    assert [(c.metric, c.value) for c in constraints] == [
        ("otr_cm3_m2_day", (2.0, 4.0)),
        ("wvtr_g_m2_day", (1.0, 3.0)),
    ]


def test_evaluated_category_constraint_is_in_rule_results(engine):
    food = FoodProfile(code="F_CUSTOM", name="Sample", food_category="Dataset category", max_otr=4)
    material = Material(material_id="m1", otr_cm3_m2_day=7, otr_status="CANONICAL", is_recycled_plastic=False, has_migration_test_data=True)
    rec = engine.evaluate_material(food, material)
    assert rec.status == "REJECTED_BARRIER"
    assert any(rr.rule_id == "CategoryBand" and rr.status == "FAIL" for rr in rec.rule_results)


def test_empty_rule_lists_disable_rule_groups():
    empty_engine = RuleEngine(regulatory_rules=[], physics_rules=[])
    assert empty_engine.regulatory_rules == []
    assert empty_engine.physics_rules == []


def test_recommend_rejects_negative_top_k(engine):
    import pytest
    with pytest.raises(ValueError):
        engine.recommend(FoodProfile(code="x", name="x"), [], top_k=-1)


def test_clustering_keeps_missing_barrier_rows_for_review(engine):
    food = FoodProfile(code="F", name="Food", min_otr=0.1, max_otr=10, min_wvtr=0.1, max_wvtr=10)
    materials = [
        Material(material_id="complete", otr_cm3_m2_day=1, otr_status="CANONICAL", wvtr_g_m2_day=1, wvtr_status="CANONICAL", is_recycled_plastic=False, has_migration_test_data=True),
        Material(material_id="missing", otr_cm3_m2_day=None, otr_status="MISSING", wvtr_g_m2_day=1, wvtr_status="CANONICAL", is_recycled_plastic=False, has_migration_test_data=True),
    ]
    result = engine.recommend(food, materials)
    assert result.cluster_summary["clustered_count"] == 1
    assert result.cluster_summary["unclustered_count"] == 1
    assert result.cluster_summary["applied_before_rules"] is True
    assert len(result.candidates) + len(result.requires_review_candidates) + len(result.rejected_candidates) == 2
