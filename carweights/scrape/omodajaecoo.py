"""omodajaecoo.hu (Omoda + Jaecoo HU importer) — bot-protected, JS-rendered.

The model showroom's 'Katalógus' buttons link to catalog/spec PDFs on a CDN. We render
the page with Scrapling (anti-bot), collect the PDFs, and extract 'Saját tömeg'. Some PDFs
are image-based (no text table) and yield nothing — those models stay gaps.
"""
from __future__ import annotations

import re

from . import manufacturer_pdf as M

PAGES = {
    "omoda": "https://www.omodajaecoo.hu/omoda-modellek/?caru-showroomCategoryTab=all",
    "jaecoo": "https://www.omodajaecoo.hu/jaecoo-modellek/?caru-showroomCategoryTab=all",
}


def _pdf_urls(page_url: str) -> list[str]:
    from scrapling.fetchers import StealthyFetcher
    p = StealthyFetcher().fetch(page_url, solve_cloudflare=True, timeout=90000, network_idle=True)
    html = p.html_content if hasattr(p, "html_content") else str(p)
    return list(dict.fromkeys(re.findall(r'href="([^"]+\.pdf[^"]*)"', html, re.I)))


def _model_num(brand: str, text: str) -> str | None:
    m = re.search(rf"{brand}\s*[ _]?([5789])", text, re.I)
    return m.group(1) if m else None


def _model_trim(brand: str, header: str, filename: str):
    """From a page header like 'OMODA 5 SHS-H MŰSZAKI ADATOK' -> ('Omoda 5', 'SHS-H')."""
    num = _model_num(brand, header) or _model_num(brand, filename.replace("o5", "omoda 5")
                                                  .replace("o7", "omoda 7").replace("o9", "omoda 9"))
    model = num if num else brand.title()  # match katalogus model naming ('5'/'7'/'9')
    trim = ""
    if header:
        h = re.sub(r"m[űu]szaki adatok.*$", "", header, flags=re.I).strip()
        h = re.sub(rf"^{brand}\s*{num or ''}\s*", "", h, flags=re.I).strip()
        trim = h[:40] or None
    return model, (trim or None)


def crawl(brand: str, *, log=print) -> list[dict]:
    """Return ingest_manual records for a brand (per-variant model/trim/powertrain)."""
    from ..normalize.names import canonical_make
    make = canonical_make(brand)
    out = []
    for url in _pdf_urls(PAGES[brand]):
        fn = url.rsplit("/", 1)[-1].replace("%20", " ")
        try:
            res = M.ingest(brand, fn, url)
        except Exception as e:
            log(f"  ! {fn}: {e}")
            continue
        fnl = fn.lower()
        for it in res.get("items", []):
            model, trim = _model_trim(brand, it["header"], fn)
            if trim in ("-", "–", ""):
                trim = None
            pt = it["powertrain"]
            if ("ev" in re.split(r"[ _.-]", fnl)) and "shs" not in fnl:
                pt = "BEV"          # 'Omoda 5 EV' brochure
            elif "shs-p" in fnl or "phev" in fnl:
                pt = "PHEV"
            out.append({"make": make, "model": model, "trim": trim,
                        "powertrain": pt, "weight": it["weight"],
                        "source_url": url, "source_name": "omodajaecoo.hu"})
        if res.get("items"):
            here = [(r["model"], r["trim"], r["powertrain"], r["weight"]) for r in out if r["source_url"] == url]
            log(f"  · {fn[:38]:38s} -> {here[:4]}")
    return out
