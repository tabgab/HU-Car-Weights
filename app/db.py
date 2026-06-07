"""Read-only SQLite access for the app."""
from __future__ import annotations

import sqlite3

from .config import DB_PATH


def get_conn() -> sqlite3.Connection:
    # read-only URI: the scraper owns writes; the app never mutates the DB.
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
