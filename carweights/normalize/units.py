"""Parse messy weight strings into integer kilograms."""
from __future__ import annotations

import re
from typing import Optional, Tuple

# matches "1.450", "1,450", "1450" (with optional thousands sep), captures the number group
_NUM = r"(\d[\d.,\s]*\d|\d)"
_RANGE_RE = re.compile(_NUM + r"\s*[-–—]\s*" + _NUM)
_SINGLE_RE = re.compile(_NUM)


def _to_int_kg(raw: str) -> Optional[int]:
    """Normalize a single numeric token (may contain . , spaces as thousands) to kg int."""
    if raw is None:
        return None
    t = raw.strip().replace(" ", "")
    if not t:
        return None
    # Remove thousands separators (both . and ,) — weights are whole kg, no decimals.
    t = t.replace(".", "").replace(",", "")
    if not t.isdigit():
        return None
    val = int(t)
    # sanity: passenger car curb weight plausible range
    if val < 400 or val > 5000:
        return None
    return val


def parse_weight(text: Optional[str]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """Return (representative, min, max) in kg.

    - "1450"            -> (1450, None, None)
    - "1.450 kg"        -> (1450, None, None)
    - "1450 - 1620"     -> (1535, 1450, 1620)   representative = midpoint
    - "kerb 1,620 kg"   -> (1620, None, None)
    - garbage / empty   -> (None, None, None)
    """
    if not text:
        return (None, None, None)
    s = str(text)
    m = _RANGE_RE.search(s)
    if m:
        lo = _to_int_kg(m.group(1))
        hi = _to_int_kg(m.group(2))
        if lo is not None and hi is not None:
            if lo > hi:
                lo, hi = hi, lo
            return ((lo + hi) // 2, lo, hi)
        single = lo if lo is not None else hi
        return (single, None, None)
    m = _SINGLE_RE.search(s)
    if m:
        return (_to_int_kg(m.group(1)), None, None)
    return (None, None, None)


def detect_basis(text: Optional[str]) -> str:
    """Classify the weight basis from surrounding label text."""
    if not text:
        return "unknown"
    t = text.lower()
    if "running order" in t or "menetkész" in t or "fahrbereit" in t:
        return "mass_in_running_order"
    if "dry" in t or "trocken" in t:
        return "dry"
    if "curb" in t or "kerb" in t or "leergewicht" in t or "saját" in t or "üres" in t:
        return "curb"
    return "unknown"
