"""Budapest parking-fee classification — the single source of truth for the app.

Rule (effective 2027-01-01):
  - BEV (fully electric) over 2000 kg  -> pays double
  - ICE or PHEV over 1800 kg           -> pays double
"over X" is strict (>). Exactly at the threshold is OK.
"""
from __future__ import annotations

from typing import Optional

THRESHOLD_BEV = 2000
THRESHOLD_COMBUSTION = 1800  # ICE and PHEV


def threshold_for(powertrain_type: Optional[str]) -> int:
    return THRESHOLD_BEV if powertrain_type == "BEV" else THRESHOLD_COMBUSTION


def classify(
    powertrain_type: Optional[str],
    weight: Optional[int],
    weight_min: Optional[int] = None,
    weight_max: Optional[int] = None,
) -> str:
    """Return 'ok' | 'double' | 'borderline' | 'unknown'."""
    t = threshold_for(powertrain_type)
    lo = weight_min if weight_min is not None else weight
    hi = weight_max if weight_max is not None else weight
    if lo is None and hi is None:
        return "unknown"
    if lo is not None and hi is not None:
        if lo > t:
            return "double"        # entire range above threshold
        if hi <= t:
            return "ok"            # entire range at/below threshold
        return "borderline"        # range straddles threshold (lo <= t < hi)
    rep = weight if weight is not None else (lo if lo is not None else hi)
    if rep is None:
        return "unknown"
    return "double" if rep > t else "ok"
