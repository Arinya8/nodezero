from pathlib import Path

import nbformat as nbf

OUT = Path(__file__).resolve().parent


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text.strip() + "\n")


setup = r'''
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
try:
    from IPython.display import display
except ImportError:
    def display(obj):
        print(obj)

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.figsize"] = (10, 5)
plt.rcParams["axes.titlesize"] = 12

import sys

ROOT = Path.cwd()
if not (ROOT / "data").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

pd.set_option("display.max_rows", 80)
pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 140)


def unique_report(df, max_levels=40):
    rows = []
    for col in df.columns:
        s = df[col]
        n_unique = s.nunique(dropna=False)
        n_missing = int(s.isna().sum())
        rows.append({
            "column": col,
            "dtype": str(s.dtype),
            "n_unique": n_unique,
            "n_missing": n_missing,
            "pct_missing": round(100 * n_missing / len(df), 2),
        })
        print(f"\n=== {col}  ({s.dtype})  unique={n_unique}  missing={n_missing} ===")
        vc = s.value_counts(dropna=False)
        if n_unique <= max_levels:
            display(vc.to_frame("count"))
        else:
            print(f"High cardinality — top {max_levels}:")
            display(vc.head(max_levels).to_frame("count"))
    return pd.DataFrame(rows)


def iqr_outliers(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return s, np.nan, np.nan
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return s[(s < lo) | (s > hi)], lo, hi


def wvtr_to_g_m2_day(value, unit):
    if pd.isna(value) or pd.isna(unit):
        return np.nan
    u = str(unit).strip().lower().replace(" ", "")
    if u in {"g/m2day", "g/m2/day", "gm/m2day"}:
        return float(value)
    if u in {"g/m2s", "g/m2/s", "gm/m2s"}:
        return float(value) * 86400.0
    return np.nan


def otr_to_cm3_m2_day(value, unit):
    if pd.isna(value) or pd.isna(unit):
        return np.nan
    u = str(unit).strip().lower().replace(" ", "")
    if u in {"cm3/m2day", "cm3/m2/day"}:
        return float(value)
    if u in {"cm3/m2s", "cm3/m2/s"}:
        return float(value) * 86400.0
    return np.nan
'''

mat_cells = [
    md("# Materials EDA\n\nExplores packaging permeability rows: uniques, missingness, outliers, unit mix, and whether values can be compared to food OTR/WVTR requirement bands."),
    code(setup),
    code('''
mat_raw = pd.read_csv(ROOT / "data/raw/packaging_materials/materials_permeability.csv")
mat = pd.read_csv(ROOT / "data/processed/materials_permeability_enriched.csv")
reqs = pd.read_csv(ROOT / "data/raw/packaging_materials/food_requirements.csv")

print("raw", mat_raw.shape, "enriched", mat.shape)
display(mat.head())
display(mat.dtypes.to_frame("dtype"))
'''),
    md("## Unique values and counts\nEvery column: cardinality, missingness, and value counts (top 40 if high cardinality)."),
    code("col_summary = unique_report(mat)\ndisplay(col_summary)"),
    md("## Missing values\nWVTR and OTR are often measured on different samples, so missing one rate is expected. Missing **unit** should track missing **value**."),
    code('''
miss = mat.isna().mean().sort_values(ascending=False).to_frame("fraction_missing")
display(miss)
fig, ax = plt.subplots()
miss["fraction_missing"].plot(kind="barh", ax=ax)
ax.set_title("Fraction missing by column")
ax.set_xlabel("fraction")
plt.tight_layout()
plt.show()

print("WVTR present, unit missing:", int(mat["WVTR"].notna().eq(True).mul(mat["WVTR unit"].isna()).sum()))
print("OTR present, unit missing:", int(mat["OTR"].notna().eq(True).mul(mat["OTR unit"].isna()).sum()))
print("both WVTR and OTR present:", int(mat["WVTR"].notna() & mat["OTR"].notna()))
print("neither present:", int(mat["WVTR"].isna() & mat["OTR"].isna()))
'''),
    md("## Categorical distinctions\n`Type` has a likely typo (`indiviudal`). Flags come from `prepare_data.py`."),
    code('''
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
for ax, col in zip(axes, ["Type", "is_commercial_fpm", "is_biobased_compostable"]):
    mat[col].value_counts(dropna=False).plot(kind="bar", ax=ax)
    ax.set_title(col)
    ax.tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(figsize=(12, 5))
mat["Base Material"].value_counts().plot(kind="bar", ax=ax)
ax.set_title("Base Material counts")
ax.tick_params(axis="x", rotation=75)
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(figsize=(10, 4))
mat["Secondary Material"].value_counts().plot(kind="bar", ax=ax)
ax.set_title("Secondary Material counts")
ax.tick_params(axis="x", rotation=70)
plt.tight_layout()
plt.show()

flag_cols = ["is_commercial_fpm", "is_biobased_compostable", "is_active_nanocomposite"]
display(mat.groupby("Type")[flag_cols].mean().round(3))
display(pd.crosstab(mat["is_commercial_fpm"], mat["is_biobased_compostable"]))
'''),
    md("## Units — materials are **not** all in one unit\nFood requirement CSV has **no unit column**. Typical food-packaging literature uses WVTR in `g/m2/day` and OTR in `cm3/m2/day`. Materials still contain other units, so raw numbers must not be mixed."),
    code('''
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
mat["WVTR unit"].value_counts(dropna=False).plot(kind="bar", ax=axes[0], title="WVTR unit")
mat["OTR unit"].value_counts(dropna=False).plot(kind="bar", ax=axes[1], title="OTR unit")
for ax in axes:
    ax.tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.show()

print("Food requirement columns:", list(reqs.columns))
print("Food requirement table has unit fields:", any("unit" in c.lower() for c in reqs.columns))
display(reqs)
'''),
    md("## Raw numeric stats and IQR outliers\nExtreme max values are usually **unit artifacts** (per-second or permeability coefficients), not extreme films."),
    code('''
display(mat[["WVTR", "OTR"]].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]))

for col in ["WVTR", "OTR"]:
    outs, lo, hi = iqr_outliers(mat[col])
    print(f"{col}: IQR fences [{lo:.4g}, {hi:.4g}]  n_outliers={len(outs)}  min={outs.min() if len(outs) else '—'}  max={outs.max() if len(outs) else '—'}")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for ax, col in zip(axes, ["WVTR", "OTR"]):
    s = pd.to_numeric(mat[col], errors="coerce").dropna()
    ax.boxplot(s, vert=True)
    ax.set_yscale("log")
    ax.set_title(f"{col} (log, mixed units)")
plt.tight_layout()
plt.show()

print("\\nWVTR by unit:")
display(mat.groupby("WVTR unit", dropna=False)["WVTR"].describe())
print("OTR by unit:")
display(mat.groupby("OTR unit", dropna=False)["OTR"].describe())
'''),
    md("## Convert comparable rows to food-like units\n- `g/m2s` → `g/m2day` by ×86400\n- `cm3/m2s` → `cm3/m2day` by ×86400\n- `cm3/m2Pas`, `cm3cm/m2s`, `cm3cm/m2Pas` need thickness/pressure and are **not** converted here"),
    code('''
mat["WVTR_g_m2_day"] = [wvtr_to_g_m2_day(v, u) for v, u in zip(mat["WVTR"], mat["WVTR unit"])]
mat["OTR_cm3_m2_day"] = [otr_to_cm3_m2_day(v, u) for v, u in zip(mat["OTR"], mat["OTR unit"])]
mat["wvtr_comparable"] = mat["WVTR_g_m2_day"].notna()
mat["otr_comparable"] = mat["OTR_cm3_m2_day"].notna()

print("WVTR convertible to g/m2day:", int(mat["wvtr_comparable"].sum()), "/", mat["WVTR"].notna().sum(), "measured")
print("OTR convertible to cm3/m2day:", int(mat["otr_comparable"].sum()), "/", mat["OTR"].notna().sum(), "measured")
print("OTR left incomparable (permeability-style units):")
display(mat.loc[mat["OTR"].notna() & ~mat["otr_comparable"], "OTR unit"].value_counts())

display(mat.loc[mat["wvtr_comparable"], ["WVTR_g_m2_day"]].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))
display(mat.loc[mat["otr_comparable"], ["OTR_cm3_m2_day"]].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))

for col in ["WVTR_g_m2_day", "OTR_cm3_m2_day"]:
    outs, lo, hi = iqr_outliers(mat[col])
    print(f"{col}: IQR fences [{lo:.4g}, {hi:.4g}]  n_outliers={len(outs)}")
'''),
    md("## Bins and distributions (converted units)"),
    code('''
wvtr_bins = [0, 1, 10, 100, 1000, 1e4, 1e5, np.inf]
otr_bins = [0, 1, 10, 100, 1e3, 1e4, 1e6, np.inf]
wvtr_labels = ["<1", "1–10", "10–100", "100–1e3", "1e3–1e4", "1e4–1e5", ">1e5"]
otr_labels = ["<1", "1–10", "10–100", "100–1e3", "1e3–1e4", "1e4–1e6", ">1e6"]

mat["wvtr_bin"] = pd.cut(mat["WVTR_g_m2_day"], bins=wvtr_bins, labels=wvtr_labels, right=False)
mat["otr_bin"] = pd.cut(mat["OTR_cm3_m2_day"], bins=otr_bins, labels=otr_labels, right=False)
display(mat["wvtr_bin"].value_counts().sort_index().to_frame("count"))
display(mat["otr_bin"].value_counts().sort_index().to_frame("count"))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.histplot(np.log10(mat["WVTR_g_m2_day"].dropna().clip(lower=1e-12)), bins=30, ax=axes[0])
axes[0].set_title("log10 WVTR (g/m2day)")
sns.histplot(np.log10(mat["OTR_cm3_m2_day"].dropna().clip(lower=1e-12)), bins=30, ax=axes[1])
axes[1].set_title("log10 OTR (cm3/m2day)")
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.boxplot(data=mat.dropna(subset=["WVTR_g_m2_day"]), x="Type", y="WVTR_g_m2_day", ax=axes[0])
axes[0].set_yscale("log")
axes[0].tick_params(axis="x", rotation=30)
axes[0].set_title("WVTR by Type (converted)")
sns.boxplot(data=mat.dropna(subset=["OTR_cm3_m2_day"]), x="Type", y="OTR_cm3_m2_day", ax=axes[1])
axes[1].set_yscale("log")
axes[1].tick_params(axis="x", rotation=30)
axes[1].set_title("OTR by Type (converted)")
plt.tight_layout()
plt.show()
'''),
    md("## Alignment with food requirement bands\nAssuming food `Min/Max_WVTR` are `g/m2day` and `Min/Max_OTR` are `cm3/m2day` (not stated in the CSV)."),
    code('''
pair = mat.dropna(subset=["WVTR_g_m2_day", "OTR_cm3_m2_day"])
fig, ax = plt.subplots(figsize=(9, 7))
if len(pair):
    ax.scatter(pair["OTR_cm3_m2_day"], pair["WVTR_g_m2_day"], s=18, alpha=0.6, label="materials (both rates)")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("OTR cm3/m2day")
ax.set_ylabel("WVTR g/m2day")

colors = sns.color_palette("tab10", n_colors=len(reqs))
for (i, r), color in zip(reqs.iterrows(), colors):
    x0, x1 = r["Min_OTR"], r["Max_OTR"]
    y0, y1 = r["Min_WVTR"], r["Max_WVTR"]
    ax.add_patch(plt.Rectangle((x0, y0), max(x1 - x0, x0 * 1e-6), max(y1 - y0, y0 * 1e-6),
                               fill=False, edgecolor=color, linewidth=1.4, label=r["Food_Category"]))
ax.set_title("Materials vs food OTR/WVTR windows")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
plt.tight_layout()
plt.show()

rows = []
for _, r in reqs.iterrows():
    w = mat["WVTR_g_m2_day"].between(r["Min_WVTR"], r["Max_WVTR"])
    o = mat["OTR_cm3_m2_day"].between(r["Min_OTR"], r["Max_OTR"])
    rows.append({
        "Food_Category": r["Food_Category"],
        "n_mat_WVTR_in_band": int(w.sum()),
        "n_mat_OTR_in_band": int(o.sum()),
        "n_mat_both_in_band": int((w & o).sum()),
        "Min_OTR": r["Min_OTR"], "Max_OTR": r["Max_OTR"],
        "Min_WVTR": r["Min_WVTR"], "Max_WVTR": r["Max_WVTR"],
    })
cover = pd.DataFrame(rows)
display(cover)

print("Materials with comparable WVTR:", int(mat["wvtr_comparable"].sum()))
print("Materials with comparable OTR:", int(mat["otr_comparable"].sum()))
print("Spearman WVTR vs OTR (converted, paired):",
      pair[["WVTR_g_m2_day", "OTR_cm3_m2_day"]].corr(method="spearman").iloc[0, 1] if len(pair) > 2 else "n/a")
'''),
    md("## Findings to carry forward\n- Do not compare raw `WVTR`/`OTR` across rows until units are unified.\n- Food requirement units are **assumed**, not stored.\n- Permeability-style OTR units cannot join food bands without thickness.\n- IQR outliers on mixed-unit data are not physical outliers."),
]

food_cells = [
    md("# Food category EDA\n\nExplores IFCT-derived food risk rows, packaging-group mapping, requirement bands, and whether those bands share units with the materials table."),
    code(setup),
    code('''
foods = pd.read_csv(ROOT / "data/processed/food_risk_profile.csv")
joined = pd.read_csv(ROOT / "data/processed/food_packaging_requirements.csv")
reqs = pd.read_csv(ROOT / "data/raw/packaging_materials/food_requirements.csv")
mat = pd.read_csv(ROOT / "data/processed/materials_permeability_enriched.csv")
index = pd.read_csv(ROOT / "data/raw/food_ctegory/index.csv", nrows=5)

from src.preprocessing.food_category.food_category_map import FOOD_CATEGORY_MAP

print("foods", foods.shape, "joined", joined.shape, "reqs", reqs.shape)
display(foods.head(3))
display(foods.dtypes.to_frame("dtype"))
print("index.csv sample columns (first 12):", list(index.columns[:12]))
print("fams in food_risk_profile.csv?", "fams" in foods.columns)
print("fams is used in oxidation_risk_index but dropped from the saved food table.")
'''),
    md("## Unique values and counts"),
    code("food_col_summary = unique_report(foods, max_levels=25)\ndisplay(food_col_summary)"),
    md("## Category, moisture, and risk-profile mix"),
    code('''
fig, ax = plt.subplots(figsize=(11, 5))
foods["grup"].value_counts().plot(kind="barh", ax=ax)
ax.set_title("Foods per IFCT grup")
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
foods["moisture_class"].value_counts().plot(kind="bar", ax=axes[0], title="moisture_class")
foods["moisture_barrier_requirement"].value_counts().plot(kind="bar", ax=axes[1], title="moisture_barrier_requirement")
foods["food_risk_profile"].value_counts().plot(kind="bar", ax=axes[2], title="food_risk_profile")
for ax in axes:
    ax.tick_params(axis="x", rotation=55)
plt.tight_layout()
plt.show()

display(pd.crosstab(foods["grup"], foods["moisture_class"]))
display(pd.crosstab(foods["moisture_class"], foods["food_risk_profile"]))
display(foods["tags"].value_counts().to_frame("count"))
'''),
    md("## Composition statistics and outliers\nIFCT nutrient amounts are per 100 g food (typical IFCT convention). That is **not** the same physical quantity as material WVTR/OTR."),
    code('''
num_cols = [c for c in foods.columns if foods[c].dtype != "object"]
display(foods[num_cols].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T)

outlier_rows = []
for col in num_cols:
    outs, lo, hi = iqr_outliers(foods[col])
    outlier_rows.append({
        "column": col, "n_outliers": len(outs),
        "fence_lo": lo, "fence_hi": hi,
        "out_min": outs.min() if len(outs) else np.nan,
        "out_max": outs.max() if len(outs) else np.nan,
    })
display(pd.DataFrame(outlier_rows).sort_values("n_outliers", ascending=False))

fig, axes = plt.subplots(2, 3, figsize=(14, 8))
for ax, col in zip(axes.ravel(), ["water", "fatce", "fapu", "vitc", "polyph", "oxidation_risk_index"]):
    sns.histplot(foods[col].dropna(), bins=40, ax=ax)
    ax.set_title(col)
plt.tight_layout()
plt.show()
'''),
    md("## Moisture and oxidation bins vs cut definitions\n- moisture_class: water ≤20 low, ≤50 medium, ≤75 high, else very_high\n- oxidation bands on the index: ≤0 low, ≤10 medium, else high"),
    code('''
fig, ax = plt.subplots()
sns.histplot(foods["water"].dropna(), bins=40, ax=ax)
for x, lab in [(20, "20"), (50, "50"), (75, "75")]:
    ax.axvline(x, color="crimson", ls="--", lw=1)
    ax.text(x, ax.get_ylim()[1] * 0.9, lab, color="crimson")
ax.set_title("Water with moisture_class cuts")
plt.tight_layout()
plt.show()

fig, ax = plt.subplots()
sns.histplot(foods["oxidation_risk_index"].dropna(), bins=40, ax=ax)
ax.axvline(0, color="crimson", ls="--")
ax.axvline(10, color="crimson", ls="--")
ax.set_title("oxidation_risk_index with oxidation-band cuts")
plt.tight_layout()
plt.show()

display(foods.groupby("moisture_class")["water"].describe())
display(foods.groupby("food_risk_profile")["oxidation_risk_index"].describe())

fig, ax = plt.subplots(figsize=(8, 5))
sns.scatterplot(
    data=foods, x="water", y="oxidation_risk_index",
    hue="moisture_barrier_requirement", alpha=0.55, s=22, ax=ax,
)
ax.set_title("Water vs oxidation_risk_index")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.show()
'''),
    md("## Mapping IFCT `grup` → packaging requirement category"),
    code('''
map_df = pd.DataFrame(FOOD_CATEGORY_MAP.items(), columns=["grup", "packaging_category"])
counts = foods["grup"].value_counts().rename("n_foods")
map_df = map_df.merge(counts, left_on="grup", right_index=True, how="left")
map_df["mapped"] = map_df["packaging_category"].notna()
display(map_df.sort_values("n_foods", ascending=False))

print("foods dropped as unmapped:", int(foods["grup"].map(FOOD_CATEGORY_MAP).isna().sum()))
print("joined rows vs food rows:", len(joined), "vs", len(foods))

fig, ax = plt.subplots(figsize=(10, 5))
joined["packaging_category"].value_counts().plot(kind="barh", ax=ax)
ax.set_title("Foods per packaging_category after join")
plt.tight_layout()
plt.show()

display(joined.groupby("packaging_category")[["Min_OTR", "Max_OTR", "Min_WVTR", "Max_WVTR"]].first())
'''),
    md("## Food requirement bands (log scale)\nThese ranges are the target windows materials should fall into. Units are not stored on this table."),
    code('''
fig, ax = plt.subplots(figsize=(9, 6))
ys = np.arange(len(reqs))
ax.hlines(ys, reqs["Min_OTR"], reqs["Max_OTR"], color="C0", lw=6, label="OTR window")
ax.set_yticks(ys)
ax.set_yticklabels(reqs["Food_Category"])
ax.set_xscale("log")
ax.set_xlabel("OTR (assumed cm3/m2day)")
ax.set_title("Food Min–Max OTR")
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(figsize=(9, 6))
ax.hlines(ys, reqs["Min_WVTR"], reqs["Max_WVTR"], color="C1", lw=6)
ax.set_yticks(ys)
ax.set_yticklabels(reqs["Food_Category"])
ax.set_xscale("log")
ax.set_xlabel("WVTR (assumed g/m2day)")
ax.set_title("Food Min–Max WVTR")
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(reqs["Min_OTR"], reqs["Min_WVTR"], label="min corner")
ax.scatter(reqs["Max_OTR"], reqs["Max_WVTR"], label="max corner")
for _, r in reqs.iterrows():
    ax.plot([r["Min_OTR"], r["Max_OTR"]], [r["Min_WVTR"], r["Max_WVTR"]], alpha=0.4)
    ax.text(r["Max_OTR"], r["Max_WVTR"], r["Food_Category"], fontsize=7)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("OTR")
ax.set_ylabel("WVTR")
ax.set_title("Requirement window corners")
ax.legend()
plt.tight_layout()
plt.show()
'''),
    md("## Do food windows and materials share units?\nMaterials: mixed (`g/m2day`, `g/m2s`, `cm3/m2day`, `cm3/m2s`, plus permeability units).\nFoods: nutrient %/100 g plus unitless requirement numbers.\nAlignment is only possible after converting materials onto `g/m2day` and `cm3/m2day`."),
    code('''
mat["WVTR_g_m2_day"] = [wvtr_to_g_m2_day(v, u) for v, u in zip(mat["WVTR"], mat["WVTR unit"])]
mat["OTR_cm3_m2_day"] = [otr_to_cm3_m2_day(v, u) for v, u in zip(mat["OTR"], mat["OTR unit"])]

unit_table = pd.DataFrame({
    "dataset": ["materials WVTR", "materials OTR", "food Min/Max_WVTR", "food Min/Max_OTR", "food composition"],
    "stated_units": [
        ", ".join(sorted(mat["WVTR unit"].dropna().unique().astype(str))),
        ", ".join(sorted(mat["OTR unit"].dropna().unique().astype(str))),
        "not provided (assumed g/m2day)",
        "not provided (assumed cm3/m2day)",
        "IFCT per 100 g food (not barrier units)",
    ],
    "n_values": [
        int(mat["WVTR"].notna().sum()),
        int(mat["OTR"].notna().sum()),
        len(reqs),
        len(reqs),
        len(foods),
    ],
})
display(unit_table)

cover = []
wv = mat["WVTR_g_m2_day"]
ot = mat["OTR_cm3_m2_day"]
for _, r in reqs.iterrows():
    n_foods = int((joined["packaging_category"] == r["Food_Category"]).sum())
    cover.append({
        "Food_Category": r["Food_Category"],
        "n_foods": n_foods,
        "n_materials_WVTR_in_band": int(wv.between(r["Min_WVTR"], r["Max_WVTR"]).sum()),
        "n_materials_OTR_in_band": int(ot.between(r["Min_OTR"], r["Max_OTR"]).sum()),
        "n_materials_both_in_band": int(
            (wv.between(r["Min_WVTR"], r["Max_WVTR"]) & ot.between(r["Min_OTR"], r["Max_OTR"])).sum()
        ),
    })
display(pd.DataFrame(cover).sort_values("n_foods", ascending=False))

fig, ax = plt.subplots(figsize=(9, 5))
sns.boxplot(data=joined, x="packaging_category", y="oxidation_risk_index", ax=ax)
ax.tick_params(axis="x", rotation=55)
ax.set_title("oxidation_risk_index by packaging_category")
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(figsize=(9, 5))
sns.boxplot(data=joined, x="packaging_category", y="water", ax=ax)
ax.tick_params(axis="x", rotation=55)
ax.set_title("water by packaging_category")
plt.tight_layout()
plt.show()
'''),
    md("## Findings\n- Food composition and material permeability are different quantities; only OTR/WVTR **requirement bands** can be compared to materials.\n- Those bands have no unit field; treat them as `cm3/m2day` and `g/m2day` until documented otherwise.\n- Most foods sit in `very_high` moisture / `high__medium_oxidation`.\n- `Miscellaneous Foods` (2 rows) never join a packaging category."),
]


def write_nb(name, cells):
    nb = nbf.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    nb.cells = cells
    path = OUT / name
    nbf.write(nb, path)
    print("wrote", path)


write_nb("eda_materials.ipynb", mat_cells)
write_nb("eda_food_categories.ipynb", food_cells)
