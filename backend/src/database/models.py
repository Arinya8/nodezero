SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS packaging_requirement (
    food_category TEXT PRIMARY KEY,
    min_otr REAL,
    max_otr REAL,
    min_wvtr REAL,
    max_wvtr REAL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS food_item (
    code TEXT PRIMARY KEY,
    name TEXT,
    scie TEXT,
    lang TEXT,
    grup TEXT,
    regn INTEGER,
    tags TEXT,
    water REAL,
    fatce REAL,
    protcnt REAL,
    choavldf REAL,
    fibtg REAL,
    orgac REAL,
    vitc REAL,
    polyph REAL,
    cartoid REAL,
    fasat REAL,
    fauns REAL,
    fapu REAL,
    starch REAL,
    moisture_class TEXT,
    oxidation_risk_index REAL,
    moisture_barrier_requirement TEXT,
    food_risk_profile TEXT
);

CREATE TABLE IF NOT EXISTS food_group_map (
    grup TEXT PRIMARY KEY,
    packaging_category TEXT,
    FOREIGN KEY (packaging_category) REFERENCES packaging_requirement(food_category)
);

CREATE TABLE IF NOT EXISTS material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_material TEXT,
    type TEXT,
    secondary_material TEXT,
    wvtr REAL,
    otr REAL,
    wvtr_unit TEXT,
    otr_unit TEXT,
    is_commercial_fpm INTEGER,
    is_biobased_compostable INTEGER,
    is_active_nanocomposite INTEGER,
    is_recycled_plastic INTEGER,
    is_recycled_plastic_fcm_rpet INTEGER,
    has_rpet_decontamination_proof INTEGER,
    compostable_is17088 INTEGER,
    thickness_um REAL,
    has_migration_test_data INTEGER,
    has_ink_safety_cert INTEGER,
    acid_resistance INTEGER
);

CREATE INDEX IF NOT EXISTS idx_food_item_grup ON food_item(grup);
CREATE INDEX IF NOT EXISTS idx_material_base ON material(base_material);

CREATE VIEW IF NOT EXISTS food_packaging_requirement AS
SELECT
    f.code,
    f.name,
    f.scie,
    f.lang,
    f.grup,
    f.regn,
    f.tags,
    f.water,
    f.fatce,
    f.protcnt,
    f.choavldf,
    f.fibtg,
    f.orgac,
    f.vitc,
    f.polyph,
    f.cartoid,
    f.fasat,
    f.fauns,
    f.fapu,
    f.starch,
    f.moisture_class,
    f.oxidation_risk_index,
    f.moisture_barrier_requirement,
    f.food_risk_profile,
    m.packaging_category,
    p.min_otr,
    p.max_otr,
    p.min_wvtr,
    p.max_wvtr,
    p.description
FROM food_item f
JOIN food_group_map m ON f.grup = m.grup
JOIN packaging_requirement p ON m.packaging_category = p.food_category
WHERE m.packaging_category IS NOT NULL;
"""
