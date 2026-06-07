"""SQLite connection + schema bootstrap."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ..settings import DB_PATH, SCHEMA_PATH

SCHEMA_VERSION = 1


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")  # allow concurrent writers to retry
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Add cross-source columns to an existing weights table (idempotent)."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(weights)")}
    add = {
        "hu_weight_kg": "INTEGER",
        "hu_weight_url": "TEXT",
        "n_sources": "INTEGER NOT NULL DEFAULT 1",
        "sources_agree": "INTEGER",
        "primary_source": "TEXT",
    }
    for name, decl in add.items():
        if name not in cols:
            conn.execute(f"ALTER TABLE weights ADD COLUMN {name} {decl}")
    vcols = {r["name"] for r in conn.execute("PRAGMA table_info(variants)")}
    if "source" not in vcols:
        conn.execute("ALTER TABLE variants ADD COLUMN source TEXT NOT NULL DEFAULT 'cars-data'")
    hcols = {r["name"] for r in conn.execute("PRAGMA table_info(hu_catalog)")}
    for name, decl in {"display_name": "TEXT", "power_kw": "INTEGER", "model_year": "INTEGER"}.items():
        if name not in hcols:
            conn.execute(f"ALTER TABLE hu_catalog ADD COLUMN {name} {decl}")
    conn.commit()


def init_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Create the schema if needed (idempotent) and record the version."""
    conn = connect(db_path)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    _migrate(conn)
    row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
    if row is None or row["v"] is None:
        conn.execute("INSERT INTO schema_version(version) VALUES (?)", (SCHEMA_VERSION,))
    conn.commit()
    return conn
