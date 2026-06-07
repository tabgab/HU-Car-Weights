"""Manufacturer brochure / spec-sheet PDF ingestion (gap-filler).

Downloads (or reads a local) PDF and extracts curb-weight figures with nearby context.
Curb-weight labels are matched across HU / EN / DE so manufacturer leaflets in any of
those languages work.
"""
from __future__ import annotations

import io
import os
import re
from dataclasses import dataclass
from typing import List

import requests

from ..settings import USER_AGENT

SOURCE_TMPL = "manufacturer:{make}.hu"
CONFIDENCE = 0.97  # manufacturer's own figure: top authority

_LABEL = re.compile(r"saját\s*tömeg|sajat\s*tomeg|kerb\s*weight|curb\s*weight|kerb\s*mass|"
                    r"curb\s*mass|leergewicht|unladen|kerb\s*\(curb\)|kerb/curb", re.I)
_NUM = re.compile(r"\b(\d[.,]?\d{2,3})\b")  # 947 / 1855 / 1.940 / 2,073 (not across spaces)


@dataclass
class PdfWeight:
    context: str
    weight_kg: int
    page: int


def fetch_pdf(url: str) -> bytes:
    if os.path.exists(url):  # local file path
        with open(url, "rb") as fh:
            return fh.read()
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=40)
    r.raise_for_status()
    if "pdf" not in r.headers.get("content-type", "").lower() and r.content[:4] != b"%PDF":
        raise ValueError(f"not a PDF: {url} ({r.headers.get('content-type')})")
    return r.content


def extract_weights(pdf_bytes: bytes) -> List[PdfWeight]:
    import pdfplumber

    out: List[PdfWeight] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for line in text.splitlines():
                if _LABEL.search(line):
                    # join space-separated thousands ('2 535' -> '2535') before matching
                    line = re.sub(r"(\d)\s+(\d{3})(?!\d)", r"\1\2", line)
                    for m in _NUM.finditer(line):
                        digits = re.sub(r"\D", "", m.group(1))
                        if digits and 600 <= int(digits) <= 4000:
                            out.append(PdfWeight(context=line.strip()[:90],
                                                 weight_kg=int(digits), page=pno))
    return out


def ingest(make: str, model: str, pdf_url: str) -> dict:
    data = fetch_pdf(pdf_url)
    weights = extract_weights(data)
    return {
        "make": make, "model": model, "source_url": pdf_url,
        "source_name": SOURCE_TMPL.format(make=make),
        "weights": [w.weight_kg for w in weights],
        "rows": [(w.context, w.weight_kg, w.page) for w in weights[:40]],
    }
