from dataclasses import dataclass
from typing import Any, Mapping, Optional


def _get(row: Mapping[str, Any], key: str, default=None):
    try:
        value = row[key]
    except (KeyError, IndexError):
        return default
    return default if value is None else value


def _bool_optional(value):
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"1", "true", "yes", "t"}:
            return True
        if cleaned in {"0", "false", "no", "f"}:
            return False
        return None
    return bool(value)


@dataclass
class PackagingRequirement:
    food_category: str
    min_otr: Optional[float] = None
    max_otr: Optional[float] = None
    min_wvtr: Optional[float] = None
    max_wvtr: Optional[float] = None
    description: Optional[str] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "PackagingRequirement":
        return cls(
            food_category=_get(row, "food_category"),
            min_otr=_get(row, "min_otr"),
            max_otr=_get(row, "max_otr"),
            min_wvtr=_get(row, "min_wvtr"),
            max_wvtr=_get(row, "max_wvtr"),
            description=_get(row, "description"),
        )


@dataclass
class FoodItem:
    code: str
    name: Optional[str] = None
    scie: Optional[str] = None
    lang: Optional[str] = None
    grup: Optional[str] = None
    regn: Optional[int] = None
    tags: Optional[str] = None
    water: Optional[float] = None
    fatce: Optional[float] = None
    protcnt: Optional[float] = None
    choavldf: Optional[float] = None
    fibtg: Optional[float] = None
    orgac: Optional[float] = None
    vitc: Optional[float] = None
    polyph: Optional[float] = None
    cartoid: Optional[float] = None
    fasat: Optional[float] = None
    fauns: Optional[float] = None
    fapu: Optional[float] = None
    starch: Optional[float] = None
    moisture_class: Optional[str] = None
    oxidation_risk_index: Optional[float] = None
    moisture_barrier_requirement: Optional[str] = None
    food_risk_profile: Optional[str] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "FoodItem":
        return cls(
            code=_get(row, "code"),
            name=_get(row, "name"),
            scie=_get(row, "scie"),
            lang=_get(row, "lang"),
            grup=_get(row, "grup"),
            regn=_get(row, "regn"),
            tags=_get(row, "tags"),
            water=_get(row, "water"),
            fatce=_get(row, "fatce"),
            protcnt=_get(row, "protcnt"),
            choavldf=_get(row, "choavldf"),
            fibtg=_get(row, "fibtg"),
            orgac=_get(row, "orgac"),
            vitc=_get(row, "vitc"),
            polyph=_get(row, "polyph"),
            cartoid=_get(row, "cartoid"),
            fasat=_get(row, "fasat"),
            fauns=_get(row, "fauns"),
            fapu=_get(row, "fapu"),
            starch=_get(row, "starch"),
            moisture_class=_get(row, "moisture_class"),
            oxidation_risk_index=_get(row, "oxidation_risk_index"),
            moisture_barrier_requirement=_get(row, "moisture_barrier_requirement"),
            food_risk_profile=_get(row, "food_risk_profile"),
        )


@dataclass
class FoodGroupMap:
    grup: str
    packaging_category: Optional[str] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "FoodGroupMap":
        return cls(
            grup=_get(row, "grup"),
            packaging_category=_get(row, "packaging_category"),
        )


@dataclass
class Material:
    id: Optional[int] = None
    base_material: Optional[str] = None
    type: Optional[str] = None
    secondary_material: Optional[str] = None
    wvtr: Optional[float] = None
    otr: Optional[float] = None
    wvtr_unit: Optional[str] = None
    otr_unit: Optional[str] = None
    is_commercial_fpm: Optional[bool] = None
    is_biobased_compostable: Optional[bool] = None
    is_active_nanocomposite: Optional[bool] = None
    is_recycled_plastic: Optional[bool] = None
    is_recycled_plastic_fcm_rpet: Optional[bool] = None
    has_rpet_decontamination_proof: Optional[bool] = None
    compostable_is17088: Optional[bool] = None
    thickness_um: Optional[float] = None
    has_migration_test_data: Optional[bool] = None
    has_ink_safety_cert: Optional[bool] = None
    acid_resistance: Optional[bool] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Material":
        return cls(
            id=_get(row, "id"),
            base_material=_get(row, "base_material"),
            type=_get(row, "type"),
            secondary_material=_get(row, "secondary_material"),
            wvtr=_get(row, "wvtr"),
            otr=_get(row, "otr"),
            wvtr_unit=_get(row, "wvtr_unit"),
            otr_unit=_get(row, "otr_unit"),
            is_commercial_fpm=_bool_optional(_get(row, "is_commercial_fpm")),
            is_biobased_compostable=_bool_optional(_get(row, "is_biobased_compostable")),
            is_active_nanocomposite=_bool_optional(_get(row, "is_active_nanocomposite")),
            is_recycled_plastic=_bool_optional(_get(row, "is_recycled_plastic")),
            is_recycled_plastic_fcm_rpet=_bool_optional(_get(row, "is_recycled_plastic_fcm_rpet")),
            has_rpet_decontamination_proof=_bool_optional(_get(row, "has_rpet_decontamination_proof")),
            compostable_is17088=_bool_optional(_get(row, "compostable_is17088")),
            thickness_um=_get(row, "thickness_um"),
            has_migration_test_data=_bool_optional(_get(row, "has_migration_test_data")),
            has_ink_safety_cert=_bool_optional(_get(row, "has_ink_safety_cert")),
            acid_resistance=_bool_optional(_get(row, "acid_resistance")),
        )


@dataclass
class FoodPackagingRequirement(FoodItem):
    packaging_category: Optional[str] = None
    min_otr: Optional[float] = None
    max_otr: Optional[float] = None
    min_wvtr: Optional[float] = None
    max_wvtr: Optional[float] = None
    description: Optional[str] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "FoodPackagingRequirement":
        base = FoodItem.from_row(row)
        return cls(
            **base.__dict__,
            packaging_category=_get(row, "packaging_category"),
            min_otr=_get(row, "min_otr"),
            max_otr=_get(row, "max_otr"),
            min_wvtr=_get(row, "min_wvtr"),
            max_wvtr=_get(row, "max_wvtr"),
            description=_get(row, "description"),
        )
