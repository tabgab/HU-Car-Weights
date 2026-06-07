"""Classify a car variant into BEV / PHEV / ICE from fuel/name signals.

Ordered rules: structured signals first (battery + engine displacement), then keyword
precedence PHEV > BEV > MHEV/HEV > diesel/petrol. Full/series hybrids (incl. Nissan
e-Power) fall into the ICE bucket because, per the Budapest rule, anything with a
combustion engine uses the 1800 kg threshold.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

PHEV_KW = (
    "phev", "plug-in", "plug in", "plugin", "plug-in hybrid", "konnektor",
    "e-hybrid", "ehybrid", "recharge", "4xe", "e-tense", "blue hybrid plug",
    "tfsi e", "tsi e", "twin engine",
)
BEV_KW = (
    "electric", "elektromos", "100% electric", "battery electric", "bev",
    "e-tron", "etron", "ev6", "id.", "id3", "id4", "id5", "ioniq", "eqa", "eqb",
    "eqc", "eqe", "eqs", "i4", "ix", "i5", "i7", "e-208", "e-2008", "e-c4",
)
# generic "ev" handled carefully (substring of many words) -> only as standalone token
MHEV_KW = ("mhev", "mild hybrid", "48v", "48 v", "mild-hybrid", "etsi")
HEV_KW = (
    "hybrid", "hev", "full hybrid", "self-charging", "öntöltő", "e-power",
    "hsd", "e-cvt", "e:hev", "e-tech hybrid",
)
DIESEL_KW = ("diesel", "dízel", "dizel", "tdi", "dci", "hdi", "bluehdi", "d4d",
             "cdi", "bluetec", "crdi", "cdti", "dtr", "blue tec")
PETROL_KW = ("petrol", "benzin", "tsi", "tfsi", "tce", "vti", "gdi", "t-gdi",
             "tgdi", "mpi", "ecoboost", "gasoline", "puretech", "firefly",
             "skyactiv-g", "mhev petrol")


@dataclass
class PowertrainResult:
    powertrain_type: str            # 'BEV' | 'PHEV' | 'ICE'
    powertrain_subtype: Optional[str]  # 'BEV'|'PHEV'|'MHEV'|'HEV'|'diesel'|'petrol'|None
    confidence: float


def _has(text: str, kws) -> bool:
    return any(k in text for k in kws)


def _has_token_ev(text: str) -> bool:
    # standalone 'ev' token (avoid matching 'level', 'seven', etc.)
    import re
    return re.search(r"(?<![a-z])ev(?![a-z])", text) is not None


def classify(
    fuel: Optional[str] = None,
    name: Optional[str] = None,
    battery_kwh: Optional[float] = None,
    engine_displacement_cc: Optional[int] = None,
    chargeable: Optional[bool] = None,
) -> PowertrainResult:
    text = " ".join(p for p in (fuel, name) if p).lower()
    has_engine = bool(engine_displacement_cc and engine_displacement_cc > 0)
    has_battery = bool(battery_kwh and battery_kwh > 0)

    # 1. Strong structured signals
    if has_battery and not has_engine and (_has(text, BEV_KW) or _has_token_ev(text)
                                           or "electric" in text or not text):
        if not _has(text, DIESEL_KW) and not _has(text, PETROL_KW):
            return PowertrainResult("BEV", "BEV", 0.95)
    if has_battery and has_engine:
        return PowertrainResult("PHEV", "PHEV", 0.9)

    # 2/3. Keyword precedence (PHEV beats generic hybrid/electric substrings)
    if _has(text, PHEV_KW):
        return PowertrainResult("PHEV", "PHEV", 0.85)
    if (_has(text, BEV_KW) or _has_token_ev(text)) and not _has(text, DIESEL_KW) \
            and not _has(text, PETROL_KW) and not _has(text, HEV_KW):
        return PowertrainResult("BEV", "BEV", 0.85)
    if _has(text, MHEV_KW):
        return PowertrainResult("ICE", "MHEV", 0.8)
    if _has(text, HEV_KW):  # full/series hybrid (incl. e-Power) -> combustion bucket
        return PowertrainResult("ICE", "HEV", 0.8)
    if _has(text, DIESEL_KW):
        return PowertrainResult("ICE", "diesel", 0.8)
    if _has(text, PETROL_KW):
        return PowertrainResult("ICE", "petrol", 0.75)

    # 4. Fallback: assume combustion, low confidence (flagged)
    if has_battery:
        return PowertrainResult("BEV", "BEV", 0.4)
    return PowertrainResult("ICE", None, 0.3)


def normalize_drivetrain(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.lower()
    if any(k in t for k in ("4wd", "awd", "4x4", "4motion", "quattro", "xdrive",
                            "4matic", "all-wheel", "allrad", "összkerék")):
        return "4WD"
    if any(k in t for k in ("2wd", "fwd", "rwd", "front-wheel", "rear-wheel",
                            "2x4", "first")):
        return "2WD"
    return None
