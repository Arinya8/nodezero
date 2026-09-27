"""Core Rule Engine orchestrator."""

from typing import Any, Dict, List, Optional
from src.rule_engine.config import Config
from src.rule_engine.constraints import ConstraintEvaluator
from src.rule_engine.explain import attach_explanation
from src.rule_engine.models import (
    Constraint,
    FoodProfile,
    Material,
    PackagingContext,
    Recommendation,
    RecommendationResult,
    RuleResult,
)
from src.rule_engine.rules.base import BaseRule
from src.rule_engine.rules.physics import get_all_physics_rules
from src.rule_engine.rules.regulatory import get_all_regulatory_rules
from src.rule_engine.scoring import DeterministicBarrierRanker
from src.rule_engine.clustering import group_materials


class RuleEngine:
    """Packaging Recommendation Rule Engine."""

    def __init__(
        self,
        config: Optional[Config] = None,
        regulatory_rules: Optional[List[BaseRule]] = None,
        physics_rules: Optional[List[BaseRule]] = None,
    ):
        self.config = config or Config.load_from_yaml()
        self.regulatory_rules = regulatory_rules if regulatory_rules is not None else get_all_regulatory_rules(self.config)
        self.physics_rules = physics_rules if physics_rules is not None else get_all_physics_rules(self.config)
        self.ranker = DeterministicBarrierRanker()

    @classmethod
    def from_config(cls, config_path: Optional[str] = None) -> "RuleEngine":
        """Instantiate RuleEngine with configuration from file path."""
        config = Config.load_from_yaml(config_path) if config_path else Config.load_from_yaml()
        return cls(config=config)

    def get_category_constraints(self, food_category: Optional[str], food: Optional[FoodProfile] = None) -> List[Constraint]:
        """Generate constraints from food category requirement bands in configuration."""
        if not food_category and not food:
            return []
        category_key = food_category

        bounds = {
            "min_otr": food.min_otr if food else None,
            "max_otr": food.max_otr if food else None,
            "min_wvtr": food.min_wvtr if food else None,
            "max_wvtr": food.max_wvtr if food else None,
        }
        configured = self.config.get_category_bounds(category_key) or {} if category_key else {}
        for key in bounds:
            if bounds[key] is None:
                bounds[key] = configured.get(key)
        if not any(value is not None for value in bounds.values()):
            return []

        constraints = []
        min_otr = bounds.get("min_otr")
        max_otr = bounds.get("max_otr")
        min_wvtr = bounds.get("min_wvtr")
        max_wvtr = bounds.get("max_wvtr")

        if min_otr is not None and max_otr is not None:
            constraints.append(Constraint(
                metric="otr_cm3_m2_day",
                operator="between",
                value=(float(min_otr), float(max_otr)),
                source_rule="CategoryBand",
                reason=f"Category band constraint for '{food_category}': OTR must be between {min_otr} and {max_otr} cm3/m2/day.",
            ))
        elif max_otr is not None:
            constraints.append(Constraint(
                metric="otr_cm3_m2_day",
                operator="<=",
                value=float(max_otr),
                source_rule="CategoryBand",
                reason=f"Category band constraint for '{food_category}': OTR max limit <= {max_otr} cm3/m2/day.",
            ))
        elif min_otr is not None:
            constraints.append(Constraint(
                metric="otr_cm3_m2_day",
                operator=">=",
                value=float(min_otr),
                source_rule="CategoryBand",
                reason=f"Category band constraint for '{food_category}': OTR min limit >= {min_otr} cm3/m2/day.",
            ))

        if min_wvtr is not None and max_wvtr is not None:
            constraints.append(Constraint(
                metric="wvtr_g_m2_day",
                operator="between",
                value=(float(min_wvtr), float(max_wvtr)),
                source_rule="CategoryBand",
                reason=f"Category band constraint for '{food_category}': WVTR must be between {min_wvtr} and {max_wvtr} g/m2/day.",
            ))
        elif max_wvtr is not None:
            constraints.append(Constraint(
                metric="wvtr_g_m2_day",
                operator="<=",
                value=float(max_wvtr),
                source_rule="CategoryBand",
                reason=f"Category band constraint for '{food_category}': WVTR max limit <= {max_wvtr} g/m2/day.",
            ))
        elif min_wvtr is not None:
            constraints.append(Constraint(
                metric="wvtr_g_m2_day",
                operator=">=",
                value=float(min_wvtr),
                source_rule="CategoryBand",
                reason=f"Category band constraint for '{food_category}': WVTR min limit >= {min_wvtr} g/m2/day.",
            ))

        return constraints

    def evaluate_material(
        self,
        food: FoodProfile,
        material: Material,
        context: Optional[PackagingContext] = None,
    ) -> Recommendation:
        """Evaluate a single material candidate against food profile and runtime context.

        Applies strict 5-tier evaluation precedence:
        1. REJECTED_REGULATORY (hard regulatory rule failure)
        2. REJECTED_BARRIER (hard physical constraint failure)
        3. REQUIRES_REVIEW (unknown critical safety/compliance evidence or unmeasured metric)
        4. FEASIBLE (all applicable hard requirements passed)
        """
        ctx = context or PackagingContext()
        rule_results: List[RuleResult] = []
        collected_constraints: List[Constraint] = []
        assumptions: List[str] = [
            "Food-category OTR bands are interpreted in cm3/m2/day.",
            "Food-category WVTR bands are interpreted in g/m2/day.",
        ]
        warnings: List[str] = []

        # Step 1: Evaluate Regulatory Rules (Group 1)
        reg_fail = False
        reg_unknown = False
        for rule in self.regulatory_rules:
            res = rule.evaluate(food, material, ctx)
            rule_results.append(res)
            if res.status == "FAIL":
                reg_fail = True
            elif res.status == "UNKNOWN":
                reg_unknown = True

        # Step 2: Evaluate Physics Rules (Group 2) -> Collect emitted constraints
        for rule in self.physics_rules:
            res = rule.evaluate(food, material, ctx)
            rule_results.append(res)
            if res.evidence and "constraint" in res.evidence:
                collected_constraints.append(res.evidence["constraint"])

        # Step 3: Add Food Category requirement band constraints
        category_constraints = self.get_category_constraints(food.food_category, food)
        collected_constraints.extend(category_constraints)

        # Step 4: Evaluate collected constraints against candidate material
        barrier_status, constraint_evals = ConstraintEvaluator.evaluate_all(collected_constraints, material)
        for constraint, constraint_status, reason in constraint_evals:
            rule_results.append(RuleResult(
                rule_id=constraint.source_rule,
                group="PHYSICS",
                status=constraint_status,
                severity="HARD",
                reason=reason,
                evidence={"constraint": constraint},
            ))
        for result in rule_results:
            if result.group == "PHYSICS" and result.severity == "HARD":
                if result.status == "FAIL":
                    barrier_status = "FAIL"
                elif result.status == "UNKNOWN" and barrier_status != "FAIL":
                    barrier_status = "UNKNOWN"

        # Determine limiting barrier type
        limiting_barrier = None
        for c in collected_constraints:
            if c.metric == "otr_cm3_m2_day":
                limiting_barrier = "OTR_CRITICAL"
            elif c.metric == "wvtr_g_m2_day" and limiting_barrier != "OTR_CRITICAL":
                limiting_barrier = "WVTR_CRITICAL"

        # Determine Final Candidate Status via Precedence
        if reg_fail:
            status = "REJECTED_REGULATORY"
            reg_status_str = "FAIL"
        elif barrier_status == "FAIL":
            status = "REJECTED_BARRIER"
            reg_status_str = "PASS" if not reg_unknown else "UNKNOWN"
        elif reg_unknown or barrier_status == "UNKNOWN":
            status = "REQUIRES_REVIEW"
            reg_status_str = "UNKNOWN" if reg_unknown else "PASS"
            if barrier_status == "UNKNOWN":
                warnings.append("Permeability or physical metrics missing/incomparable for evaluated constraints.")
            if reg_unknown:
                warnings.append("One or more regulatory compliance fields are absent in dataset.")
        else:
            status = "FEASIBLE"
            reg_status_str = "PASS"

        material_name = f"{material.base_material or 'Unknown'}"
        if material.structure_type:
            material_name += f" ({material.structure_type})"

        rec = Recommendation(
            material_id=material.material_id,
            material_name=material_name,
            status=status,
            regulatory_status=reg_status_str,
            barrier_status=barrier_status,
            limiting_barrier_type=limiting_barrier,
            constraints=collected_constraints,
            rule_results=rule_results,
            assumptions=assumptions,
            warnings=warnings,
        )

        # If FEASIBLE, score material
        if status == "FEASIBLE":
            self.ranker.score(food, material, rec, ctx)

        # Generate audit explanation
        attach_explanation(food, material, rec, ctx)

        return rec

    def recommend(
        self,
        food: FoodProfile,
        materials: List[Material],
        context: Optional[PackagingContext] = None,
        top_k: int = 10,
        use_clustering: bool = True,
    ) -> RecommendationResult:
        """Evaluate candidate materials for a food item and return structured recommendation result."""
        ctx = context or PackagingContext()

        feasible_list: List[Recommendation] = []
        requires_review_list: List[Recommendation] = []
        rejected_list: List[Recommendation] = []
        if not isinstance(top_k, int) or top_k < 0:
            raise ValueError("top_k must be a non-negative integer")

        clustered = group_materials(materials) if use_clustering else None
        candidate_materials = clustered.materials if clustered else materials
        indexed = list(enumerate(candidate_materials))
        if clustered:
            indexed.sort(key=lambda item: (
                clustered.cluster_by_material[item[0]] is None,
                clustered.cluster_by_material[item[0]] if clustered.cluster_by_material[item[0]] is not None else 0,
                item[0],
            ))
        for material_index, mat in indexed:
            rec = self.evaluate_material(food, mat, ctx)
            if clustered:
                rec.cluster_id = clustered.cluster_by_material[material_index]
            if rec.status == "FEASIBLE":
                feasible_list.append(rec)
            elif rec.status == "REQUIRES_REVIEW":
                requires_review_list.append(rec)
            else:
                rejected_list.append(rec)

        # Sort FEASIBLE candidates deterministically by score
        feasible_ranked = sorted(feasible_list, key=lambda r: (r.score or 0.0), reverse=True)[:top_k]

        warnings = []
        if not feasible_ranked:
            warnings.append("No FEASIBLE candidate materials were found that satisfy all hard constraints without missing evidence.")

        assumptions = [
            "Food-category OTR bands are interpreted in cm3/m2/day.",
            "Food-category WVTR bands are interpreted in g/m2/day.",
        ]

        return RecommendationResult(
            food=food,
            packaging_category=food.food_category,
            candidates=feasible_ranked,
            requires_review_candidates=requires_review_list,
            rejected_candidates=rejected_list,
            warnings=warnings,
            assumptions=assumptions,
            cluster_summary={
                "enabled": bool(clustered),
                "clustered_count": clustered.clustered_count if clustered else 0,
                "unclustered_count": clustered.unclustered_count if clustered else 0,
                "cluster_count": clustered.cluster_count if clustered else 0,
                "cluster_by_material": clustered.cluster_by_material if clustered else [],
                "explanation": clustered.explanation if clustered else "Clustering disabled; all materials were evaluated directly.",
                "applied_before_rules": True,
            },
        )

    def data_quality_report(
        self,
        food_profiles: List[FoodProfile],
        materials: List[Material],
    ) -> Dict[str, Any]:
        """Generate compact data quality audit report."""
        total_foods = len(food_profiles)
        mapped_foods = sum(1 for f in food_profiles if f.food_category is not None)
        unmapped_foods = total_foods - mapped_foods

        total_materials = len(materials)
        otr_normalized = sum(1 for m in materials if m.otr_status in ("CANONICAL", "CONVERTED"))
        wvtr_normalized = sum(1 for m in materials if m.wvtr_status in ("CANONICAL", "CONVERTED"))
        both_normalized = sum(
            1 for m in materials
            if m.otr_status in ("CANONICAL", "CONVERTED") and m.wvtr_status in ("CANONICAL", "CONVERTED")
        )

        return {
            "total_food_records": total_foods,
            "mapped_food_categories": mapped_foods,
            "unmapped_foods": unmapped_foods,
            "total_materials": total_materials,
            "materials_with_normalized_otr": otr_normalized,
            "materials_with_normalized_wvtr": wvtr_normalized,
            "materials_with_both_normalized": both_normalized,
        }
