"""CLI recommendation runner script."""

import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rule_engine.engine import RuleEngine
from src.rule_engine.food import load_food_profiles_from_db
from src.rule_engine.materials import load_materials_from_db
from src.rule_engine.models import PackagingContext


def main():
    db_path = Path(__file__).parent.parent / "database" / "app.db"
    if not db_path.exists():
        print(f"Database file not found at {db_path}. Please initialize SQLite DB first.")
        return

    print("=== Rule Engine MVP Data Quality Report ===")
    foods = load_food_profiles_from_db(str(db_path))
    materials = load_materials_from_db(str(db_path))

    engine = RuleEngine.from_config()
    report = engine.data_quality_report(foods, materials)
    for k, v in report.items():
        print(f"  {k}: {v}")

    # Pick first high-fat or peanuts food item for demo
    sample_food = foods[0]
    for f in foods:
        if f.fat_pct and f.fat_pct > 15.0:
            sample_food = f
            break

    print(f"\n=== Running Recommendation for Food: '{sample_food.name}' (Code: {sample_food.code}, Fat: {sample_food.fat_pct}%, Category: {sample_food.food_category}) ===")
    context = PackagingContext()
    res = engine.recommend(sample_food, materials, context, top_k=5)

    print(f"\n--- FEASIBLE CANDIDATES ({len(res.candidates)}) ---")
    for r in res.candidates:
        print(f"  * [{r.material_id}] {r.material_name} | Score: {r.score} | Barrier Status: {r.barrier_status}")

    print(f"\n--- REQUIRES REVIEW ({len(res.requires_review_candidates)}) ---")
    for r in res.requires_review_candidates[:5]:
        print(f"  * [{r.material_id}] {r.material_name} | Regulatory Status: {r.regulatory_status} | Reason: {r.warnings[0] if r.warnings else 'Missing metadata'}")

    print(f"\n--- REJECTED CANDIDATES ({len(res.rejected_candidates)}) ---")
    for r in res.rejected_candidates[:5]:
        failed_rule = next((rr for rr in r.rule_results if rr.status == "FAIL"), None)
        reason_str = failed_rule.reason if failed_rule else "Physical constraint failure"
        print(f"  * [{r.material_id}] {r.material_name} | Status: {r.status} | Reason: {reason_str}")

    if res.candidates:
        top_cand = res.candidates[0]
        print(f"\n=== Detailed Audit Narrative for Top Candidate ({top_cand.material_name}) ===")
        print(top_cand.explanation)


if __name__ == "__main__":
    main()
