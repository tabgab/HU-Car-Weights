"""Canonicalize make/model names via an alias map (config/aliases.yaml)."""
from __future__ import annotations

import functools
from typing import Dict

import yaml

from ..settings import CONFIG_DIR


@functools.lru_cache(maxsize=1)
def _aliases() -> Dict[str, Dict[str, str]]:
    path = CONFIG_DIR / "aliases.yaml"
    if not path.exists():
        return {"makes": {}, "models": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "makes": {k.lower(): v for k, v in (data.get("makes") or {}).items()},
        "models": {k.lower(): v for k, v in (data.get("models") or {}).items()},
    }


def canonical_make(name: str) -> str:
    if not name:
        return name
    return _aliases()["makes"].get(name.strip().lower(), name.strip())


def canonical_model(name: str) -> str:
    if not name:
        return name
    return _aliases()["models"].get(name.strip().lower(), name.strip())
