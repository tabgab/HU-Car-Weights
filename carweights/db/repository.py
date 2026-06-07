"""Idempotent upsert helpers. All writes converge on natural/fingerprint keys."""
from __future__ import annotations

import re
import sqlite3
from typing import Optional


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower())
    return s.strip("-")


def upsert_make(conn: sqlite3.Connection, canonical_name: str, on_sale_hu: int = 1) -> int:
    slug = slugify(canonical_name)
    conn.execute(
        """INSERT INTO makes(canonical_name, slug, on_sale_hu) VALUES(?,?,?)
           ON CONFLICT(slug) DO UPDATE SET
             canonical_name=excluded.canonical_name,
             on_sale_hu=excluded.on_sale_hu,
             updated_at=datetime('now')""",
        (canonical_name, slug, on_sale_hu),
    )
    return conn.execute("SELECT make_id FROM makes WHERE slug=?", (slug,)).fetchone()[0]


def upsert_model(
    conn: sqlite3.Connection,
    make_id: int,
    canonical_name: str,
    body_type: Optional[str] = None,
    model_year_from: Optional[int] = None,
    model_year_to: Optional[int] = None,
    on_sale_hu: int = 1,
) -> int:
    slug = slugify(canonical_name)
    conn.execute(
        """INSERT INTO models(make_id, canonical_name, slug, body_type,
                              model_year_from, model_year_to, on_sale_hu)
           VALUES(?,?,?,?,?,?,?)
           ON CONFLICT(make_id, slug) DO UPDATE SET
             canonical_name=excluded.canonical_name,
             body_type=COALESCE(excluded.body_type, models.body_type),
             model_year_from=COALESCE(excluded.model_year_from, models.model_year_from),
             model_year_to=COALESCE(excluded.model_year_to, models.model_year_to),
             on_sale_hu=excluded.on_sale_hu,
             updated_at=datetime('now')""",
        (make_id, canonical_name, slug, body_type, model_year_from, model_year_to, on_sale_hu),
    )
    return conn.execute(
        "SELECT model_id FROM models WHERE make_id=? AND slug=?", (make_id, slug)
    ).fetchone()[0]


def variant_fingerprint(
    make_slug: str,
    model_slug: str,
    powertrain_subtype: Optional[str],
    power_kw: Optional[int],
    drivetrain: Optional[str],
    battery_kwh: Optional[float],
) -> str:
    batt = "" if battery_kwh is None else str(int(round(battery_kwh / 5.0)))  # 5 kWh buckets
    return "|".join(
        [
            make_slug,
            model_slug,
            (powertrain_subtype or "?"),
            ("" if power_kw is None else str(power_kw)),
            (drivetrain or "?"),
            batt,
        ]
    )


def upsert_variant(
    conn: sqlite3.Connection,
    model_id: int,
    fingerprint: str,
    powertrain_type: str,
    powertrain_subtype: Optional[str] = None,
    trim_name: Optional[str] = None,
    drivetrain: Optional[str] = None,
    power_kw: Optional[int] = None,
    battery_kwh: Optional[float] = None,
    model_year: Optional[int] = None,
    on_sale_hu: int = 1,
    source: str = "cars-data",
) -> int:
    conn.execute(
        """INSERT INTO variants(model_id, trim_name, powertrain_type, powertrain_subtype,
                                drivetrain, power_kw, battery_kwh, model_year, on_sale_hu,
                                source, fingerprint)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(model_id, fingerprint) DO UPDATE SET
             trim_name=COALESCE(excluded.trim_name, variants.trim_name),
             powertrain_type=excluded.powertrain_type,
             powertrain_subtype=COALESCE(excluded.powertrain_subtype, variants.powertrain_subtype),
             drivetrain=COALESCE(excluded.drivetrain, variants.drivetrain),
             power_kw=COALESCE(excluded.power_kw, variants.power_kw),
             battery_kwh=COALESCE(excluded.battery_kwh, variants.battery_kwh),
             model_year=COALESCE(excluded.model_year, variants.model_year),
             on_sale_hu=excluded.on_sale_hu,
             source=excluded.source,
             updated_at=datetime('now')""",
        (model_id, trim_name, powertrain_type, powertrain_subtype, drivetrain,
         power_kw, battery_kwh, model_year, on_sale_hu, source, fingerprint),
    )
    return conn.execute(
        "SELECT variant_id FROM variants WHERE model_id=? AND fingerprint=?",
        (model_id, fingerprint),
    ).fetchone()[0]


def upsert_weight(
    conn: sqlite3.Connection,
    variant_id: int,
    curb_weight_kg: Optional[int],
    curb_weight_min_kg: Optional[int] = None,
    curb_weight_max_kg: Optional[int] = None,
    weight_basis: str = "curb",
) -> int:
    is_missing = 1 if (curb_weight_kg is None and curb_weight_min_kg is None
                       and curb_weight_max_kg is None) else 0
    conn.execute(
        """INSERT INTO weights(variant_id, unit, curb_weight_kg, curb_weight_min_kg,
                               curb_weight_max_kg, weight_basis, is_missing)
           VALUES(?,?,?,?,?,?,?)
           ON CONFLICT(variant_id) DO UPDATE SET
             curb_weight_kg=COALESCE(excluded.curb_weight_kg, weights.curb_weight_kg),
             curb_weight_min_kg=COALESCE(excluded.curb_weight_min_kg, weights.curb_weight_min_kg),
             curb_weight_max_kg=COALESCE(excluded.curb_weight_max_kg, weights.curb_weight_max_kg),
             weight_basis=excluded.weight_basis,
             is_missing=excluded.is_missing,
             updated_at=datetime('now')""",
        (variant_id, "kg", curb_weight_kg, curb_weight_min_kg, curb_weight_max_kg,
         weight_basis, is_missing),
    )
    return conn.execute(
        "SELECT weight_id FROM weights WHERE variant_id=?", (variant_id,)
    ).fetchone()[0]


def add_provenance(
    conn: sqlite3.Connection,
    entity_type: str,
    entity_id: int,
    field: str,
    source_name: str,
    value_text: Optional[str] = None,
    source_url: Optional[str] = None,
    confidence: float = 0.5,
    raw_cache_path: Optional[str] = None,
) -> None:
    conn.execute(
        """INSERT INTO provenance(entity_type, entity_id, field, value_text, source_name,
                                  source_url, confidence, raw_cache_path)
           VALUES(?,?,?,?,?,?,?,?)
           ON CONFLICT(entity_type, entity_id, field, source_name) DO UPDATE SET
             value_text=excluded.value_text,
             source_url=excluded.source_url,
             confidence=excluded.confidence,
             raw_cache_path=excluded.raw_cache_path,
             scraped_at=datetime('now')""",
        (entity_type, entity_id, field, value_text, source_name, source_url,
         confidence, raw_cache_path),
    )


def upsert_hu_catalog(conn, make_slug, model_slug, variant_slug, powertrain_type,
                      drivetrain, weight_kg, source_url, display_name=None,
                      power_kw=None, model_year=None):
    conn.execute(
        """INSERT INTO hu_catalog(make_slug, model_slug, variant_slug, powertrain_type,
                                  drivetrain, weight_kg, display_name, power_kw, model_year,
                                  source_url)
           VALUES(?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(source_url) DO UPDATE SET
             weight_kg=excluded.weight_kg, powertrain_type=excluded.powertrain_type,
             drivetrain=excluded.drivetrain, display_name=excluded.display_name,
             power_kw=excluded.power_kw, model_year=excluded.model_year,
             scraped_at=datetime('now')""",
        (make_slug, model_slug, variant_slug, powertrain_type, drivetrain, weight_kg,
         display_name, power_kw, model_year, source_url),
    )


def log_fetch(conn, url, source_name, http_status, cache_path, etag=None, content_hash=None):
    conn.execute(
        """INSERT INTO fetch_log(url, source_name, http_status, cache_path, etag, content_hash)
           VALUES(?,?,?,?,?,?)""",
        (url, source_name, http_status, cache_path, etag, content_hash),
    )
