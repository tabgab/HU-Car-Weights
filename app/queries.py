"""Filter -> parameterized SQL. The fee_status CASE mirrors app.fees.classify exactly."""
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Tuple

# UI powertrain value -> DB powertrain_type
_PT_MAP = {"electric": "BEV", "bev": "BEV", "phev": "PHEV", "ice": "ICE"}

_SORTS = {
    "make": "make COLLATE NOCASE, model COLLATE NOCASE, trim COLLATE NOCASE",
    "weight_asc": "(weight IS NULL), weight ASC",
    "weight_desc": "(weight IS NULL), weight DESC",
    "year_desc": "(model_year IS NULL), model_year DESC",
}

# threshold + range + fee_status (app vocab) computed in SQL; mirrors fees.classify
_BASE_CTE = """
WITH base AS (
  SELECT *,
         CASE WHEN powertrain_type='BEV' THEN 2000 ELSE 1800 END AS threshold,
         COALESCE(weight_min, weight) AS w_lo,
         COALESCE(weight_max, weight) AS w_hi
  FROM v_parking_summary
),
classified AS (
  SELECT *,
    CASE
      WHEN w_lo IS NULL AND w_hi IS NULL THEN 'unknown'
      WHEN w_lo IS NOT NULL AND w_hi IS NOT NULL THEN
        CASE WHEN w_lo > threshold THEN 'double'
             WHEN w_hi <= threshold THEN 'ok'
             ELSE 'borderline' END
      ELSE
        CASE WHEN COALESCE(weight, w_lo, w_hi) IS NULL THEN 'unknown'
             WHEN COALESCE(weight, w_lo, w_hi) > threshold THEN 'double'
             ELSE 'ok' END
    END AS fee_status
  FROM base
)
"""


def _predicates(f: Dict[str, Any], skip: str | None = None) -> Tuple[List[str], List[Any]]:
    """Build WHERE fragments + params. `skip` omits one facet group (for faceting)."""
    where: List[str] = []
    params: List[Any] = []

    if f.get("q"):
        like = f"%{f['q'].lower()}%"
        where.append("(LOWER(make) LIKE ? OR LOWER(model) LIKE ? OR LOWER(COALESCE(trim,'')) LIKE ?)")
        params += [like, like, like]

    if skip != "powertrain" and f.get("powertrain"):
        vals = [_PT_MAP.get(str(v).lower()) for v in f["powertrain"] if _PT_MAP.get(str(v).lower())]
        if vals:
            where.append("powertrain_type IN (%s)" % ",".join("?" * len(vals)))
            params += vals

    if skip != "subtype" and f.get("subtype"):
        vals = list(f["subtype"])
        where.append("powertrain_subtype IN (%s)" % ",".join("?" * len(vals)))
        params += vals

    if skip != "drivetrain" and f.get("drivetrain"):
        vals = list(f["drivetrain"])
        where.append("drivetrain IN (%s)" % ",".join("?" * len(vals)))
        params += vals

    if f.get("weight_min") is not None:
        where.append("weight >= ?")
        params.append(f["weight_min"])
    if f.get("weight_max") is not None:
        where.append("weight <= ?")
        params.append(f["weight_max"])

    if f.get("weight_threshold") is not None and f.get("weight_cmp"):
        if f["weight_cmp"] == "above":
            where.append("weight > ?")
        else:
            where.append("weight <= ?")
        params.append(f["weight_threshold"])

    if skip != "fee" and f.get("fee"):
        vals = list(f["fee"])
        where.append("fee_status IN (%s)" % ",".join("?" * len(vals)))
        params += vals

    if not f.get("include_unknown_weight", True):
        where.append("weight IS NOT NULL")

    if skip != "model_year" and f.get("model_year"):
        vals = list(f["model_year"])
        where.append("model_year IN (%s)" % ",".join("?" * len(vals)))
        params += vals

    if f.get("min_confidence") is not None:
        where.append("(weight_confidence IS NULL OR weight_confidence >= ?)")
        params.append(f["min_confidence"])

    return where, params


def list_cars(conn: sqlite3.Connection, f: Dict[str, Any]) -> Dict[str, Any]:
    where, params = _predicates(f)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sort = _SORTS.get(f.get("sort", "make"), _SORTS["make"])
    page = max(1, int(f.get("page", 1)))
    page_size = min(200, max(1, int(f.get("page_size", 50))))
    offset = (page - 1) * page_size

    total = conn.execute(
        f"{_BASE_CTE} SELECT COUNT(*) FROM classified {where_sql}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"{_BASE_CTE} SELECT * FROM classified {where_sql} ORDER BY {sort} LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()

    return {"total": total, "page": page, "page_size": page_size,
            "items": [dict(r) for r in rows]}


def facets(conn: sqlite3.Connection, f: Dict[str, Any]) -> Dict[str, Any]:
    def grouped(col: str, skip: str):
        where, params = _predicates(f, skip=skip)
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        q = (f"{_BASE_CTE} SELECT {col} AS value, COUNT(*) AS count "
             f"FROM classified {where_sql} GROUP BY {col} ORDER BY count DESC")
        return [{"value": r["value"], "count": r["count"]}
                for r in conn.execute(q, params).fetchall() if r["value"] is not None]

    where, params = _predicates(f)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    bounds = conn.execute(
        f"{_BASE_CTE} SELECT MIN(weight) AS mn, MAX(weight) AS mx FROM classified {where_sql}",
        params,
    ).fetchone()

    # map powertrain_type back to UI labels for the powertrain facet
    pt = grouped("powertrain_type", "powertrain")
    label = {"BEV": "electric", "PHEV": "PHEV", "ICE": "ICE"}
    pt = [{"value": label.get(x["value"], x["value"]), "count": x["count"]} for x in pt]

    return {
        "powertrain": pt,
        "subtype": grouped("powertrain_subtype", "subtype"),
        "drivetrain": grouped("drivetrain", "drivetrain"),
        "fee_status": grouped("fee_status", "fee"),
        "model_year": grouped("model_year", "model_year"),
        "weight_bounds": {"min": bounds["mn"], "max": bounds["mx"]},
    }


def get_car(conn: sqlite3.Connection, car_id: int) -> Dict[str, Any] | None:
    row = conn.execute(
        f"{_BASE_CTE} SELECT * FROM classified WHERE id = ?", [car_id]
    ).fetchone()
    return dict(row) if row else None


def list_sql_for_export(f: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """Full filtered query (no pagination) for CSV export via pandas."""
    where, params = _predicates(f)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sort = _SORTS.get(f.get("sort", "make"), _SORTS["make"])
    cols = ("make, model, trim, powertrain_type, powertrain_subtype, drivetrain, power_kw, "
            "battery_kwh, model_year, weight, weight_min, weight_max, weight_unit, "
            "hu_weight_kg, n_sources, sources_agree, threshold, fee_status, "
            "weight_source, weight_source_url")
    return (f"{_BASE_CTE} SELECT {cols} FROM classified {where_sql} ORDER BY {sort}", params)
