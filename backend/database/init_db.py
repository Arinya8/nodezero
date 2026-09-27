import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.database.connection import DB_PATH, get_connection
from src.database.models import SCHEMA_SQL


def init_db() -> Path:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(material)")}
        additions = {
            "is_recycled_plastic": "INTEGER",
            "is_recycled_plastic_fcm_rpet": "INTEGER",
            "has_rpet_decontamination_proof": "INTEGER",
            "compostable_is17088": "INTEGER",
            "thickness_um": "REAL",
            "has_migration_test_data": "INTEGER",
            "has_ink_safety_cert": "INTEGER",
            "acid_resistance": "INTEGER",
        }
        for name, sql_type in additions.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE material ADD COLUMN {name} {sql_type}")
        conn.commit()
    finally:
        conn.close()
    print(f"Initialized {DB_PATH}")
    return DB_PATH


if __name__ == "__main__":
    init_db()
