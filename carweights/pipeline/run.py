"""Seed/scrape orchestrator: discover -> parse -> upsert -> derive."""
from __future__ import annotations

import sqlite3
from typing import Optional

from ..db import repository as R
from ..normalize.names import canonical_make, canonical_model
from ..scrape import cars_data
from .derive import derive


def _store(conn: sqlite3.Connection, rec: cars_data.VariantRecord) -> None:
    make = canonical_make(rec.make)
    model = canonical_model(rec.model)
    mk = R.upsert_make(conn, make)
    md = R.upsert_model(conn, mk, model)
    fp = R.variant_fingerprint(R.slugify(make), R.slugify(model),
                               rec.powertrain_subtype, rec.power_kw,
                               rec.drivetrain, rec.battery_kwh)
    # include trim so distinct trims (same engine) stay separate -> real per-model range
    if rec.trim:
        fp = fp + "|" + R.slugify(rec.trim)
    vid = R.upsert_variant(
        conn, md, fp, rec.powertrain_type, rec.powertrain_subtype, rec.trim,
        rec.drivetrain, rec.power_kw, rec.battery_kwh, rec.model_year,
    )
    R.upsert_weight(conn, vid, rec.curb_weight_kg, rec.curb_weight_min_kg,
                    rec.curb_weight_max_kg)
    R.add_provenance(conn, "variant", vid, "powertrain_type", cars_data.SOURCE,
                     value_text=rec.trim, source_url=rec.url, confidence=rec.confidence)
    if rec.curb_weight_kg is not None or rec.curb_weight_min_kg is not None:
        R.add_provenance(conn, "weight", vid, "curb_weight_kg", cars_data.SOURCE,
                         value_text=rec.raw_weight, source_url=rec.url,
                         confidence=rec.confidence)


def _gen_year(gen_url: str) -> Optional[int]:
    import re
    # year appears in the generation segment, e.g. .../golf/2024-hatchback
    m = re.search(r"(19|20)\d{2}", gen_url.rsplit("/", 1)[-1])
    return int(m.group(0)) if m else None


def scrape_model(
    conn: sqlite3.Connection,
    make_slug: str,
    model_slug: str,
    *,
    max_generations: int = 1,
    max_variants: Optional[int] = 8,
    min_year: Optional[int] = None,
    log=print,
) -> dict:
    stats = {"variants": 0, "with_weight": 0, "errors": 0}
    try:
        gens = cars_data.discover_generations(make_slug, model_slug)
    except Exception as e:
        log(f"  ! {make_slug}/{model_slug}: discovery failed: {e}")
        stats["errors"] += 1
        return stats
    if not gens:
        log(f"  ! {make_slug}/{model_slug}: no generations found")
        return stats

    # keep only current generations (year unknown is kept; newest first)
    if min_year is not None:
        cur = [g for g in gens if (_gen_year(g) is None or _gen_year(g) >= min_year)]
        if not cur:
            stats["skipped_old"] = True
            return stats
        gens = cur

    for gen in gens[:max_generations]:
        try:
            variants = cars_data.discover_variants(gen)
        except Exception as e:
            log(f"  ! {gen}: variant discovery failed: {e}")
            stats["errors"] += 1
            continue
        if max_variants:
            variants = variants[:max_variants]
        for vurl in variants:
            try:
                rec = cars_data.parse_variant(make_slug, model_slug, vurl)
                _store(conn, rec)
                stats["variants"] += 1
                if rec.curb_weight_kg is not None or rec.curb_weight_min_kg is not None:
                    stats["with_weight"] += 1
                wtxt = rec.raw_weight or "—"
                log(f"    · {rec.trim[:42]:42s} {rec.powertrain_type:4s} {wtxt}")
            except Exception as e:
                log(f"    ! {vurl}: {e}")
                stats["errors"] += 1
    conn.commit()
    return stats


def scrape_make(
    conn: sqlite3.Connection,
    make_slug: str,
    *,
    max_models: Optional[int] = None,
    max_variants: int = 3,
    min_year: int = 2023,
    log=print,
) -> dict:
    """Discover and scrape all current models of a make."""
    agg = {"models": 0, "variants": 0, "with_weight": 0, "errors": 0, "skipped": 0}
    try:
        models = cars_data.discover_models(make_slug)
    except Exception as e:
        log(f"! {make_slug}: model discovery failed: {e}")
        agg["errors"] += 1
        return agg
    if max_models:
        models = models[:max_models]
    log(f"• {make_slug}: {len(models)} candidate models")
    for ms in models:
        st = scrape_model(conn, make_slug, ms, max_generations=1,
                          max_variants=max_variants, min_year=min_year, log=log)
        if st.get("skipped_old"):
            agg["skipped"] += 1
            continue
        if st["variants"]:
            agg["models"] += 1
        for k in ("variants", "with_weight", "errors"):
            agg[k] += st[k]
        conn.commit()
    return agg


def run_market(conn: sqlite3.Connection, makes: list[str], *, max_models=None,
               max_variants=3, min_year=2018, log=print) -> dict:
    total = {"makes": 0, "models": 0, "variants": 0, "with_weight": 0, "errors": 0, "skipped": 0}
    for mk in makes:
        st = scrape_make(conn, mk, max_models=max_models, max_variants=max_variants,
                         min_year=min_year, log=log)
        total["makes"] += 1
        for k in ("models", "variants", "with_weight", "errors", "skipped"):
            total[k] += st[k]
        log(f"  = {mk}: {st['models']} current models, {st['variants']} variants, "
            f"{st['skipped']} skipped(old), {st['errors']} errors")
    log("• deriving parking classification…")
    total["classification"] = derive(conn)
    return total


def run_seed(conn: sqlite3.Connection, seeds: list[dict], *, max_variants=8, log=print) -> dict:
    total = {"models": 0, "variants": 0, "with_weight": 0, "errors": 0}
    for s in seeds:
        log(f"• {s['make']} / {s['model']}")
        st = scrape_model(conn, s["make"], s["model"],
                          max_generations=s.get("max_generations", 1),
                          max_variants=s.get("max_variants", max_variants), log=log)
        total["models"] += 1
        for k in ("variants", "with_weight", "errors"):
            total[k] += st[k]
    log("• deriving parking classification…")
    total["classification"] = derive(conn)
    return total
