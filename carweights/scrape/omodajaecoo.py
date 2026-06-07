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


def _model_and_powertrain(brand: str, filename: str):
    fn = filename.lower()
    m = re.search(r"(?:omoda|jaecoo|^o|^j)[ _]?([5789])", fn)
    model = f"{brand.title()} {m.group(1)}" if m else brand.title()
    if "ev" in fn:
        pt = "BEV"
    elif "shs-p" in fn or "phev" in fn or "plug" in fn:
        pt = "PHEV"
    else:
        pt = "ICE"
    return model, pt


def crawl(brand: str, *, log=print) -> list[dict]:
    """Return [{model, powertrain, weight, source_url}] for a brand."""
    out = []
    for url in _pdf_urls(PAGES[brand]):
        fn = url.rsplit("/", 1)[-1].replace("%20", " ")
        try:
            res = M.ingest(brand, fn, url)
        except Exception as e:
            log(f"  ! {fn}: {e}")
            continue
        if not res["weights"]:
            continue
        model, pt = _model_and_powertrain(brand, fn)
        for kg in sorted(set(res["weights"])):
            out.append({"model": model, "powertrain": pt, "weight": kg, "source_url": url})
        log(f"  · {fn[:40]:40s} {model} {pt} -> {sorted(set(res['weights']))}")
    return out
