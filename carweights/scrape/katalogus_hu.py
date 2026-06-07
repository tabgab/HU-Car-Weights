"""katalogus.hasznaltauto.hu — Hungarian-market car catalog (authoritative HU source).

Per-variant pages at /<brand>/<slug>/<id> carry 'Saját tömeg N kg' (curb weight) with
Hungarian-market variant names. Cloudflare-protected -> Scrapling stealth render (cached).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup

from ..fetch import dynamic

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


def discover_variant_urls(brand_slug: str) -> List[str]:
    html = dynamic.render_stealth(f"{BASE}/{brand_slug}", SOURCE)
    soup = BeautifulSoup(html, "lxml")
    pat = re.compile(rf"{re.escape(BASE)}/{re.escape(brand_slug)}/[^/]+/\d+$")
    urls = [a["href"] for a in soup.find_all("a", href=True) if pat.match(a["href"])]
    return list(dict.fromkeys(urls))


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
    html = dynamic.render_stealth(url, SOURCE)
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
    pt = _powertrain_from(slug, low)
    return HuRecord(make=brand_slug, model_slug=model_slug, variant_slug=slug, url=url,
                    weight_kg=weight, powertrain_hint=pt, drivetrain=drivetrain, raw_weight=raw)
