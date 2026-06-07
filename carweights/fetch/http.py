"""Polite HTTP fetching: cache-first, robots-aware, retry/backoff."""
from __future__ import annotations

import time
from typing import Optional

import requests

from ..settings import USER_AGENT
from . import cache, robots


class FetchError(Exception):
    pass


_session: Optional[requests.Session] = None


def session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": USER_AGENT,
                                 "Accept-Language": "en,hu;q=0.8"})
    return _session


def get(
    url: str,
    source_name: str,
    *,
    use_cache: bool = True,
    max_age_days: Optional[float] = 30.0,
    respect_robots: bool = True,
    retries: int = 3,
    timeout: int = 25,
) -> str:
    """Return page text, from cache if fresh, else fetch politely and cache it."""
    if use_cache:
        cached = cache.read(source_name, url, max_age_days=max_age_days)
        if cached is not None:
            return cached

    if respect_robots and not robots.allowed(url):
        raise FetchError(f"blocked by robots.txt: {url}")

    last_exc = None
    for attempt in range(retries):
        robots.wait(url)
        try:
            r = session().get(url, timeout=timeout)
            if r.status_code == 200:
                cache.write(source_name, url, r.text)
                return r.text
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                last_exc = FetchError(f"HTTP {r.status_code} for {url}")
                continue
            raise FetchError(f"HTTP {r.status_code} for {url}")
        except requests.RequestException as e:
            last_exc = e
            time.sleep(2 ** attempt)
    raise FetchError(f"failed after {retries} attempts: {url} ({last_exc})")
