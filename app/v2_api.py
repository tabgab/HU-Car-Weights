"""AndroidApp-style API for the new web UI: dynamic-threshold policy simulation.

Mirrors the structure of the Android app's `PolicySimulator` exactly, but
server-side, so the JS client can keep the classifier rules in a single
place (this server) and the client stays a thin view.
"""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from fastapi import APIRouter, Query

from . import fees
from .db import get_conn

router = APIRouter(prefix="/api/v2")


def _classify_row(pt: Optional[str], w: Optional[int], wmin: Optional[int], wmax: Optional[int],
                 t: int) -> str:
    """Mirror app/fees.classify + the Android Kotlin FeeClassifier.classify."""
    if wmin is not None and wmax is not None:
        lo, hi = wmin, wmax
    else:
        lo = wmin if wmin is not None else w
        hi = wmax if wmax is not None else w
    if lo is None and hi is None:
        return "unknown"
    if lo is not None and hi is not None:
        if lo > t:
            return "double"
        if hi <= t:
            return "ok"
        return "borderline"
    rep = w if w is not None else (lo if lo is not None else hi)
    if rep is None:
        return "unknown"
    return "double" if rep > t else "ok"


@router.get("/policy")
def policy(
    bev: int = Query(2000, ge=500, le=5000),
    ice: int = Query(1800, ge=500, le=5000),
    pt: List[str] = Query(default_factory=list, description="Powertrain subtype filter (BEV, PHEV, HEV, MHEV, petrol, diesel)"),
    make: List[str] = Query(default_factory=list, description="Make filter (canonical name)"),
    hu_only: bool = Query(False, description="Only cars with a Hungarian-catalog weight"),
    limit: int = Query(500, ge=1, le=2000, description="Max border cases to return per bucket"),
):
    """Return fleet outcome + border cases for a given policy + filters.

    Single endpoint, server-rendered, sub-100ms on the full 9k fleet.
    """
    conn = get_conn()
    try:
        where = ["COALESCE(w.is_missing, 0) = 0", "v.on_sale_hu = 1"]
        params: list = []
        if hu_only:
            where.append("w.hu_weight_kg IS NOT NULL")
        if pt:
            where.append(f"v.powertrain_subtype IN ({','.join('?' * len(pt))})")
            params.extend(pt)
        if make:
            where.append(f"mk.canonical_name IN ({','.join('?' * len(make))})")
            params.extend(make)
        where_sql = "WHERE " + " AND ".join(where)

        sql = f"""
            SELECT
                v.variant_id     AS id,
                mk.canonical_name AS make,
                md.canonical_name AS model,
                v.trim_name      AS trim,
                v.powertrain_type,
                v.powertrain_subtype,
                v.drivetrain,
                v.power_kw,
                v.battery_kwh,
                v.model_year,
                w.curb_weight_kg     AS weight,
                w.curb_weight_min_kg AS weight_min,
                w.curb_weight_max_kg AS weight_max,
                w.hu_weight_kg,
                w.sources_agree
            FROM variants v
            JOIN models md ON md.model_id = v.model_id
            JOIN makes  mk ON mk.make_id  = md.make_id
            LEFT JOIN weights w ON w.variant_id = v.variant_id
            {where_sql}
        """
        rows = conn.execute(sql, params).fetchall()

        ok = double = borderline = unknown = 0
        borders: List[dict] = []
        for r in rows:
            pt_type = r["powertrain_type"]
            t = bev if pt_type == "BEV" else ice
            status = _classify_row(pt_type, r["weight"], r["weight_min"], r["weight_max"], t)
            if status == "ok":
                ok += 1
            elif status == "double":
                double += 1
            elif status == "borderline":
                borderline += 1
            else:
                unknown += 1
            if status == "double" and r["weight"] is not None and t > 0:
                over_pct = (r["weight"] - t) / t * 100.0
                if 0 < over_pct <= 25.0:
                    borders.append({
                        "id": r["id"],
                        "make": r["make"],
                        "model": r["model"],
                        "trim": r["trim"],
                        "powertrain_subtype": r["powertrain_subtype"] or pt_type,
                        "weight": r["weight"],
                        "threshold": t,
                        "over_pct": over_pct,
                    })

        borders.sort(key=lambda b: b["over_pct"])
        b5 = [b for b in borders if b["over_pct"] <= 5.0][:limit]
        b10 = [b for b in borders if b["over_pct"] <= 10.0][:limit]
        b25 = borders[:limit]

        return {
            "total": len(rows),
            "ok": ok,
            "double": double,
            "borderline": borderline,
            "unknown": unknown,
            "bev_threshold": bev,
            "ice_threshold": ice,
            "border_cases": {
                "5pct": b5,
                "10pct": b10,
                "25pct": b25,
            },
            "thresholds": {"BEV": bev, "ICE": ice, "PHEV": ice, "HEV": ice, "MHEV": ice,
                           "petrol": ice, "diesel": ice},
        }
    finally:
        conn.close()


@router.get("/makes")
def list_makes(conn=None):
    """Distinct canonical make names, alphabetical."""
    if conn is None:
        conn = get_conn()
        try:
            rows = conn.execute(
                "SELECT DISTINCT canonical_name FROM makes "
                "WHERE on_sale_hu = 1 ORDER BY canonical_name"
            ).fetchall()
            return [r["canonical_name"] for r in rows]
        finally:
            conn.close()
    rows = conn.execute(
        "SELECT DISTINCT canonical_name FROM makes WHERE on_sale_hu = 1 ORDER BY canonical_name"
    ).fetchall()
    return [r["canonical_name"] for r in rows]
