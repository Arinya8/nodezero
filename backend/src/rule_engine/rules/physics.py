"""Group 2 Physics & Barrier Rules (R2.1 - R2.4)."""

from typing import List, Optional, Tuple, Any, Dict
from src.rule_engine.config import Config
from src.rule_engine.models import Constraint, FoodProfile, Material, PackagingContext, RuleResult
from src.rule_engine.rules.base import BaseRule


class HighFatOxidationRule(BaseRule):
    """R2.1 - High-fat oxidation risk rule emitting OTR constraint."""

    rule_id = "R2.1"
    name = "High-Fat Oxidation Risk"
    group = "PHYSICS"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        fat_threshold = 15.0
        max_otr = 10.0
        if self.config:
            cfg = self.config.get_rule_config("high_fat")
            fat_threshold = cfg.get("fat_pct_threshold", 15.0)
            max_otr = cfg.get("max_otr", 10.0)

        fat_pct = food.fat_pct
        if fat_pct is None:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="NOT_APPLICABLE",
                severity="HARD",
                reason="Fat percentage is unknown for this food item.",
            )

        if fat_pct > fat_threshold:
            constraint = Constraint(
                metric="otr_cm3_m2_day",
                operator="<=",
                value=max_otr,
                source_rule=self.rule_id,
                reason=f"High-fat content ({fat_pct}% > {fat_threshold}%): requires strict OTR barrier <= {max_otr} cm3/m2/day.",
            )
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="PASS",
                severity="HARD",
                reason=f"Emitted OTR constraint <= {max_otr} due to high fat content ({fat_pct}%).",
                evidence={"constraint": constraint, "fat_pct": fat_pct},
            )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="NOT_APPLICABLE",
            severity="HARD",
            reason=f"Fat content ({fat_pct}%) is below high-fat threshold ({fat_threshold}%).",
        )


class HygroscopicMoistureRule(BaseRule):
    """R2.2 - Hygroscopic / moisture barrier rule emitting WVTR constraint."""

    rule_id = "R2.2"
    name = "Hygroscopic Moisture Barrier"
    group = "PHYSICS"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        moisture_threshold = 10.0
        aw_threshold = 0.3
        max_wvtr = 1.0

        if self.config:
            cfg = self.config.get_rule_config("hygroscopic")
            moisture_threshold = cfg.get("moisture_pct_threshold", 10.0)
            aw_threshold = cfg.get("water_activity_threshold", 0.3)
            max_wvtr = cfg.get("max_wvtr", 1.0)

        is_hygroscopic = False
        reasons = []

        if food.water_pct is not None and food.water_pct < moisture_threshold:
            is_hygroscopic = True
            reasons.append(f"Low moisture content ({food.water_pct}% < {moisture_threshold}%)")

        if context.water_activity is not None and context.water_activity < aw_threshold:
            is_hygroscopic = True
            reasons.append(f"Low water activity ({context.water_activity} < {aw_threshold})")

        if food.moisture_barrier_requirement in ("High", "Very High"):
            is_hygroscopic = True
            reasons.append(f"High moisture barrier requirement derived flag")

        if is_hygroscopic:
            constraint = Constraint(
                metric="wvtr_g_m2_day",
                operator="<=",
                value=max_wvtr,
                source_rule=self.rule_id,
                reason="; ".join(reasons) + f": requires WVTR <= {max_wvtr} g/m2/day.",
            )
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="PASS",
                severity="HARD",
                reason=f"Emitted WVTR constraint <= {max_wvtr} g/m2/day for hygroscopic food.",
                evidence={"constraint": constraint, "triggers": reasons},
            )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="NOT_APPLICABLE",
            severity="HARD",
            reason="Food item is not identified as hygroscopic.",
        )


class FreshProduceRespirationRule(BaseRule):
    """R2.3 - Fresh produce respiration window emitting OTR interval constraint."""

    rule_id = "R2.3"
    name = "Fresh Produce Respiration Window"
    group = "PHYSICS"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        min_otr = 10000.0
        max_otr = 100000.0
        if self.config:
            cfg = self.config.get_rule_config("fresh_produce")
            min_otr = cfg.get("min_otr", 10000.0)
            max_otr = cfg.get("max_otr", 100000.0)

        is_fresh = False
        if context.is_fresh_produce:
            is_fresh = True
        elif food.food_category and "fruits" in food.food_category.lower() and "vegetables" in food.food_category.lower():
            is_fresh = True

        if is_fresh:
            constraint = Constraint(
                metric="otr_cm3_m2_day",
                operator="between",
                value=(min_otr, max_otr),
                source_rule=self.rule_id,
                reason=f"Fresh produce requires OTR respiration window between {min_otr} and {max_otr} cm3/m2/day.",
            )
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="PASS",
                severity="HARD",
                reason=f"Emitted OTR interval constraint ({min_otr} - {max_otr}) for fresh produce.",
                evidence={"constraint": constraint},
            )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="NOT_APPLICABLE",
            severity="HARD",
            reason="Food item is not fresh produce.",
        )


class AcidicLiquidRule(BaseRule):
    """R2.4 - Acidic liquid gate emitting acid resistance constraint."""

    rule_id = "R2.4"
    name = "Acidic Liquid Gate"
    group = "PHYSICS"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        ph_threshold = 4.5
        moisture_threshold = 60.0
        if self.config:
            cfg = self.config.get_rule_config("acidic_liquid")
            ph_threshold = cfg.get("ph_threshold", 4.5)
            moisture_threshold = cfg.get("moisture_pct_threshold", 60.0)

        if context.pH is not None and food.water_pct is not None:
            if context.pH < ph_threshold and food.water_pct > moisture_threshold:
                constraint = Constraint(
                    metric="acid_resistance",
                    operator="==",
                    value=True,
                    source_rule=self.rule_id,
                    reason=f"Acidic liquid (pH {context.pH} < {ph_threshold}, water {food.water_pct}% > {moisture_threshold}%) requires acid-resistant lining.",
                )
                return RuleResult(
                    rule_id=self.rule_id,
                    group=self.group,
                    status="PASS",
                    severity="HARD",
                    reason="Emitted acid-resistance constraint.",
                    evidence={"constraint": constraint},
                )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="NOT_APPLICABLE",
            severity="HARD",
            reason="Food is not classified as acidic liquid.",
        )


def get_all_physics_rules(config: Optional[Config] = None) -> List[BaseRule]:
    """Factory function returning instantiated physics rules."""
    return [
        HighFatOxidationRule(config),
        HygroscopicMoistureRule(config),
        FreshProduceRespirationRule(config),
        AcidicLiquidRule(config),
    ]
