"""Extra Hungarian-market sources that need bespoke handling:
- locally-downloaded manufacturer brochure PDFs (Zeekr, Changan Deepal S07)
- Changan Deepal S05 web spec page (changaneurope.com)
"""
from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from ..settings import USER_AGENT
from . import manufacturer_pdf as M

CHANGAN_S05_URL = "https://www.changaneurope.com/de/modelle/changan-deepal-s05/spezifikationen"


def _manual_meta(filename: str):
    """(make, model, powertrain) from a downloaded brochure filename."""
    fn = filename.lower()
    if "zeekr" in fn:
        if "7gt" in fn:
            model = "7GT"
        elif "7x" in fn:
            model = "7X"
        elif re.search(r"zeekr-x|zeekr_x|-x-", fn):
            model = "X"
        else:
            model = "Zeekr"
        return ("Zeekr", model, "BEV")  # Zeekr is BEV-only
    if "changan" in fn or "deepal" in fn:
        m = re.search(r"s0?(\d)", fn)
        model = f"Deepal S0{m.group(1)}" if m else "Deepal"
        return ("Changan", model, "PHEV")  # Deepal S07 EU = range-extender (has engine)
    return (None, None, None)


def manual_pdf_records(directory: str, log=print) -> list[dict]:
    import glob
    import os
    recs = []
    for path in sorted(glob.glob(os.path.join(directory, "*.pdf"))):
        fn = os.path.basename(path)
        make, model, pt = _manual_meta(fn)
        if not make:
            log(f"  ? {fn}: unknown brand, skipped")
            continue
        try:
            res = M.ingest(make, model, path)
        except Exception as e:
            log(f"  ! {fn}: {e}")
            continue
        weights = sorted(set(res["weights"]))
        log(f"  · {fn[:40]:40s} {make} {model} {pt} -> {weights}")
        for kg in weights:
            recs.append({"make": make, "model": model, "powertrain": pt, "weight": kg,
                         "source_url": "manual:" + fn, "source_name": "manufacturer-pdf"})
    return recs


def changan_s05_records(log=print) -> list[dict]:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "de,hu,en;q=0.8"})
    r = s.get(CHANGAN_S05_URL, timeout=25)
    soup = BeautifulSoup(r.text, "lxml")
    weights = set()
    for el in soup.find_all(string=re.compile(r"leergewicht", re.I)):
        row = el.find_parent(["tr", "li", "div"])
        txt = re.sub(r"\s+", " ", row.get_text(" ", strip=True)) if row else ""
        if 0 < len(txt) < 80:
            for m in re.finditer(r"(\d[.,]?\d{2,3})\s*kg", txt):
                d = int(re.sub(r"\D", "", m.group(1)))
                if 800 <= d <= 4000:
                    weights.add(d)
    log(f"  Changan Deepal S05 (BEV; PHEV trim absent on site): {sorted(weights)}")
    # S05 listed trims are battery-electric; the PHEV version is not published here
    return [{"make": "Changan", "model": "Deepal S05", "powertrain": "BEV", "weight": kg,
             "source_url": CHANGAN_S05_URL, "source_name": "changaneurope.com"} for kg in sorted(weights)]
