"""Group 1 Regulatory Rules (R1.1 - R1.6)."""

from typing import List, Optional, Any, Dict
import re
from src.rule_engine.config import Config
from src.rule_engine.models import FoodProfile, Material, PackagingContext, RuleResult
from src.rule_engine.normalization import canonicalize_material_name
from src.rule_engine.rules.base import BaseRule


class PanMasalaProhibitionRule(BaseRule):
    """R1.1 - Pan Masala material prohibition rule."""

    rule_id = "R1.1"
    name = "Pan Masala Material Prohibition"
    group = "REGULATORY"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        is_pan_masala = False
        if food.food_category and "pan masala" in food.food_category.lower():
            is_pan_masala = True
        elif food.name and "pan masala" in food.name.lower():
            is_pan_masala = True

        if not is_pan_masala:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="NOT_APPLICABLE",
                severity="HARD",
                reason="Food item is not Pan Masala.",
            )

        mat_text = " ".join([
            material.base_material or "",
            material.structure_type or "",
            material.secondary_material or "",
        ]).lower()

        prohibited = [
            "polyethylene", "polypropylene", "polyester", "pvc",
            "synthetic polymer", "copolymer", "laminate",
            "aluminium foil", "metallised", "metallized", "pe", "pp", "pet", "bopp",
        ]
        if self.config:
            pan_cfg = self.config.get_rule_config("pan_masala")
            if pan_cfg.get("prohibited_materials"):
                prohibited = pan_cfg.get("prohibited_materials")

        for p in prohibited:
            token_pattern = r"(?<![a-z0-9])" + re.escape(p.lower()) + r"(?![a-z0-9])"
            if re.search(token_pattern, mat_text):
                return RuleResult(
                    rule_id=self.rule_id,
                    group=self.group,
                    status="FAIL",
                    severity="HARD",
                    reason=f"Prohibited material component '{p}' detected for Pan Masala.",
                    evidence={"detected_prohibited_component": p, "material_text": mat_text},
                )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="PASS",
            severity="HARD",
            reason="Material complies with Pan Masala packaging restrictions.",
        )


class RecycledPlasticRule(BaseRule):
    """R1.2 - Non-approved recycled plastics gate."""

    rule_id = "R1.2"
    name = "Non-approved Recycled Plastics Gate"
    group = "REGULATORY"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        if material.is_recycled_plastic is True:
            if material.is_recycled_plastic_fcm_rpet is True:
                return RuleResult(
                    rule_id=self.rule_id,
                    group=self.group,
                    status="PASS",
                    severity="HARD",
                    reason="Recycled plastic is approved FCM rPET.",
                )
            elif material.is_recycled_plastic_fcm_rpet is False:
                return RuleResult(
                    rule_id=self.rule_id,
                    group=self.group,
                    status="FAIL",
                    severity="HARD",
                    reason="Recycled plastic is not approved for food contact application.",
                )
            else:
                return RuleResult(
                    rule_id=self.rule_id,
                    group=self.group,
                    status="UNKNOWN",
                    severity="HARD",
                    reason="Recycled plastic FCM approval status is missing from dataset.",
                )

        if material.is_recycled_plastic is None:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="UNKNOWN",
                severity="HARD",
                reason="Recycled plastic classification evidence missing from dataset.",
            )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="PASS",
            severity="HARD",
            reason="Material is not a recycled plastic.",
        )


class RPETDecontaminationRule(BaseRule):
    """R1.3 - rPET decontamination proof gate."""

    rule_id = "R1.3"
    name = "rPET Decontamination Proof Gate"
    group = "REGULATORY"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        mat_text = " ".join([material.base_material or "", material.structure_type or ""]).lower()
        is_rpet = "rpet" in mat_text or "recycled pet" in mat_text

        if not is_rpet:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="NOT_APPLICABLE",
                severity="HARD",
                reason="Material does not contain rPET.",
            )

        if material.has_rpet_decontamination_proof is True:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="PASS",
                severity="HARD",
                reason="rPET decontamination proof verified.",
            )
        elif material.has_rpet_decontamination_proof is False:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="FAIL",
                severity="HARD",
                reason="rPET lacks mandatory decontamination proof.",
            )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="UNKNOWN",
            severity="HARD",
            reason="rPET decontamination process proof is missing from material metadata.",
        )


class ThicknessFloorRule(BaseRule):
    """R1.4 - Minimum thickness floor rule."""

    rule_id = "R1.4"
    name = "Thickness Floor Gate"
    group = "REGULATORY"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        format_name = (context.packaging_format or "").strip().lower()
        restricted_formats = {"carry bag", "flexible sheet"}

        if format_name not in restricted_formats:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="NOT_APPLICABLE",
                severity="HARD",
                reason=f"Packaging format '{context.packaging_format}' does not trigger mandatory thickness floor.",
            )

        thickness = context.thickness_um or material.thickness_um
        if thickness is None:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="UNKNOWN",
                severity="HARD",
                reason="Thickness metadata is missing for packaging format subject to regulatory floor.",
            )

        if thickness < 50.0 and not material.compostable_is17088:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="FAIL",
                severity="HARD",
                reason=f"Thickness ({thickness} um) is below regulatory threshold (50 um) and material is not certified compostable.",
                evidence={"thickness_um": thickness, "min_required_um": 50.0},
            )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="PASS",
            severity="HARD",
            reason="Material meets or exceeds thickness floor requirements.",
        )


class MigrationLimitsRule(BaseRule):
    """R1.5 - Overall and Specific Migration Limits (OML/SML)."""

    rule_id = "R1.5"
    name = "Migration Limits Compliance"
    group = "REGULATORY"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        if material.has_migration_test_data is True:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="PASS",
                severity="HARD",
                reason="Migration test evidence available and compliant.",
            )
        elif material.has_migration_test_data is False:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="FAIL",
                severity="HARD",
                reason="Migration testing failed or non-compliant.",
            )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="UNKNOWN",
            severity="HARD",
            reason="Required migration test evidence is absent from current material dataset.",
        )


class PrintingInkSafetyRule(BaseRule):
    """R1.6 - Printing ink safety gate."""

    rule_id = "R1.6"
    name = "Printing Ink Safety Gate"
    group = "REGULATORY"

    def evaluate(self, food: FoodProfile, material: Material, context: PackagingContext) -> RuleResult:
        if not context.is_printed:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="NOT_APPLICABLE",
                severity="HARD",
                reason="Packaging is not printed.",
            )

        if material.has_ink_safety_cert is True:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="PASS",
                severity="HARD",
                reason="Printing ink safety certification verified.",
            )
        elif material.has_ink_safety_cert is False:
            return RuleResult(
                rule_id=self.rule_id,
                group=self.group,
                status="FAIL",
                severity="HARD",
                reason="Printing ink safety certification missing or failed.",
            )

        return RuleResult(
            rule_id=self.rule_id,
            group=self.group,
            status="UNKNOWN",
            severity="HARD",
            reason="Printing ink safety certification status is absent.",
        )


def get_all_regulatory_rules(config: Optional[Config] = None) -> List[BaseRule]:
    """Factory function returning instantiated regulatory rules."""
    return [
        PanMasalaProhibitionRule(config),
        RecycledPlasticRule(config),
        RPETDecontaminationRule(config),
        ThicknessFloorRule(config),
        MigrationLimitsRule(config),
        PrintingInkSafetyRule(config),
    ]
