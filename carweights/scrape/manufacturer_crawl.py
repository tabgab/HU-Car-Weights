"""Crawl a manufacturer/dealer Hungarian site's spec-PDF listing and ingest curb weights.

The authoritative HU source: a brand's own 'Műszaki adatok' (technical spec) PDFs. Given a
page that lists them, harvest the specification PDFs, derive the model from the filename,
extract 'Saját tömeg', and ingest. Per-brand listing URLs live in config/dealer_sources.yaml.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ..settings import USER_AGENT
from . import manufacturer_pdf as M

SPEC_RE = re.compile(r"muszaki|specif|technical|adatok", re.I)


def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "hu,en;q=0.8"})
    return s


def discover_spec_pdfs(page_url: str) -> list[str]:
    s = _session()
    r = s.get(page_url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    pdfs = [urljoin(page_url, a["href"]) for a in soup.find_all("a", href=True)
            if a["href"].lower().split("?")[0].endswith(".pdf")]
    spec = [p for p in dict.fromkeys(pdfs) if SPEC_RE.search(p)]
    return spec


def model_from_filename(brand: str, url: str) -> str:
    name = url.rsplit("/", 1)[-1].lower()
    name = re.sub(r"\.pdf.*$", "", name)
    # strip brand + spec keywords -> leave the model token(s)
    name = name.replace(brand.lower(), "")
    name = SPEC_RE.sub("", name)
    name = re.sub(r"[-_]+", " ", name).strip()
    return name or url.rsplit("/", 1)[-1]


def crawl_brand(brand: str, page_url: str, *, log=print) -> list[dict]:
    """Return list of {make, model, weights, source_url} from a brand's spec PDFs."""
    out = []
    try:
        pdfs = discover_spec_pdfs(page_url)
    except Exception as e:
        log(f"! {brand}: spec page failed: {e}")
        return out
    log(f"• {brand}: {len(pdfs)} spec PDFs")
    for pdf in pdfs:
        model = model_from_filename(brand, pdf)
        try:
            res = M.ingest(brand, model, pdf)
            if res["weights"]:
                out.append(res)
                log(f"  · {model[:30]:30s} -> {sorted(set(res['weights']))}")
        except Exception as e:
            log(f"  ! {pdf}: {e}")
    return out
