"""Central paths and constants for the carWeights scraper package."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXPORT_DIR = DATA_DIR / "exports"
CONFIG_DIR = ROOT / "config"

# The SQLite contract shared with the FastAPI app. Overridable for tests.
DB_PATH = Path(os.environ.get("CARWEIGHTS_DB", DATA_DIR / "cars.db"))

SCHEMA_PATH = Path(__file__).resolve().parent / "db" / "schema.sql"

USER_AGENT = "carWeights-research/0.1 (+info@omnest.com)"

# Budapest parking-fee threshold (kg). Effective 2027-01-01.
# Single rule: any car (BEV, ICE, PHEV) over 2000 kg pays double.
THRESHOLD_KG = 2000

for _d in (DATA_DIR, RAW_DIR, EXPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)
