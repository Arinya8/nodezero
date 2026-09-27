import sqlite3
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "app.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
