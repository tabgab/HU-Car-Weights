"""Manufacturer Hungarian brochure / spec-sheet PDF ingestion (gap-filler).

Manufacturer .hu sites publish 'Műszaki adatok' brochures listing 'Saját tömeg'. This
downloads such a PDF and extracts curb-weight figures with nearby model/variant context.
Used to fill gaps where katalogus.hasznaltauto.hu lacks a model. Per-brand brochure URLs
are bespoke, so this is pointed at a specific PDF (CLI: `hu-pdf <make> <model> <pdf_url>`).
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import List, Optional

import requests

from ..settings import USER_AGENT

SOURCE_TMPL = "manufacturer:{make}.hu"
CONFIDENCE = 0.97  # manufacturer's own HU figure: top authority


@dataclass
class PdfWeight:
    context: str          # surrounding text (variant/column label)
    weight_kg: int
    page: int


def fetch_pdf(url: str) -> bytes:
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=40)
    r.raise_for_status()
    if "pdf" not in r.headers.get("content-type", "").lower() and not r.content[:4] == b"%PDF":
        raise ValueError(f"not a PDF: {url} ({r.headers.get('content-type')})")
    return r.content


def extract_weights(pdf_bytes: bytes) -> List[PdfWeight]:
    """Find 'Saját tömeg' rows and the kg values on the same line/row."""
    import pdfplumber

    out: List[PdfWeight] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for line in text.splitlines():
                if re.search(r"saját\s*tömeg|sajat\s*tomeg", line, re.I):
                    # all plausible kg numbers on this line (HU uses space thousands sep)
                    for m in re.finditer(r"(\d[\d  ]{2,6})\s*(?:kg)?", line):
                        digits = re.sub(r"\D", "", m.group(1))
                        if digits and 600 <= int(digits) <= 4000:
                            out.append(PdfWeight(context=line.strip()[:80],
                                                 weight_kg=int(digits), page=pno))
    return out


def ingest(make: str, model: str, pdf_url: str) -> dict:
    """Download + parse; return found weights (caller stores into hu_catalog/provenance)."""
    data = fetch_pdf(pdf_url)
    weights = extract_weights(data)
    return {
        "make": make, "model": model, "source_url": pdf_url,
        "source_name": SOURCE_TMPL.format(make=make),
        "weights": [w.weight_kg for w in weights],
        "rows": [(w.context, w.weight_kg, w.page) for w in weights[:40]],
    }
