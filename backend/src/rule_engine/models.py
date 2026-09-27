"""Canonical data models for the Packaging Recommendation Rule Engine."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal


@dataclass
class FoodProfile:
    """Canonical representation of a food record."""

    code: str
    name: str
    food_category: Optional[str] = None
    water_pct: Optional[float] = None
    fat_pct: Optional[float] = None
    moisture_class: Optional[str] = None
    oxidation_risk_index: Optional[float] = None
    moisture_barrier_requirement: Optional[str] = None
    food_risk_profile: Optional[str] = None
    tags: Optional[str] = None
    min_otr: Optional[float] = None
    max_otr: Optional[float] = None
    min_wvtr: Optional[float] = None
    max_wvtr: Optional[float] = None
    requirement_description: Optional[str] = None
    raw_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PackagingContext:
    """Runtime operational packaging context supplied by user or system."""

    target_shelf_life_days: Optional[float] = None
    storage_temperature_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    light_sensitive: Optional[bool] = None
    physical_form: Optional[str] = None
    processing_method: Optional[str] = None
    packaging_format: Optional[str] = None
    unit_pack_weight_kg: Optional[float] = None
    headspace_o2_pct: Optional[float] = None
    headspace_co2_pct: Optional[float] = None
    max_unit_cost: Optional[float] = None
    target_epr_category: Optional[str] = None
    is_fresh_produce: bool = False
    pH: Optional[float] = None
    water_activity: Optional[float] = None
    thickness_um: Optional[float] = None
    is_printed: Optional[bool] = None


@dataclass
class Material:
    """Canonical representation of a candidate packaging material."""

    material_id: str
    base_material: Optional[str] = None
    structure_type: Optional[str] = None
    secondary_material: Optional[str] = None

    # WVTR (Water Vapor Transmission Rate)
    wvtr_raw: Optional[float] = None
    wvtr_unit: Optional[str] = None
    wvtr_g_m2_day: Optional[float] = None
    wvtr_status: str = "MISSING"  # CANONICAL, CONVERTED, INCOMPARABLE, MISSING

    # OTR (Oxygen Transmission Rate)
    otr_raw: Optional[float] = None
    otr_unit: Optional[str] = None
    otr_cm3_m2_day: Optional[float] = None
    otr_status: str = "MISSING"  # CANONICAL, CONVERTED, INCOMPARABLE, MISSING

    # Flags & Regulatory features
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
    raw_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Constraint:
    """Evaluatable physical or regulatory constraint."""

    metric: str  # e.g., "otr_cm3_m2_day", "wvtr_g_m2_day", "material_class"
    operator: str  # "<=", ">=", "==", "between", "not_in"
    value: Any  # float threshold, tuple (min, max), or list/set
    source_rule: str
    reason: str


@dataclass
class RuleResult:
    """Individual rule evaluation outcome."""

    rule_id: str
    group: str  # "REGULATORY", "PHYSICS"
    status: Literal["PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE"]
    severity: Literal["HARD", "SOFT", "INFO"]
    reason: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Recommendation:
    """Detailed recommendation object for a single material candidate."""

    material_id: str
    material_name: str
    status: Literal["FEASIBLE", "REQUIRES_REVIEW", "REJECTED_BARRIER", "REJECTED_REGULATORY"]
    score: Optional[float] = None
    score_components: Dict[str, Optional[float]] = field(default_factory=dict)
    regulatory_status: str = "UNKNOWN"
    barrier_status: str = "UNKNOWN"
    limiting_barrier_type: Optional[str] = None
    constraints: List[Constraint] = field(default_factory=list)
    rule_results: List[RuleResult] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    explanation: str = ""
    cluster_id: Optional[int] = None


@dataclass
class RecommendationResult:
    """Overall engine result for a food item query."""

    food: FoodProfile
    packaging_category: Optional[str]
    candidates: List[Recommendation]  # Ranked FEASIBLE candidates
    requires_review_candidates: List[Recommendation]
    rejected_candidates: List[Recommendation]
    warnings: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    cluster_summary: Dict[str, Any] = field(default_factory=dict)
