"""cars-data.com adapter.

Discovery (static HTML, requests): model page -> generation pages -> variant /specs URLs.
Weight extraction (rendered, Playwright): the spec values live in the Next.js RSC
(__next_f) payload as label/value pairs, e.g. "Kerb weight" -> "1,249 kg".
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

from bs4 import BeautifulSoup

from ..fetch import dynamic, http
from ..normalize.powertrain import normalize_drivetrain
from ..normalize.units import parse_weight

SOURCE = "cars-data"
SOURCE_RENDERED = "cars-data-rendered"
BASE = "https://cars-data.com"
CONFIDENCE = 0.8

_WEIGHT_LABELS = ("kerb weight", "curb weight", "empty weight", "kerb / curb weight")


@dataclass
class VariantRecord:
    make: str
    model: str
    trim: str
    url: str
    curb_weight_kg: Optional[int] = None
    curb_weight_min_kg: Optional[int] = None
    curb_weight_max_kg: Optional[int] = None
    powertrain_type: str = "ICE"
    powertrain_subtype: Optional[str] = None
    drivetrain: Optional[str] = None
    power_kw: Optional[int] = None
    battery_kwh: Optional[float] = None
    model_year: Optional[int] = None
    confidence: float = CONFIDENCE
    raw_weight: Optional[str] = None


def model_url(make_slug: str, model_slug: str) -> str:
    return f"{BASE}/en/{make_slug}/{model_slug}"


# brand-page links that are body-type/fuel/category filters, not real models
_NOT_A_MODEL = {
    "diesel", "electric", "petrol", "hybrid", "lpg", "cng", "hydrogen", "ethanol",
    "phev", "bev", "mhev", "hev", "ev", "mild-hybrid", "plug-in-hybrid",
    "hatchback", "sedan", "saloon", "estate", "station-wagon", "wagon", "suv", "mpv",
    "coupe", "convertible", "cabriolet", "cabrio", "van", "pickup", "pick-up", "minivan",
    "crossover", "roadster", "limousine", "compact", "city-car", "sports", "off-road",
    "4x4", "manual", "automatic", "new", "used", "commercial", "funcruiser", "targa",
}


def discover_models(make_slug: str) -> List[str]:
    """All model slugs listed on a make's brand page (category pseudo-links removed)."""
    html = http.get(f"{BASE}/en/{make_slug}", SOURCE)
    soup = BeautifulSoup(html, "lxml")
    pat = re.compile(rf"^/en/{re.escape(make_slug)}/([^/]+)$")
    out = []
    for a in soup.find_all("a", href=True):
        m = pat.match(a["href"])
        if m and m.group(1) not in _NOT_A_MODEL:
            out.append(m.group(1))
    return list(dict.fromkeys(out))


def discover_generations(make_slug: str, model_slug: str) -> List[str]:
    """Generation page URLs (e.g. /golf/2024-hatchback) from the static model page."""
    html = http.get(model_url(make_slug, model_slug), SOURCE)
    soup = BeautifulSoup(html, "lxml")
    pat = re.compile(rf"^/en/{re.escape(make_slug)}/{re.escape(model_slug)}/[^/]+$")
    gens = [a["href"] for a in soup.find_all("a", href=True) if pat.match(a["href"])]
    return [BASE + g for g in dict.fromkeys(gens)]


def discover_variants(generation_url: str) -> List[str]:
    """Variant detail URLs from a static generation page (…--<id>)."""
    path = generation_url[len(BASE):]
    html = http.get(generation_url, SOURCE)
    soup = BeautifulSoup(html, "lxml")
    pat = re.compile(rf"^{re.escape(path)}/.+--\d+$")
    vs = [a["href"] for a in soup.find_all("a", href=True) if pat.match(a["href"])]
    return [BASE + v for v in dict.fromkeys(vs)]


def _rsc_text(html: str) -> str:
    chunks = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', html, re.S)
    out = []
    for c in chunks:
        try:
            out.append(json.loads(c))
        except Exception:
            continue
    return "".join(out)


def _spec_pairs(rsc: str) -> dict:
    """Ordered label->value spec pairs from the RSC children-string sequence."""
    seq = re.findall(r'"children":"([^"]{1,48})"', rsc)
    pairs: dict[str, str] = {}
    for i, v in enumerate(seq):
        if re.search(r"\d\s*kg", v) or re.search(r"\d\s*(kw|hp|kwh|cc)\b", v.lower()):
            for j in range(i - 1, max(-1, i - 4), -1):
                lbl = seq[j]
                if "kg" not in lbl and "lb" not in lbl and re.search(r"[A-Za-z]", lbl):
                    pairs.setdefault(lbl.strip().lower(), v.strip())
                    break
    return pairs


def parse_variant(make: str, model: str, variant_url: str) -> VariantRecord:
    trim = variant_url.rstrip("/").split("/")[-1]
    trim = re.sub(r"--\d+$", "", trim).replace("-", " ").strip()
    trim = re.sub(r"^variant\s+", "", trim).strip()  # cars-data slugs prefix 'variant-'
    specs_url = variant_url + "/specs"
    html = dynamic.render(specs_url, SOURCE_RENDERED)
    rsc = _rsc_text(html)
    pairs = _spec_pairs(rsc)

    rec = VariantRecord(make=make, model=model, trim=trim, url=specs_url)

    # weight
    raw = None
    for lbl in _WEIGHT_LABELS:
        if lbl in pairs:
            raw = pairs[lbl]
            break
    if raw:
        rec.raw_weight = raw
        before_paren = raw.split("(")[0]
        v, lo, hi = parse_weight(before_paren)
        rec.curb_weight_kg, rec.curb_weight_min_kg, rec.curb_weight_max_kg = v, lo, hi

    # power (kW) and battery (kWh) if present
    for lbl, val in pairs.items():
        if rec.power_kw is None and re.search(r"\bpower\b", lbl) and "kw" in val.lower():
            m = re.search(r"(\d{2,4})\s*kw", val.lower())
            if m:
                rec.power_kw = int(m.group(1))
        if rec.battery_kwh is None and ("battery" in lbl or "capacity" in lbl) and "kwh" in val.lower():
            m = re.search(r"(\d{1,3}(?:\.\d)?)\s*kwh", val.lower())
            if m:
                rec.battery_kwh = float(m.group(1))

    # year from generation path segment (…/2024-hatchback/…)
    ym = re.search(r"/(\d{4})-", variant_url)
    if ym:
        rec.model_year = int(ym.group(1))

    # battery capacity from trim (e.g. "84kwh") if not already found
    if rec.battery_kwh is None:
        bm = re.search(r"(\d{2,3})\s*kwh", trim.lower())
        if bm:
            rec.battery_kwh = float(bm.group(1))

    # Powertrain via AUTHORITATIVE structural signals from the spec sheet, not just the
    # trim name (cars-data BEV trims like "m70"/"performance awd" carry no EV keyword):
    #   - no engine cylinder field        -> BEV (no combustion engine)
    #   - has cylinders + plug-in signal  -> PHEV
    #   - has cylinders, no plug          -> ICE (subtype from trim)
    # Authoritative consumption signals (the dirty "fuel tank"/"valves" fields on EV pages
    # are ignored): kWh/100km => electric energy use; l/100km => combustion fuel use.
    low = rsc.lower()
    trim_low = trim.lower()
    has_ev = "kwh/100km" in low
    has_fuel = "l/100km" in low
    plug = any(k in trim_low for k in
               ("plug-in", "plug in", "phev", "4xe", "recharge", "e-hybrid", "ehybrid",
                "e tense", "e-tense", "e performance", "e-performance")) \
        or re.search(r"(?<![a-z])iv(?![a-z])", trim_low) is not None
    bev_signal = (has_ev or (rec.battery_kwh and rec.battery_kwh > 5)) and not has_fuel and not plug

    if bev_signal:
        rec.powertrain_type, rec.powertrain_subtype, rec.confidence = "BEV", "BEV", 0.9
    elif plug or (has_ev and has_fuel):
        rec.powertrain_type, rec.powertrain_subtype, rec.confidence = "PHEV", "PHEV", 0.85
    else:
        if any(k in trim_low for k in ("tdi", "diesel", "dci", "hdi", "cdi", "crdi", "bluehdi")):
            sub = "diesel"
        elif any(k in trim_low for k in ("etsi", "mhev", "48v", "e tec", "e-tec", "mild")):
            sub = "MHEV"
        elif "hybrid" in trim_low or "e power" in trim_low or "e-power" in trim_low:
            sub = "HEV"
        else:
            sub = "petrol"
        rec.powertrain_type, rec.powertrain_subtype, rec.confidence = "ICE", sub, 0.8

    rec.drivetrain = normalize_drivetrain(trim)
    return rec
