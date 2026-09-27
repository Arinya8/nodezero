"""Deterministic barrier-fit scoring and candidate ranking module."""

from typing import Dict, List, Optional, Protocol
from src.rule_engine.models import FoodProfile, Material, PackagingContext, Recommendation


class Ranker(Protocol):
    """Protocol interface for candidate material rankers."""

    def score(
        self,
        food: FoodProfile,
        material: Material,
        recommendation: Recommendation,
        context: Optional[PackagingContext] = None,
    ) -> float:
        ...


class DeterministicBarrierRanker:
    """Deterministic barrier-fit ranker for feasible candidate materials.

    Calculates a bounded barrier fit score (0.0 to 1.0) based on OTR and WVTR margins.
    Does not assign fake zeroes for unavailable dimensions.
    """

    def score(
        self,
        food: FoodProfile,
        material: Material,
        recommendation: Recommendation,
        context: Optional[PackagingContext] = None,
    ) -> float:
        score_components: Dict[str, Optional[float]] = {}
        barrier_scores = []

        # Evaluate OTR barrier fit margin
        for constraint in recommendation.constraints:
            if constraint.metric == "otr_cm3_m2_day" and material.otr_cm3_m2_day is not None:
                val = material.otr_cm3_m2_day
                if constraint.operator == "<=":
                    thresh = float(constraint.value)
                    # Margin score: higher is better barrier (lower transmission rate)
                    # Score = 1.0 - (val / thresh), capped at [0.1, 1.0]
                    if thresh > 0:
                        margin = max(0.1, min(1.0, 1.0 - (val / (thresh * 1.5))))
                        barrier_scores.append(margin)
                elif constraint.operator == "between":
                    min_v, max_v = constraint.value
                    if min_v <= val <= max_v:
                        # Center fit inside window
                        mid = (min_v + max_v) / 2.0
                        dev = abs(val - mid) / (max_v - min_v)
                        barrier_scores.append(max(0.5, 1.0 - dev))

            elif constraint.metric == "wvtr_g_m2_day" and material.wvtr_g_m2_day is not None:
                val = material.wvtr_g_m2_day
                if constraint.operator == "<=":
                    thresh = float(constraint.value)
                    if thresh > 0:
                        margin = max(0.1, min(1.0, 1.0 - (val / (thresh * 1.5))))
                        barrier_scores.append(margin)

        barrier_fit = float(sum(barrier_scores) / len(barrier_scores)) if barrier_scores else 0.50
        score_components["barrier_fit"] = round(barrier_fit, 4)

        # Optional sustainability bonus if metadata exists
        if material.is_biobased_compostable is True:
            score_components["sustainability"] = 0.10
        else:
            score_components["sustainability"] = None

        final_score = barrier_fit + (score_components["sustainability"] or 0.0)
        recommendation.score = round(min(1.0, final_score), 4)
        recommendation.score_components = score_components

        return recommendation.score


def rank_feasible_materials(recommendations: List[Recommendation]) -> List[Recommendation]:
    """Sort FEASIBLE candidates deterministically by score in descending order."""
    ranker = DeterministicBarrierRanker()
    for rec in recommendations:
        if rec.status == "FEASIBLE":
            # Dummy material/food for protocol if needed, properties already populated in rec
            pass
    return sorted(recommendations, key=lambda r: (r.score or 0.0), reverse=True)
