"""Gzip cache for raw fetched pages, keyed by sha1(url)."""
from __future__ import annotations

import gzip
import hashlib
from pathlib import Path
from typing import Optional

from ..settings import RAW_DIR


def _key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def cache_path(source_name: str, url: str) -> Path:
    d = RAW_DIR / source_name
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_key(url)}.html.gz"


def read(source_name: str, url: str, max_age_days: Optional[float] = None) -> Optional[str]:
    p = cache_path(source_name, url)
    if not p.exists():
        return None
    if max_age_days is not None:
        import time
        if (time.time() - p.stat().st_mtime) > max_age_days * 86400:
            return None
    with gzip.open(p, "rt", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def write(source_name: str, url: str, content: str) -> Path:
    p = cache_path(source_name, url)
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        fh.write(content)
    return p
