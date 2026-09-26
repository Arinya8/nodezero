from typing import Iterable, List, Optional, Sequence

from src.database.schemas import (
    FoodGroupMap,
    FoodItem,
    FoodPackagingRequirement,
    Material,
    PackagingRequirement,
)


def _bool_int(value):
    return None if value is None else int(bool(value))


class PackagingRequirementRepository:
    def __init__(self, conn):
        self.conn = conn

    def replace_all(self, rows: Sequence[PackagingRequirement]) -> None:
        self.conn.execute("DELETE FROM packaging_requirement")
        self.conn.executemany(
            """
            INSERT INTO packaging_requirement (
                food_category, min_otr, max_otr, min_wvtr, max_wvtr, description
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (r.food_category, r.min_otr, r.max_otr, r.min_wvtr, r.max_wvtr, r.description)
                for r in rows
            ],
        )

    def list_all(self) -> List[PackagingRequirement]:
        cur = self.conn.execute("SELECT * FROM packaging_requirement ORDER BY food_category")
        return [PackagingRequirement.from_row(row) for row in cur.fetchall()]

    def get(self, food_category: str) -> Optional[PackagingRequirement]:
        cur = self.conn.execute(
            "SELECT * FROM packaging_requirement WHERE food_category = ?",
            (food_category,),
        )
        row = cur.fetchone()
        return PackagingRequirement.from_row(row) if row else None


class FoodItemRepository:
    def __init__(self, conn):
        self.conn = conn

    def replace_all(self, rows: Sequence[FoodItem]) -> None:
        self.conn.execute("DELETE FROM food_item")
        self.conn.executemany(
            """
            INSERT INTO food_item (
                code, name, scie, lang, grup, regn, tags, water, fatce, protcnt,
                choavldf, fibtg, orgac, vitc, polyph, cartoid, fasat, fauns, fapu,
                starch, moisture_class, oxidation_risk_index,
                moisture_barrier_requirement, food_risk_profile
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r.code, r.name, r.scie, r.lang, r.grup, r.regn, r.tags, r.water,
                    r.fatce, r.protcnt, r.choavldf, r.fibtg, r.orgac, r.vitc,
                    r.polyph, r.cartoid, r.fasat, r.fauns, r.fapu, r.starch,
                    r.moisture_class, r.oxidation_risk_index,
                    r.moisture_barrier_requirement, r.food_risk_profile,
                )
                for r in rows
            ],
        )

    def list_all(self) -> List[FoodItem]:
        cur = self.conn.execute("SELECT * FROM food_item ORDER BY code")
        return [FoodItem.from_row(row) for row in cur.fetchall()]

    def get(self, code: str) -> Optional[FoodItem]:
        cur = self.conn.execute("SELECT * FROM food_item WHERE code = ?", (code,))
        row = cur.fetchone()
        return FoodItem.from_row(row) if row else None


class FoodGroupMapRepository:
    def __init__(self, conn):
        self.conn = conn

    def replace_all(self, rows: Sequence[FoodGroupMap]) -> None:
        self.conn.execute("DELETE FROM food_group_map")
        self.conn.executemany(
            "INSERT INTO food_group_map (grup, packaging_category) VALUES (?, ?)",
            [(r.grup, r.packaging_category) for r in rows],
        )

    def list_all(self) -> List[FoodGroupMap]:
        cur = self.conn.execute("SELECT * FROM food_group_map ORDER BY grup")
        return [FoodGroupMap.from_row(row) for row in cur.fetchall()]

    def get(self, grup: str) -> Optional[FoodGroupMap]:
        cur = self.conn.execute("SELECT * FROM food_group_map WHERE grup = ?", (grup,))
        row = cur.fetchone()
        return FoodGroupMap.from_row(row) if row else None


class MaterialRepository:
    def __init__(self, conn):
        self.conn = conn

    def replace_all(self, rows: Iterable[Material]) -> None:
        self.conn.execute("DELETE FROM material")
        self.conn.executemany(
            """
            INSERT INTO material (
                base_material, type, secondary_material, wvtr, otr, wvtr_unit, otr_unit,
                is_commercial_fpm, is_biobased_compostable, is_active_nanocomposite,
                is_recycled_plastic, is_recycled_plastic_fcm_rpet, has_rpet_decontamination_proof,
                compostable_is17088, thickness_um, has_migration_test_data, has_ink_safety_cert, acid_resistance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r.base_material, r.type, r.secondary_material, r.wvtr, r.otr,
                    r.wvtr_unit, r.otr_unit, _bool_int(r.is_commercial_fpm),
                    _bool_int(r.is_biobased_compostable),
                    _bool_int(r.is_active_nanocomposite),
                    _bool_int(r.is_recycled_plastic),
                    _bool_int(r.is_recycled_plastic_fcm_rpet),
                    _bool_int(r.has_rpet_decontamination_proof),
                    _bool_int(r.compostable_is17088),
                    r.thickness_um,
                    _bool_int(r.has_migration_test_data),
                    _bool_int(r.has_ink_safety_cert),
                    _bool_int(r.acid_resistance),
                )
                for r in rows
            ],
        )

    def list_all(self) -> List[Material]:
        cur = self.conn.execute("SELECT * FROM material ORDER BY id")
        return [Material.from_row(row) for row in cur.fetchall()]

    def get(self, material_id: int) -> Optional[Material]:
        cur = self.conn.execute("SELECT * FROM material WHERE id = ?", (material_id,))
        row = cur.fetchone()
        return Material.from_row(row) if row else None


class FoodPackagingRequirementRepository:
    def __init__(self, conn):
        self.conn = conn

    def list_all(self) -> List[FoodPackagingRequirement]:
        cur = self.conn.execute("SELECT * FROM food_packaging_requirement ORDER BY code")
        return [FoodPackagingRequirement.from_row(row) for row in cur.fetchall()]

    def get(self, code: str) -> Optional[FoodPackagingRequirement]:
        cur = self.conn.execute(
            "SELECT * FROM food_packaging_requirement WHERE code = ?",
            (code,),
        )
        row = cur.fetchone()
        return FoodPackagingRequirement.from_row(row) if row else None
