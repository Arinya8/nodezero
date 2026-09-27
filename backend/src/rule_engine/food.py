"""Food data ingestion, normalization, and packaging category mapping module."""

import sqlite3
from typing import Dict, List, Optional
import pandas as pd

from src.rule_engine.models import FoodProfile
from src.preprocessing.food_category.food_category_map import FOOD_CATEGORY_MAP


def map_food_to_packaging_category(grup_or_category: Optional[str]) -> Optional[str]:
    """Map raw food group (e.g. IFCT grup) or raw food category to packaging requirement category."""
    if not grup_or_category:
        return None

    cleaned = grup_or_category.strip()
    if cleaned in FOOD_CATEGORY_MAP:
        return FOOD_CATEGORY_MAP[cleaned]

    return cleaned


def create_food_profile_from_dict(row: Dict[str, str | float | int | None]) -> FoodProfile:
    """Construct a canonical FoodProfile object from a dictionary or database row."""
    code = str(row.get("code") or row.get("id") or "UNKNOWN")
    name = str(row.get("name") or "Unnamed Food")
    grup = row.get("grup")
    food_category = map_food_to_packaging_category(
        str(row.get("packaging_category")) if row.get("packaging_category") else (str(grup) if grup else None)
    )

    water_pct = float(row["water"]) if row.get("water") is not None and str(row.get("water")).strip() != "" else None
    fat_pct = float(row["fatce"]) if row.get("fatce") is not None and str(row.get("fatce")).strip() != "" else None

    def optional_float(*keys):
        for key in keys:
            value = row.get(key)
            if value is not None and str(value).strip() != "":
                return float(value)
        return None

    return FoodProfile(
        code=code,
        name=name,
        food_category=food_category,
        water_pct=water_pct,
        fat_pct=fat_pct,
        moisture_class=str(row["moisture_class"]) if row.get("moisture_class") else None,
        oxidation_risk_index=float(row["oxidation_risk_index"]) if row.get("oxidation_risk_index") is not None else None,
        moisture_barrier_requirement=str(row["moisture_barrier_requirement"]) if row.get("moisture_barrier_requirement") else None,
        food_risk_profile=str(row["food_risk_profile"]) if row.get("food_risk_profile") else None,
        tags=str(row["tags"]) if row.get("tags") else None,
        min_otr=optional_float("min_otr", "Min_OTR"),
        max_otr=optional_float("max_otr", "Max_OTR"),
        min_wvtr=optional_float("min_wvtr", "Min_WVTR"),
        max_wvtr=optional_float("max_wvtr", "Max_WVTR"),
        requirement_description=row.get("description") or row.get("Description"),
        raw_attributes=dict(row),
    )


def load_food_profiles_from_db(db_path: str) -> List[FoodProfile]:
    """Load food profiles from SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Query view or food_item table directly
    try:
        cur.execute("SELECT * FROM food_packaging_requirement")
    except sqlite3.OperationalError:
        cur.execute("SELECT * FROM food_item")

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return [create_food_profile_from_dict(r) for r in rows]


def load_food_profiles_from_csv(csv_path: str) -> List[FoodProfile]:
    """Load food profiles from processed CSV file."""
    df = pd.read_csv(csv_path)
    return [create_food_profile_from_dict(row.to_dict()) for _, row in df.iterrows()]


def load_food_profiles_from_sources(food_csv_path: str, requirements_csv_path: str) -> List[FoodProfile]:
    """Build the searchable profiles directly from the tracked source CSVs."""
    foods = pd.read_csv(food_csv_path)
    requirements = pd.read_csv(requirements_csv_path).rename(columns={"Food_Category": "packaging_category"})
    foods["packaging_category"] = foods["grup"].map(FOOD_CATEGORY_MAP)
    merged = foods.merge(requirements, on="packaging_category", how="left")

    profiles = []
    keep = {
        "code", "name", "scie", "lang", "grup", "regn", "tags", "water", "fatce",
        "protcnt", "fapu", "fams", "vitc", "polyph", "cartoid", "packaging_category",
        "Min_OTR", "Max_OTR", "Min_WVTR", "Max_WVTR", "Description",
    }
    for raw in merged.to_dict(orient="records"):
        row = {
            key: (None if pd.isna(raw.get(key)) else raw.get(key))
            for key in keep
        }
        water = pd.to_numeric(row.get("water"), errors="coerce")
        fat = pd.to_numeric(row.get("fatce"), errors="coerce")
        row["water"] = None if pd.isna(water) else float(water)
        row["fatce"] = None if pd.isna(fat) else float(fat)
        row["moisture_class"] = (
            "low" if pd.notna(water) and water < 20 else
            "medium" if pd.notna(water) and water < 50 else
            "high" if pd.notna(water) and water < 75 else
            "very_high" if pd.notna(water) else None
        )
        row["moisture_barrier_requirement"] = (
            "high" if pd.notna(water) and water >= 75 else
            "medium" if pd.notna(water) and water >= 40 else
            "high_for_moisture_gain" if pd.notna(water) else "unknown"
        )
        def nutrient(key: str) -> float:
            value = pd.to_numeric(row.get(key), errors="coerce")
            return float(value) if pd.notna(value) else 0.0

        row["oxidation_risk_index"] = (
            nutrient("fapu") + 0.5 * nutrient("fams") + 0.2 * nutrient("fatce")
            - 0.01 * nutrient("vitc") - 0.01 * nutrient("polyph") - 0.01 * nutrient("cartoid")
        )
        row["food_risk_profile"] = row["moisture_barrier_requirement"]
        profiles.append(create_food_profile_from_dict(row))
    return profiles
