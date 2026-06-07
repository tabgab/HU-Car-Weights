"""App configuration: DB path + thresholds."""
from __future__ import annotations

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("CARWEIGHTS_DB", str(_ROOT / "data" / "cars.db"))

# thresholds re-exported from fees for the API /thresholds payload
from .fees import THRESHOLD_BEV, THRESHOLD_COMBUSTION  # noqa: E402

THRESHOLDS = {"BEV": THRESHOLD_BEV, "ICE": THRESHOLD_COMBUSTION, "PHEV": THRESHOLD_COMBUSTION}
