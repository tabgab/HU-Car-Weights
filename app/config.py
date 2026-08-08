"""App configuration: DB path + thresholds."""
from __future__ import annotations

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("CARWEIGHTS_DB", str(_ROOT / "data" / "cars.db"))

# threshold re-exported from fees for the API /thresholds payload
from .fees import THRESHOLD_KG  # noqa: E402

# One rule for all powertrains; keyed shape kept for frontend compatibility.
THRESHOLDS = {"BEV": THRESHOLD_KG, "ICE": THRESHOLD_KG, "PHEV": THRESHOLD_KG}
