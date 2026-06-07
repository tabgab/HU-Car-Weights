"""katalogus.hasznaltauto.hu — Hungarian-market car catalog (authoritative HU source).

Per-variant pages at /<brand>/<slug>/<id> carry 'Saját tömeg N kg' (curb weight) with
Hungarian-market variant names. Cloudflare-protected -> Scrapling stealth render (cached).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup

from ..fetch import hu_fast

SOURCE = "katalogus.hu"
BASE = "https://katalogus.hasznaltauto.hu"
CONFIDENCE = 0.95  # Hungarian-market catalog: authoritative tier


@dataclass
class HuRecord:
    make: str
    model_slug: str          # first token(s) of the variant slug, used to match cars-data model
    variant_slug: str
    url: str
    weight_kg: Optional[int]
    powertrain_hint: Optional[str]   # 'BEV'|'PHEV'|'ICE' guess from slug/page
    drivetrain: Optional[str]
    raw_weight: Optional[str] = None
    display_name: Optional[str] = None   # clean H1, e.g. 'CUPRA Formentor 2.0 TSI VZ DSG'
    power_kw: Optional[int] = None
    model_year: Optional[int] = None


def discover_variant_urls(brand_slug: str) -> List[str]:
    html = hu_fast.get(f"{BASE}/{brand_slug}", SOURCE)
    soup = BeautifulSoup(html, "lxml")
    pat = re.compile(rf"{re.escape(BASE)}/{re.escape(brand_slug)}/[^/]+/\d+$")
    urls = [a["href"] for a in soup.find_all("a", href=True) if pat.match(a["href"])]
    return list(dict.fromkeys(urls))


def _powertrain_from_fuel(fuel: str) -> Optional[str]:
    """Classify from the catalog's Üzemanyag (fuel) field — the authoritative signal."""
    if not fuel:
        return None
    if "plug-in" in fuel or "plug in" in fuel or "konnektor" in fuel:
        return "PHEV"
    if "elektromos" in fuel and "benzin" not in fuel and "dízel" not in fuel and "dizel" not in fuel:
        return "BEV"
    if "hibrid" in fuel or "benzin" in fuel or "dízel" in fuel or "dizel" in fuel or "gáz" in fuel:
        return "ICE"  # combustion bucket (incl. full/mild hybrid)
    return None


def _powertrain_from(slug: str, page_low: str) -> str:
    s = slug.lower()
    if any(k in s for k in ("phev", "plug", "e_hybrid", "4xe", "recharge")):
        return "PHEV"
    if "kwh" in s and not any(k in s for k in ("tsi", "tdi", "tce", "benzin", "dizel")):
        # battery in slug and no combustion token -> likely BEV (but PHEV also has kwh; checked above)
        if "elektromos" in page_low or "100% elektromos" in page_low or "kwh/100" in page_low:
            return "BEV"
        return "BEV"
    if "elektromos" in page_low and "benzin" not in page_low and "dízel" not in page_low:
        return "BEV"
    return "ICE"


def parse_variant(brand_slug: str, url: str) -> HuRecord:
    html = hu_fast.get(url, SOURCE)
    low = html.lower()
    soup = BeautifulSoup(html, "lxml")
    raw = None
    weight = None
    # 'Saját tömeg' label and value may sit in sibling cells -> read the whole row
    for el in soup.find_all(string=re.compile(r"saját tömeg", re.I)):
        row = el.find_parent(["tr", "li", "div"])
        txt = re.sub(r"\s+", " ", row.get_text(" ", strip=True)) if row else str(el)
        m = re.search(r"saját tömeg\D{0,6}([\d ]{3,8})\s*kg", txt, re.I)
        if m:
            digits = re.sub(r"\D", "", m.group(1))
            if digits and 400 <= int(digits) <= 5000:
                weight = int(digits)
                raw = m.group(0)
                break
    slug = url[len(BASE) + 1:].rsplit("/", 1)[0].split("/", 1)[-1]  # the <slug> part
    model_slug = re.split(r"[_]", slug)[0]
    drivetrain = "4WD" if re.search(r"(?<![a-z])awd(?![a-z])|4wd|x_?drive|quattro|4motion|allrad", slug.lower()) else None

    # fuel type from the 'Üzemanyag' spec row -> authoritative powertrain
    fuel = ""
    for el in soup.find_all(string=re.compile(r"üzemanyag", re.I)):
        row = el.find_parent(["tr", "li", "div"])
        if row:
            fuel = re.sub(r"\s+", " ", row.get_text(" ", strip=True)).lower()
            break
    pt = _powertrain_from_fuel(fuel) or _powertrain_from(slug, low)

    # clean display name + model year from the H1 / title
    h1 = soup.find("h1")
    display = h1.get_text(" ", strip=True) if h1 else ((soup.title.string or "") if soup.title else "")
    display = re.sub(r"\bAutókatalógus\b\s*[-–]?\s*", "", display).strip()
    ym = re.search(r"\((\d{4})", display)
    model_year = int(ym.group(1)) if ym else None
    display = re.sub(r"\s*\(.*\)\s*$", "", display).strip()
    pm = re.search(r"(\d{2,4})\s*(?:le|hp|kw)\b", low)
    power_kw = None
    if pm:
        v = int(pm.group(1))
        power_kw = round(v * 0.7355) if "le" in pm.group(0) or "hp" in pm.group(0) else v

    return HuRecord(make=brand_slug, model_slug=model_slug, variant_slug=slug, url=url,
                    weight_kg=weight, powertrain_hint=pt, drivetrain=drivetrain, raw_weight=raw,
                    display_name=display or None, power_kw=power_kw, model_year=model_year)
