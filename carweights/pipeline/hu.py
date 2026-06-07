"""Hungarian-catalog scrape + cross-source reconciliation.

katalogus.hasznaltauto.hu is the authoritative HU-market source. For each cars-data
variant we find the matching HU catalog entries (by make + model slug + powertrain),
adopt the HU 'saját tömeg' as the canonical curb weight, and flag whether the
international (cars-data) figure agrees.
"""
from __future__ import annotations

import re
import sqlite3
import unicodedata

from ..db import repository as R
from ..scrape import katalogus_hu as K

WEIGHT_TOL = 0.025  # ±2.5% counts as agreement


def _ascii(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def scrape_make_hu(conn: sqlite3.Connection, brand_slug: str, *, max_variants=None, log=print) -> dict:
    st = {"variants": 0, "with_weight": 0, "errors": 0}
    try:
        urls = K.discover_variant_urls(brand_slug)
    except Exception as e:
        log(f"! {brand_slug}: HU discovery failed: {e}")
        st["errors"] += 1
        return st
    if max_variants:
        urls = urls[:max_variants]
    log(f"• HU {brand_slug}: {len(urls)} variants")
    for u in urls:
        try:
            rec = K.parse_variant(brand_slug, u)
            R.upsert_hu_catalog(conn, brand_slug, _ascii(rec.model_slug), rec.variant_slug,
                                rec.powertrain_hint, rec.drivetrain, rec.weight_kg, rec.url)
            st["variants"] += 1
            if rec.weight_kg:
                st["with_weight"] += 1
        except Exception as e:
            log(f"  ! {u}: {e}")
            st["errors"] += 1
    conn.commit()
    return st


def crosscheck(conn: sqlite3.Connection, log=print) -> dict:
    """Match HU catalog to variants; adopt HU weight as authoritative; flag agreement."""
    # group HU weights by (make, model, powertrain)
    hu = {}
    for r in conn.execute("SELECT make_slug, model_slug, powertrain_type, weight_kg "
                          "FROM hu_catalog WHERE weight_kg IS NOT NULL"):
        key = (_ascii(r["make_slug"]), _ascii(r["model_slug"]), r["powertrain_type"])
        hu.setdefault(key, []).append(r["weight_kg"])

    rows = conn.execute(
        """SELECT v.variant_id, v.powertrain_type, w.curb_weight_kg,
                  mk.canonical_name AS make, md.slug AS model_slug, md.canonical_name AS model
           FROM variants v
           JOIN models md ON md.model_id=v.model_id
           JOIN makes mk ON mk.make_id=md.make_id
           LEFT JOIN weights w ON w.variant_id=v.variant_id"""
    ).fetchall()

    stats = {"matched": 0, "confirmed": 0, "conflict": 0}
    for r in rows:
        key = (_ascii(r["make"]), _ascii(r["model_slug"]), r["powertrain_type"])
        hu_weights = hu.get(key)
        cd = r["curb_weight_kg"]
        if not hu_weights:
            conn.execute("UPDATE weights SET n_sources=1, sources_agree=NULL, hu_weight_kg=NULL,"
                         "primary_source='cars-data' WHERE variant_id=?", (r["variant_id"],))
            continue
        hu_min, hu_max = min(hu_weights), max(hu_weights)
        # representative HU figure = the one nearest the cars-data value (best variant guess)
        hu_w = min(hu_weights, key=lambda x: abs(x - cd)) if cd else round(sum(hu_weights) / len(hu_weights))
        # agreement: cars-data weight falls within the HU model range (±tol)
        agree = None
        if cd is not None:
            agree = 1 if hu_min * (1 - WEIGHT_TOL) <= cd <= hu_max * (1 + WEIGHT_TOL) else 0
        stats["matched"] += 1
        stats["confirmed" if agree == 1 else "conflict" if agree == 0 else "matched"] += 0
        if agree == 1:
            stats["confirmed"] += 1
        elif agree == 0:
            stats["conflict"] += 1
        # corroborate (do NOT overwrite the per-variant cars-data weight); keep both visible
        conn.execute(
            """UPDATE weights SET hu_weight_kg=?, n_sources=2, sources_agree=?,
                      primary_source='katalogus.hu', updated_at=datetime('now')
               WHERE variant_id=?""",
            (hu_w, agree, r["variant_id"]),
        )
        R.add_provenance(conn, "weight", r["variant_id"], "curb_weight_kg", K.SOURCE,
                         value_text=f"{hu_min}-{hu_max} kg" if hu_min != hu_max else f"{hu_w} kg",
                         source_url=f"{K.BASE}/{_ascii(r['make'])}", confidence=K.CONFIDENCE)
    conn.commit()
    return stats
