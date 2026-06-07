"""cherymotors.hu — Chery Hungary importer.

The site is a React SPA backed by a public REST API at api.cherymotors.hu.
Each car type has an 'Árlista' (pricelist) PDF that contains a 'Saját tömeg' row
on the spec page. We fetch pricelist PDFs from the API and extract the curb weight
via manufacturer_pdf.extract_weights().

Powertrain is determined from the car's API type key + PDF content:
  - HEV (full hybrid, no plug) → ICE
  - CSH / Plug-in Hibrid (external charging) → PHEV
  - BEV → BEV (not currently in the HU lineup)

Models on sale in Hungary as of 2025-06 (via carTypeKey):
  tiggo-4-hibrid, tiggo-7, tiggo-7-hev,
  tiggo-7-plug-in-hybrid (CSH), tiggo-8, tiggo-8-plug-in-hybrid (CSH),
  tiggo-9-phev (CSH)
"""
from __future__ import annotations

import re

from . import manufacturer_pdf as M

SOURCE_NAME = "cherymotors.hu"
API_BASE = "https://api.cherymotors.hu/1.0.0"

# car-type-key → (model canonical name, powertrain)
# The API route maps tiggo-7-phev / tiggo-7-csh → tiggo-7-plug-in-hybrid, etc.
_CAR_TYPES: list[tuple[str, str, str]] = [
    ("tiggo-4-hibrid",          "Tiggo 4",  "ICE"),   # 1.5 HEV full hybrid
    ("tiggo-7",                 "Tiggo 7",  "ICE"),   # 1.6 T-GDI petrol
    ("tiggo-7-hev",             "Tiggo 7",  "ICE"),   # 1.5 HEV full hybrid
    ("tiggo-7-plug-in-hybrid",  "Tiggo 7",  "PHEV"),  # CSH, plug-in
    ("tiggo-8",                 "Tiggo 8",  "ICE"),   # 1.6 T-GDI petrol
    ("tiggo-8-plug-in-hybrid",  "Tiggo 8",  "PHEV"),  # CSH, plug-in
    ("tiggo-9-phev",            "Tiggo 9",  "PHEV"),  # CSH, plug-in (34.5 kWh)
]

# Trim labels derived from car-type-key suffixes
_TRIM_HINTS = {
    "tiggo-4-hibrid":           "HEV",
    "tiggo-7-hev":              "HEV",
    "tiggo-7-plug-in-hybrid":   "Plug-in Hibrid",
    "tiggo-8-plug-in-hybrid":   "Plug-in Hibrid",
    "tiggo-9-phev":             "Plug-in Hibrid",
}


def _fetch_pricelist_url(car_type_key: str) -> tuple[str, str] | None:
    """Return (pdf_url, original_filename) for the 'Árlista' document of a car type.

    There may be multiple Árlista entries (e.g. 2025 + MY26); we return the latest
    (highest document id).
    """
    import requests

    headers = {"Content-Type": "application/json",
               "User-Agent": "Mozilla/5.0 (compatible; carWeights-bot/1.0)"}
    r = requests.get(f"{API_BASE}/cars/{car_type_key}", headers=headers, timeout=30)
    if not r.ok:
        return None
    car = r.json().get("car", {})
    docs = car.get("documents", [])
    # documentType.id == 1 → 'Árlista'; pick the highest id (most recent upload)
    pricelists = [d for d in docs if d.get("documentType", {}).get("id") == 1]
    if not pricelists:
        return None
    best = max(pricelists, key=lambda d: d.get("id", 0))
    return best["url"], best["originalFilename"]


def crawl(*, log=print) -> list[dict]:
    """Return ingest_manual records for all Chery HU models.

    Each record has {make, model, trim, powertrain, weight, source_url, source_name}.
    """
    records: list[dict] = []
    seen: set[tuple] = set()  # (model, powertrain, weight) — dedup across re-uploads

    for car_type_key, model, powertrain in _CAR_TYPES:
        trim = _TRIM_HINTS.get(car_type_key)
        result = _fetch_pricelist_url(car_type_key)
        if result is None:
            log(f"  ! {car_type_key}: no Árlista document found in API")
            continue
        pdf_url, fn = result
        log(f"  · {car_type_key}: {fn}")
        try:
            data = M.fetch_pdf(pdf_url)
            weights = M.extract_weights(data)
        except Exception as e:
            log(f"  ! {fn}: {e}")
            continue
        if not weights:
            log(f"  ! {fn}: no 'Saját tömeg' found (image-based PDF?)")
            continue
        for w in weights:
            key = (model, powertrain, w.weight_kg)
            if key in seen:
                log(f"    (dup skipped: {model} {powertrain} {w.weight_kg} kg)")
                continue
            seen.add(key)
            records.append({
                "make": "Chery",
                "model": model,
                "trim": trim,
                "powertrain": powertrain,
                "weight": w.weight_kg,
                "source_url": pdf_url,
                "source_name": SOURCE_NAME,
            })
            log(f"    → {model} ({powertrain}) {w.weight_kg} kg  trim={trim!r}")

    return records
