import os
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RAW_CSV = os.path.join(ROOT, "data", "raw", "packaging_materials", "materials_permeability.csv")
OUT_CSV = os.path.join(ROOT, "data", "processed", "materials_permeability_enriched.csv")

os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

df = pd.read_csv(RAW_CSV)

COMMERCIAL = {
    "polyethylene terephthalate", "ldpe", "hdpe", "polypropylene", "evoh",
    "paper", "paperboard", "greaseproof paper", "polylactic acid",
    "polyvinyl chloride", "polyvinylidene chloride",
}
BIOBASED = {
    "polylactic acid", "phbv", "starch", "corn starch", "oat starch",
    "chitosan", "methylcellulose", "microfibrillated cellulose",
    "cellophane", "paperboard", "paper", "greaseproof paper",
}
NANO_KEYWORDS = {"nammt", "ommt", "ag", "zno", "silica", "essential oil"}

bm = df["Base Material"].str.lower().fillna("")
sm = df["Secondary Material"].str.lower().fillna("")

df["is_commercial_fpm"]       = bm.isin(COMMERCIAL)
df["is_biobased_compostable"] = bm.isin(BIOBASED)
df["is_active_nanocomposite"] = sm.apply(lambda x: any(k in x for k in NANO_KEYWORDS))

df.to_csv(OUT_CSV, index=False)
print(f"Done - {len(df)} rows x {len(df.columns)} columns -> {OUT_CSV}")
