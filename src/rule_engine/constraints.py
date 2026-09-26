"""Constraint evaluation engine."""

from typing import List, Tuple
from src.rule_engine.models import Constraint, Material


class ConstraintEvaluator:
    """Evaluates physical and barrier constraints against candidate materials."""

    @staticmethod
    def evaluate_constraint(constraint: Constraint, material: Material) -> Tuple[str, str]:
        """Evaluate a single constraint against a material.

        Returns:
            Tuple[status, reason] where status is 'PASS', 'FAIL', or 'UNKNOWN'.
        """
        metric = constraint.metric
        op = constraint.operator
        val = constraint.value

        # Retrieve material property
        mat_val = None
        if metric == "otr_cm3_m2_day":
            mat_val = material.otr_cm3_m2_day
            status_attr = material.otr_status
        elif metric == "wvtr_g_m2_day":
            mat_val = material.wvtr_g_m2_day
            status_attr = material.wvtr_status
        elif metric == "acid_resistance":
            mat_val = material.acid_resistance
            status_attr = "CANONICAL" if mat_val is not None else "MISSING"
        else:
            # Fallback for flags / raw attributes
            mat_val = getattr(material, metric, None)
            if mat_val is None:
                mat_val = material.raw_attributes.get(metric)
            status_attr = "CANONICAL" if mat_val is not None else "MISSING"

        # Check missing or incomparable data
        if mat_val is None or status_attr in ("MISSING", "INCOMPARABLE", "INVALID"):
            return "UNKNOWN", f"Metric '{metric}' is unavailable or incomparable ({status_attr}) for material {material.material_id}."

        # Operator evaluation
        if op == "<=":
            if mat_val <= float(val):
                return "PASS", f"{metric} ({mat_val}) <= required threshold ({val})."
            return "FAIL", f"{metric} ({mat_val}) exceeds required maximum threshold ({val})."

        if op == ">=":
            if mat_val >= float(val):
                return "PASS", f"{metric} ({mat_val}) >= required threshold ({val})."
            return "FAIL", f"{metric} ({mat_val}) is below required minimum threshold ({val})."

        if op == "between":
            min_val, max_val = val
            if min_val <= mat_val <= max_val:
                return "PASS", f"{metric} ({mat_val}) is within required window [{min_val}, {max_val}]."
            return "FAIL", f"{metric} ({mat_val}) is outside required respiration window [{min_val}, {max_val}]."

        return "UNKNOWN", f"Unsupported constraint operator '{op}'."

    @classmethod
    def evaluate_all(cls, constraints: List[Constraint], material: Material) -> Tuple[str, List[Tuple[Constraint, str, str]]]:
        """Evaluate list of constraints against a material.

        Returns:
            Tuple[overall_status, List[(constraint, status, reason)]]
            where overall_status is 'PASS', 'FAIL', or 'UNKNOWN'
        """
        if not constraints:
            return "PASS", []

        results = []
        has_fail = False
        has_unknown = False

        for c in constraints:
            status, reason = cls.evaluate_constraint(c, material)
            results.append((c, status, reason))
            if status == "FAIL":
                has_fail = True
            elif status == "UNKNOWN":
                has_unknown = True

        if has_fail:
            return "FAIL", results
        if has_unknown:
            return "UNKNOWN", results
        return "PASS", results
