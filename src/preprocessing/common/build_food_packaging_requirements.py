import os
import sys
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from src.preprocessing.food_category.food_category_map import FOOD_CATEGORY_MAP

RISK_CSV = os.path.join(ROOT, "data", "processed", "food_risk_profile.csv")
REQS_CSV = os.path.join(ROOT, "data", "raw", "packaging_materials", "food_requirements.csv")
OUT_CSV  = os.path.join(ROOT, "data", "processed", "food_packaging_requirements.csv")

os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

food_df = pd.read_csv(RISK_CSV)
reqs_df = pd.read_csv(REQS_CSV)

food_df["packaging_category"] = food_df["grup"].map(FOOD_CATEGORY_MAP)

unmapped = food_df[food_df["packaging_category"].isna()]["grup"].unique()
if len(unmapped):
    print(f"Warning: {len(unmapped)} category/ies have no packaging mapping and will be excluded: {list(unmapped)}")

food_df = food_df.dropna(subset=["packaging_category"])

result = food_df.merge(
    reqs_df,
    left_on="packaging_category",
    right_on="Food_Category",
    how="left",
)

result = result.drop(columns=["Food_Category"])

result.to_csv(OUT_CSV, index=False)
print(f"Done - {len(result)} rows x {len(result.columns)} columns -> {OUT_CSV}")
