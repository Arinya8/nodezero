import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.database.connection import get_connection
from src.database.repositories import (
    FoodGroupMapRepository,
    FoodItemRepository,
    MaterialRepository,
    PackagingRequirementRepository,
)
from src.database.schemas import FoodGroupMap, FoodItem, Material, PackagingRequirement
from src.preprocessing.food_category.food_category_map import FOOD_CATEGORY_MAP
from database.init_db import init_db


def _nan_none(value):
    if value is None:
        return None
    try:
        if isinstance(value, str):
            return value
        if pd.isna(value):
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
    except TypeError:
        return value
    return value


def _bool(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "t"}
    return bool(value)


def seed_db() -> None:
    init_db()

    reqs_csv = ROOT / "data" / "raw" / "packaging_materials" / "food_requirements.csv"
    foods_csv = ROOT / "data" / "processed" / "food_risk_profile.csv"
    materials_csv = ROOT / "data" / "processed" / "materials_permeability_enriched.csv"

    reqs_df = pd.read_csv(reqs_csv)
    foods_df = pd.read_csv(foods_csv)
    materials_df = pd.read_csv(materials_csv)

    requirements = [
        PackagingRequirement(
            food_category=row["Food_Category"],
            min_otr=_nan_none(row["Min_OTR"]),
            max_otr=_nan_none(row["Max_OTR"]),
            min_wvtr=_nan_none(row["Min_WVTR"]),
            max_wvtr=_nan_none(row["Max_WVTR"]),
            description=_nan_none(row["Description"]),
        )
        for row in reqs_df.to_dict(orient="records")
    ]

    foods = [
        FoodItem(
            code=row["code"],
            name=_nan_none(row["name"]),
            scie=_nan_none(row["scie"]),
            lang=_nan_none(row["lang"]),
            grup=_nan_none(row["grup"]),
            regn=_nan_none(row["regn"]),
            tags=_nan_none(row["tags"]),
            water=_nan_none(row["water"]),
            fatce=_nan_none(row["fatce"]),
            protcnt=_nan_none(row["protcnt"]),
            choavldf=_nan_none(row["choavldf"]),
            fibtg=_nan_none(row["fibtg"]),
            orgac=_nan_none(row["orgac"]),
            vitc=_nan_none(row["vitc"]),
            polyph=_nan_none(row["polyph"]),
            cartoid=_nan_none(row["cartoid"]),
            fasat=_nan_none(row["fasat"]),
            fauns=_nan_none(row["fauns"]),
            fapu=_nan_none(row["fapu"]),
            starch=_nan_none(row["starch"]),
            moisture_class=_nan_none(row["moisture_class"]),
            oxidation_risk_index=_nan_none(row["oxidation_risk_index"]),
            moisture_barrier_requirement=_nan_none(row["moisture_barrier_requirement"]),
            food_risk_profile=_nan_none(row["food_risk_profile"]),
        )
        for row in foods_df.to_dict(orient="records")
    ]

    maps = [
        FoodGroupMap(grup=grup, packaging_category=category)
        for grup, category in FOOD_CATEGORY_MAP.items()
    ]

    materials = [
        Material(
            base_material=_nan_none(row["Base Material"]),
            type=_nan_none(row["Type"]),
            secondary_material=_nan_none(row["Secondary Material"]),
            wvtr=_nan_none(row["WVTR"]),
            otr=_nan_none(row["OTR"]),
            wvtr_unit=_nan_none(row["WVTR unit"]),
            otr_unit=_nan_none(row["OTR unit"]),
            is_commercial_fpm=_bool(row["is_commercial_fpm"]),
            is_biobased_compostable=_bool(row["is_biobased_compostable"]),
            is_active_nanocomposite=_bool(row["is_active_nanocomposite"]),
            is_recycled_plastic=_bool(row.get("is_recycled_plastic")),
            is_recycled_plastic_fcm_rpet=_bool(row.get("is_recycled_plastic_fcm_rpet")),
            has_rpet_decontamination_proof=_bool(row.get("has_rpet_decontamination_proof")),
            compostable_is17088=_bool(row.get("compostable_is17088")),
            thickness_um=_nan_none(row.get("thickness_um")),
            has_migration_test_data=_bool(row.get("has_migration_test_data")),
            has_ink_safety_cert=_bool(row.get("has_ink_safety_cert")),
            acid_resistance=_bool(row.get("acid_resistance")),
        )
        for row in materials_df.to_dict(orient="records")
    ]

    conn = get_connection()
    try:
        PackagingRequirementRepository(conn).replace_all(requirements)
        FoodItemRepository(conn).replace_all(foods)
        FoodGroupMapRepository(conn).replace_all(maps)
        MaterialRepository(conn).replace_all(materials)
        conn.commit()
        print(
            f"Seeded {len(requirements)} packaging requirements, "
            f"{len(foods)} foods, {len(maps)} group maps, {len(materials)} materials"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    seed_db()
