"""Crawl a manufacturer/dealer Hungarian site's spec-PDF listing and ingest curb weights.

The authoritative HU source: a brand's own 'Műszaki adatok' (technical spec) PDFs. Given a
page that lists them, harvest the specification PDFs, derive the model from the filename,
extract 'Saját tömeg', and ingest. Per-brand listing URLs live in config/dealer_sources.yaml.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..settings import USER_AGENT
from . import manufacturer_pdf as M

SPEC_RE = re.compile(r"muszaki|specif|technical|adatok", re.I)
NAV_RE = re.compile(r"letölt|letolt|download|katal|brochure|prospekt|árlist|arlist|price|"
                    r"műszaki|muszaki|spec|adatok", re.I)
# desktop Chrome UA — some HU sites 403 the research UA
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0 Safari/537.36")


def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": BROWSER_UA, "Accept-Language": "hu,en;q=0.8"})
    return s


def _all_pdfs_from(s, page_url: str) -> list[str]:
    r = s.get(page_url, timeout=20, allow_redirects=True)
    r.raise_for_status()
    host = urlparse(r.url).netloc
    soup = BeautifulSoup(r.text, "lxml")
    pdfs = {urljoin(r.url, a["href"]) for a in soup.find_all("a", href=True)
            if a["href"].lower().split("?")[0].endswith(".pdf")}
    subs = [urljoin(r.url, a["href"]) for a in soup.find_all("a", href=True)
            if NAV_RE.search(a.get("href", "") + " " + a.get_text(" "))]
    for u in [x for x in dict.fromkeys(subs) if urlparse(x).netloc == host][:6]:
        try:
            rr = s.get(u, timeout=15)
            for a in BeautifulSoup(rr.text, "lxml").find_all("a", href=True):
                if a["href"].lower().split("?")[0].endswith(".pdf"):
                    pdfs.add(urljoin(u, a["href"]))
        except Exception:
            pass
    return list(pdfs)


def discover_spec_pdfs(page_url: str) -> list[str]:
    """Per-model spec sheets, identified by filename (e.g. kia-niro-muszaki-adatok.pdf)."""
    s = _session()
    pdfs = _all_pdfs_from(s, page_url)
    return [p for p in pdfs if SPEC_RE.search(p.rsplit("/", 1)[-1])]


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
