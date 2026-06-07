"""Hungarian-catalog scrape + cross-source reconciliation.

katalogus.hasznaltauto.hu is the authoritative HU-market source. We render only the
catalog variants whose model matches a model already in our DB (focuses the slow
Cloudflare-bypass rendering on cars we display), then corroborate each cars-data
variant against the HU 'saját tömeg' and flag agree/conflict.
"""
from __future__ import annotations

import re
import sqlite3
import unicodedata

from ..db import repository as R
from ..scrape import katalogus_hu as K

WEIGHT_TOL = 0.025  # ±2.5% counts as agreement
# cars-data make slug -> candidate katalogus brand slugs
BRAND_ALIASES = {
    "mercedes-benz": ["mercedes", "mercedes_benz"],
    "alfa-romeo": ["alfa_romeo"],
    "land-rover": ["land_rover"],
}


def _ascii(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _variant_slug(url: str) -> str:
    return url[len(K.BASE) + 1:].rsplit("/", 1)[0].split("/", 1)[-1]


def _db_models_for(conn, brand_slug: str) -> set[str]:
    target = _ascii(brand_slug)
    out = set()
    for r in conn.execute("""SELECT mk.canonical_name AS mk, md.slug AS s
                             FROM models md JOIN makes mk ON mk.make_id=md.make_id"""):
        if _ascii(r["mk"]) == target:
            out.add(_ascii(r["s"]))
    return out


def _slug_powertrain(vslug: str) -> str:
    s = vslug.lower()
    if any(k in s for k in ("phev", "plug", "4xe", "recharge", "e_hybrid")):
        return "PHEV"
    if "kwh" in s and not any(k in s for k in ("tsi", "tdi", "tce", "gdi", "benzin", "dizel", "hdi")):
        return "BEV"
    return "ICE"


def scrape_make_hu(conn: sqlite3.Connection, brand_slug: str, *, max_variants=None,
                   per_model=3, model_filter=True, log=print) -> dict:
    st = {"variants": 0, "with_weight": 0, "errors": 0, "brand_used": None}
    cands = [brand_slug]
    if "-" in brand_slug:
        cands.append(brand_slug.replace("-", "_"))
    cands += BRAND_ALIASES.get(brand_slug, [])
    urls = []
    for c in dict.fromkeys(cands):
        try:
            urls = K.discover_variant_urls(c)
        except Exception:
            urls = []
        if urls:
            st["brand_used"] = c
            break
    if not urls:
        log(f"! {brand_slug}: no HU catalog brand page")
        return st

    if model_filter:
        want = _db_models_for(conn, brand_slug)
        if want:
            # keep the longest matching model slug per url (most specific)
            kept = []
            for u in urls:
                vs = _ascii(_variant_slug(u))
                m = max((m for m in want if vs.startswith(m)), key=len, default=None)
                if m:
                    kept.append((m, u))
            # cap per (model, powertrain-from-slug) so we sample breadth, not every trim
            seen: dict[tuple, int] = {}
            urls = []
            for m, u in kept:
                key = (m, _slug_powertrain(_variant_slug(u)))
                if seen.get(key, 0) < per_model:
                    seen[key] = seen.get(key, 0) + 1
                    urls.append(u)
    if max_variants:
        urls = urls[:max_variants]
    log(f"• HU {brand_slug} (as {st['brand_used']}): {len(urls)} relevant variants")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    brand_used = st["brand_used"]

    def fetch(u):
        return K.parse_variant(brand_used, u)

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch, u): u for u in urls}
        for fut in as_completed(futs):
            try:
                rec = fut.result()
            except Exception as e:
                log(f"  ! {futs[fut]}: {e}")
                st["errors"] += 1
                continue
            R.upsert_hu_catalog(conn, _ascii(brand_slug), _ascii(rec.variant_slug),
                                rec.variant_slug, rec.powertrain_hint, rec.drivetrain,
                                rec.weight_kg, rec.url)
            st["variants"] += 1
            if rec.weight_kg:
                st["with_weight"] += 1
    conn.commit()
    return st


def crosscheck(conn: sqlite3.Connection, log=print) -> dict:
    """Corroborate each cars-data variant against HU catalog (prefix match on model)."""
    # hu rows grouped by ascii make -> list of (variant_slug_ascii, powertrain, weight)
    hu = {}
    for r in conn.execute("SELECT make_slug, model_slug, powertrain_type, weight_kg "
                          "FROM hu_catalog WHERE weight_kg IS NOT NULL"):
        hu.setdefault(r["make_slug"], []).append(
            (r["model_slug"], r["powertrain_type"], r["weight_kg"]))

    rows = conn.execute(
        """SELECT v.variant_id, v.powertrain_type, w.curb_weight_kg,
                  mk.canonical_name AS make, md.slug AS model_slug
           FROM variants v
           JOIN models md ON md.model_id=v.model_id
           JOIN makes mk ON mk.make_id=md.make_id
           LEFT JOIN weights w ON w.variant_id=v.variant_id"""
    ).fetchall()

    stats = {"matched": 0, "confirmed": 0, "conflict": 0}
    for r in rows:
        mk = _ascii(r["make"])
        model = _ascii(r["model_slug"])
        cands = [w for (vslug, pt, w) in hu.get(mk, [])
                 if (pt == r["powertrain_type"] or pt is None) and vslug.startswith(model)]
        cd = r["curb_weight_kg"]
        if not cands:
            conn.execute("UPDATE weights SET n_sources=1, sources_agree=NULL, hu_weight_kg=NULL,"
                         "primary_source='cars-data' WHERE variant_id=?", (r["variant_id"],))
            continue
        hu_min, hu_max = min(cands), max(cands)
        hu_w = min(cands, key=lambda x: abs(x - cd)) if cd else round(sum(cands) / len(cands))
        agree = None
        if cd is not None:
            agree = 1 if hu_min * (1 - WEIGHT_TOL) <= cd <= hu_max * (1 + WEIGHT_TOL) else 0
        stats["matched"] += 1
        if agree == 1:
            stats["confirmed"] += 1
        elif agree == 0:
            stats["conflict"] += 1
        conn.execute(
            """UPDATE weights SET hu_weight_kg=?, n_sources=2, sources_agree=?,
                      primary_source='katalogus.hu', updated_at=datetime('now')
               WHERE variant_id=?""",
            (hu_w, agree, r["variant_id"]),
        )
        R.add_provenance(conn, "weight", r["variant_id"], "curb_weight_kg", K.SOURCE,
                         value_text=f"{hu_min}-{hu_max} kg" if hu_min != hu_max else f"{hu_w} kg",
                         source_url=f"{K.BASE}/{mk}", confidence=K.CONFIDENCE)
    conn.commit()
    return stats
