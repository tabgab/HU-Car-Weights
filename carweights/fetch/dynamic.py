"""JS-rendering fetch via Playwright Chromium. Used only for JS-only sources
(e.g. cars-data.com, a Next.js app whose spec values aren't in static HTML).
Cache-first so re-runs never re-render.
"""
from __future__ import annotations

from typing import Optional

from . import cache, robots


def render(
    url: str,
    source_name: str,
    *,
    use_cache: bool = True,
    max_age_days: Optional[float] = 30.0,
    respect_robots: bool = True,
    wait_until: str = "networkidle",
    timeout: int = 45000,
) -> str:
    if use_cache:
        cached = cache.read(source_name, url, max_age_days=max_age_days)
        if cached is not None:
            return cached
    if respect_robots and not robots.allowed(url):
        raise RuntimeError(f"blocked by robots.txt: {url}")

    from playwright.sync_api import sync_playwright  # lazy import

    robots.wait(url)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=None)
            page.goto(url, wait_until=wait_until, timeout=timeout)
            html = page.content()
        finally:
            browser.close()
    cache.write(source_name, url, html)
    return html


def render_stealth(
    url: str,
    source_name: str,
    *,
    use_cache: bool = True,
    max_age_days: float | None = 30.0,
    tries: int = 3,
) -> str:
    """Cloudflare-bypassing render via Scrapling StealthyFetcher (cache-first).

    For HU sources behind Cloudflare (katalogus.hasznaltauto.hu). Slow (~15s/page).
    """
    if use_cache:
        cached = cache.read(source_name, url, max_age_days=max_age_days)
        if cached is not None:
            return cached

    from scrapling.fetchers import StealthyFetcher  # lazy import

    f = StealthyFetcher()
    last = None
    for i in range(tries):
        robots.wait(url)
        try:
            page = f.fetch(url, solve_cloudflare=True, timeout=90000, network_idle=True)
            html = page.html_content if hasattr(page, "html_content") else str(page)
            if html and "just a moment" not in html.lower():
                cache.write(source_name, url, html)
                return html
            last = RuntimeError("cloudflare not solved")
        except Exception as e:  # navigation races etc.
            last = e
    raise RuntimeError(f"stealth render failed for {url}: {last}")
