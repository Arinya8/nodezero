"""Material candidate data ingestion and unit normalization module."""

import sqlite3
from typing import Dict, List, Optional
import pandas as pd

from src.rule_engine.models import Material
from src.rule_engine.normalization import normalize_otr, normalize_wvtr


def create_material_from_dict(row: Dict[str, str | float | int | None]) -> Material:
    """Transform a raw material row into a canonical normalized Material dataclass."""
    material_id = str(row.get("id") or row.get("material_id") or row.get("Base Material") or "UNKNOWN")
    base_material = str(row.get("base_material") or row.get("Base Material") or "").strip() or None
    structure_type = str(row.get("type") or row.get("Type") or "").strip() or None
    secondary_material = str(row.get("secondary_material") or row.get("Secondary Material") or "").strip() or None

    wvtr_raw = float(row["wvtr"]) if row.get("wvtr") is not None and str(row.get("wvtr")).strip() != "" else (
        float(row["WVTR"]) if row.get("WVTR") is not None and str(row.get("WVTR")).strip() != "" else None
    )
    wvtr_unit = str(row.get("wvtr_unit") or row.get("WVTR unit") or "").strip() or None

    otr_raw = float(row["otr"]) if row.get("otr") is not None and str(row.get("otr")).strip() != "" else (
        float(row["OTR"]) if row.get("OTR") is not None and str(row.get("OTR")).strip() != "" else None
    )
    otr_unit = str(row.get("otr_unit") or row.get("OTR unit") or "").strip() or None

    thickness_um = float(row["thickness_um"]) if row.get("thickness_um") is not None else None

    # Normalize permeability values
    wvtr_g_m2_day, wvtr_status = normalize_wvtr(wvtr_raw, wvtr_unit, thickness_um)
    otr_cm3_m2_day, otr_status = normalize_otr(otr_raw, otr_unit, thickness_um)

    def parse_bool(val: str | float | int | None) -> Optional[bool]:
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        val_str = str(val).strip().lower()
        if val_str in ("1", "true", "yes", "t"):
            return True
        if val_str in ("0", "false", "no", "f"):
            return False
        return None

    return Material(
        material_id=material_id,
        base_material=base_material,
        structure_type=structure_type,
        secondary_material=secondary_material,
        wvtr_raw=wvtr_raw,
        wvtr_unit=wvtr_unit,
        wvtr_g_m2_day=wvtr_g_m2_day,
        wvtr_status=wvtr_status,
        otr_raw=otr_raw,
        otr_unit=otr_unit,
        otr_cm3_m2_day=otr_cm3_m2_day,
        otr_status=otr_status,
        is_commercial_fpm=parse_bool(row.get("is_commercial_fpm")),
        is_biobased_compostable=parse_bool(row.get("is_biobased_compostable")),
        is_active_nanocomposite=parse_bool(row.get("is_active_nanocomposite")),
        is_recycled_plastic=parse_bool(row.get("is_recycled_plastic")),
        is_recycled_plastic_fcm_rpet=parse_bool(row.get("is_recycled_plastic_fcm_rpet")),
        has_rpet_decontamination_proof=parse_bool(row.get("has_rpet_decontamination_proof")),
        compostable_is17088=parse_bool(row.get("compostable_is17088")),
        thickness_um=thickness_um,
        has_migration_test_data=parse_bool(row.get("has_migration_test_data")),
        has_ink_safety_cert=parse_bool(row.get("has_ink_safety_cert")),
        acid_resistance=parse_bool(row.get("acid_resistance")),
        raw_attributes=dict(row),
    )


def load_materials_from_db(db_path: str) -> List[Material]:
    """Load material candidates from SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM material")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return [create_material_from_dict(r) for r in rows]


def load_materials_from_csv(csv_path: str) -> List[Material]:
    """Load material candidates from processed CSV file."""
    df = pd.read_csv(csv_path)
    return [create_material_from_dict(row.to_dict()) for _, row in df.iterrows()]
