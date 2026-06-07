"""robots.txt checking with per-host crawl-delay enforcement.

Uses a small, correct longest-match matcher rather than urllib.robotparser, which
mis-parses some valid real-world robots.txt files that group many User-agent lines
(e.g. cars-data.com) and then disallows everything.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlparse

import requests

from ..settings import USER_AGENT

DEFAULT_DELAYS = {
    "cars-data.com": 1.5, "www.cars-data.com": 1.5,
    "carfolio.com": 10.0, "www.carfolio.com": 10.0,
    "ultimatespecs.com": 30.0, "www.ultimatespecs.com": 30.0,
    "katalogus.hasznaltauto.hu": 0.3,
}

# host -> {"rules": [(allow_bool, path)], "delay": float|None}
_cache: dict[str, dict] = {}
_last_hit: dict[str, float] = {}


def _host(url: str) -> str:
    return urlparse(url).netloc.lower()


def _parse(robots_txt: str, ua_token: str) -> dict:
    """Extract the rule group whose User-agents include our token, else the '*' group."""
    groups: list[dict] = []
    cur: dict | None = None
    started_rules = False
    for raw in robots_txt.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip().lower()
        value = value.strip()
        if field == "user-agent":
            if cur is None or started_rules:
                cur = {"agents": [], "rules": [], "delay": None}
                groups.append(cur)
                started_rules = False
            cur["agents"].append(value.lower())
        elif field in ("allow", "disallow") and cur is not None:
            started_rules = True
            cur["rules"].append((field == "allow", value))
        elif field == "crawl-delay" and cur is not None:
            started_rules = True
            try:
                cur["delay"] = float(value)
            except ValueError:
                pass

    def match_group(token: str):
        for g in groups:
            if any(token == a or (a != "*" and a in token) for a in g["agents"]):
                return g
        return None

    chosen = match_group(ua_token) or next((g for g in groups if "*" in g["agents"]), None)
    return chosen or {"agents": ["*"], "rules": [], "delay": None}


def _rule_re(path: str) -> str:
    # convert robots path with * wildcards and optional $ anchor to regex
    p = re.escape(path).replace(r"\*", ".*")
    if p.endswith(r"\$"):
        p = p[:-2] + "$"
    return "^" + p


def _load(url: str) -> dict:
    host = _host(url)
    if host in _cache:
        return _cache[host]
    scheme = urlparse(url).scheme or "https"
    txt = ""
    try:
        r = requests.get(f"{scheme}://{host}/robots.txt",
                         headers={"User-Agent": USER_AGENT}, timeout=15)
        if r.status_code == 200 and "<html" not in r.text[:200].lower():
            txt = r.text
    except requests.RequestException:
        txt = ""
    ua_token = USER_AGENT.split("/")[0].lower()
    grp = _parse(txt, ua_token) if txt else {"rules": [], "delay": None}
    _cache[host] = grp
    return grp


def allowed(url: str) -> bool:
    grp = _load(url)
    path = urlparse(url).path or "/"
    best_len, best_allow = -1, True  # default allow when no rule matches
    for allow, rule_path in grp["rules"]:
        if rule_path == "":
            continue
        if re.search(_rule_re(rule_path), path):
            specificity = len(rule_path)
            if specificity > best_len or (specificity == best_len and allow):
                best_len, best_allow = specificity, allow
    return best_allow


def crawl_delay(url: str) -> float:
    grp = _load(url)
    if grp.get("delay"):
        return float(grp["delay"])
    return DEFAULT_DELAYS.get(_host(url), 3.0)


def wait(url: str) -> None:
    host = _host(url)
    delay = crawl_delay(url)
    last = _last_hit.get(host)
    if last is not None:
        elapsed = time.time() - last
        if elapsed < delay:
            time.sleep(delay - elapsed)
    _last_hit[host] = time.time()
