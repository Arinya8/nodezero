"""Explanation and audit trail generation module."""

from typing import List
from src.rule_engine.models import FoodProfile, Material, PackagingContext, Recommendation, RuleResult


class TemplateExplanationProvider:
    """Deterministic, template-based explanation generator."""

    def generate_explanation(
        self,
        food: FoodProfile,
        material: Material,
        recommendation: Recommendation,
        context: PackagingContext,
    ) -> str:
        lines = []

        lines.append(f"Evaluation Summary for Material: {recommendation.material_name} (ID: {recommendation.material_id})")
        lines.append(f"Candidate Status: {recommendation.status}")
        if recommendation.score is not None:
            lines.append(f"Barrier Score: {recommendation.score}")

        lines.append("\nKey Factors & Evidence:")
        lines.append(f"- Food Item: '{food.name}' (Category: {food.food_category or 'Unmapped'})")

        if food.fat_pct is not None:
            lines.append(f"- Composition: Fat content = {food.fat_pct}%")
        if food.water_pct is not None:
            lines.append(f"- Composition: Water content = {food.water_pct}%")

        lines.append("\nEvaluated Constraints & Rules:")
        for res in recommendation.rule_results:
            if res.status in ("PASS", "FAIL", "UNKNOWN"):
                lines.append(f"  [{res.rule_id}]: {res.status} ({res.reason})")

        for c in recommendation.constraints:
            lines.append(f"  - Constraint [{c.source_rule}]: {c.reason}")

        if material.otr_cm3_m2_day is not None:
            lines.append(f"- Material OTR: {material.otr_cm3_m2_day} cm3/m2/day ({material.otr_status})")
        else:
            lines.append(f"- Material OTR: Missing / Unmeasured")

        if material.wvtr_g_m2_day is not None:
            lines.append(f"- Material WVTR: {material.wvtr_g_m2_day} g/m2/day ({material.wvtr_status})")
        else:
            lines.append(f"- Material WVTR: Missing / Unmeasured")

        if recommendation.warnings:
            lines.append("\nData Limitations & Warnings:")
            for w in recommendation.warnings:
                lines.append(f"  * {w}")

        if recommendation.assumptions:
            lines.append("\nEngine Assumptions:")
            for a in recommendation.assumptions:
                lines.append(f"  * {a}")

        return "\n".join(lines)


def attach_explanation(
    food: FoodProfile,
    material: Material,
    recommendation: Recommendation,
    context: PackagingContext,
) -> None:
    """Generate and attach explanation text to recommendation object."""
    provider = TemplateExplanationProvider()
    recommendation.explanation = provider.generate_explanation(food, material, recommendation, context)
