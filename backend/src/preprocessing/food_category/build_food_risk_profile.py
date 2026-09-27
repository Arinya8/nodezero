import os
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RAW_CSV = os.path.join(ROOT, "data", "raw", "food_ctegory", "index.csv")
OUT_CSV = os.path.join(ROOT, "data", "processed", "food_risk_profile.csv")

os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

cols = ["code", "name", "scie", "lang", "grup", "regn", "tags",
        "water", "fatce", "protcnt", "choavldf", "fibtg", "orgac",
        "vitc", "polyph", "cartoid", "fasat", "fauns", "fapu", "starch", "fams"]

food_df = pd.read_csv(RAW_CSV, usecols=lambda c: c in cols)

food_df["water"] = pd.to_numeric(food_df["water"], errors="coerce")
food_df["moisture_class"] = pd.cut(
    food_df["water"],
    bins=[-float("inf"), 20, 50, 75, float("inf")],
    labels=["low", "medium", "high", "very_high"]
)

for col in ["fatce", "fapu", "fams", "vitc", "polyph", "cartoid"]:
    food_df[col] = pd.to_numeric(food_df[col], errors="coerce").fillna(0)

food_df["oxidation_risk_index"] = (
    food_df["fapu"]
    + 0.5 * food_df["fams"]
    + 0.2 * food_df["fatce"]
    - 0.01 * food_df["vitc"]
    - 0.01 * food_df["polyph"]
    - 0.01 * food_df["cartoid"]
)

food_df["moisture_barrier_requirement"] = np.select(
    [food_df["water"] >= 75, food_df["water"].between(40, 74.999), food_df["water"] < 40],
    ["high", "medium", "high_for_moisture_gain"],
    default="unknown"
)

food_df["food_risk_profile"] = (
    food_df["moisture_barrier_requirement"].astype(str)
    + "__"
    + pd.cut(
        food_df["oxidation_risk_index"],
        bins=[-np.inf, 0, 10, np.inf],
        labels=["low_oxidation", "medium_oxidation", "high_oxidation"]
    ).astype(str)
)

out_cols = ["code", "name", "scie", "lang", "grup", "regn", "tags",
            "water", "fatce", "protcnt", "choavldf", "fibtg", "orgac",
            "vitc", "polyph", "cartoid", "fasat", "fauns", "fapu", "starch",
            "moisture_class", "oxidation_risk_index",
            "moisture_barrier_requirement", "food_risk_profile"]

food_df[out_cols].to_csv(OUT_CSV, index=False)
print(f"Saved food_risk_profile.csv -> {OUT_CSV}")
