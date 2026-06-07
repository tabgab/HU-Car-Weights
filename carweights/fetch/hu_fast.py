"""Fast Cloudflare-cleared fetcher for katalogus.hasznaltauto.hu.

Solve the Cloudflare challenge ONCE with a stealth browser to obtain a clearance cookie,
then fetch every page with curl_cffi (Chrome TLS impersonation) so the cookie is honoured
without re-rendering — ~0.5s/page instead of ~15s. Re-solves on expiry/403. Cache-first.
"""
from __future__ import annotations

import threading

from . import cache, robots

_cookies: dict | None = None
_ua: str | None = None
_lock = threading.Lock()
_ROOT = "https://katalogus.hasznaltauto.hu/"


def _solve() -> None:
    from scrapling.fetchers import StealthyFetcher
    global _cookies, _ua
    p = StealthyFetcher().fetch(_ROOT, solve_cloudflare=True, timeout=90000, network_idle=True)
    _cookies = {c["name"]: c["value"] for c in p.cookies}
    try:
        _ua = p.request_headers.get("user-agent")
    except Exception:
        _ua = None


def get(url: str, source_name: str, *, use_cache: bool = True, max_age_days: float | None = 30.0) -> str:
    if use_cache:
        cached = cache.read(source_name, url, max_age_days=max_age_days)
        if cached is not None:
            return cached

    from curl_cffi import requests as creq
    global _cookies

    for attempt in range(4):
        with _lock:
            if _cookies is None:
                _solve()
            cookies, ua = _cookies, _ua
        robots.wait(url)
        try:
            r = creq.get(url, cookies=cookies, headers={"User-Agent": ua} if ua else None,
                         impersonate="chrome", timeout=30)
        except Exception:
            with _lock:
                _cookies = None
            continue
        low = r.text.lower()
        if r.status_code == 200 and "just a moment" not in low and "<title>attention required" not in low:
            cache.write(source_name, url, r.text)
            return r.text
        with _lock:  # challenge/403 -> force re-solve
            _cookies = None
    raise RuntimeError(f"hu_fast failed (cloudflare) for {url}")
