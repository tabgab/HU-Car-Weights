"""Canonicalize make/model names via an alias map (config/aliases.yaml)."""
from __future__ import annotations

import functools
import re
import unicodedata
from typing import Dict

import yaml

from ..settings import CONFIG_DIR


def _squash(s: str) -> str:
    """Ascii-fold, lowercase, strip everything but letters/digits:
    'Mercedes-Benz' -> 'mercedesbenz', 'Škoda' -> 'skoda'.

    Some pipeline stages (hu_catalog.make_slug) store ascii-squashed slugs, so the
    alias lookup must tolerate missing hyphens/spaces and stripped accents."""
    folded = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", folded.lower())


@functools.lru_cache(maxsize=1)
def _aliases() -> Dict[str, Dict[str, str]]:
    path = CONFIG_DIR / "aliases.yaml"
    if not path.exists():
        return {"makes": {}, "models": {}, "makes_squashed": {}, "models_squashed": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    makes = {k.lower(): v for k, v in (data.get("makes") or {}).items()}
    models = {k.lower(): v for k, v in (data.get("models") or {}).items()}

    def sqkey(k: str) -> str:
        # squash each part of a possibly make-scoped key ("jaecoo/5") separately so
        # the '/' separator survives and scoped keys can't collide with plain names
        return "/".join(_squash(p) for p in k.split("/"))

    return {
        "makes": makes,
        "models": models,
        "makes_squashed": {sqkey(k): v for k, v in makes.items()},
        "models_squashed": {sqkey(k): v for k, v in models.items()},
    }


def _lookup(kind: str, name: str, scope: str = "") -> str:
    a = _aliases()
    key = name.strip().lower()
    if scope:
        # make-scoped model alias, e.g. models: {"jaecoo/5": "J5"} — needed where a
        # bare name ("5") means different cars under different makes.
        scoped = a[kind].get(f"{scope}/{key}")
        if scoped is not None:
            return scoped
        scoped = a[kind + "_squashed"].get(_squash(scope) + "/" + _squash(key))
        if scoped is not None:
            return scoped
    hit = a[kind].get(key)
    if hit is not None:
        return hit
    return a[kind + "_squashed"].get(_squash(key), name.strip())


def canonical_make(name: str) -> str:
    if not name:
        return name
    return _lookup("makes", name)


def canonical_model(name: str, make: str = "") -> str:
    if not name:
        return name
    return _lookup("models", name, scope=make)
