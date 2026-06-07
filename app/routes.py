"""REST API: /api/cars, /api/facets, /api/cars/{id}, /api/cars.csv"""
from __future__ import annotations

import io
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response

from . import queries
from .config import THRESHOLDS
from .db import get_conn

router = APIRouter()

# UI powertrain label -> human category passthrough for responses
_CATEGORY = {"BEV": "electric", "PHEV": "PHEV", "ICE": "ICE"}


def _collect_filters(
    q, powertrain, subtype, drivetrain, weight_min, weight_max,
    weight_threshold, weight_cmp, fee, include_unknown_weight, model_year,
    min_confidence, sort, page, page_size, hu_only=False,
):
    return {
        "q": q,
        "powertrain": powertrain,
        "subtype": subtype,
        "drivetrain": drivetrain,
        "weight_min": weight_min,
        "weight_max": weight_max,
        "weight_threshold": weight_threshold,
        "weight_cmp": weight_cmp,
        "fee": fee,
        "include_unknown_weight": include_unknown_weight,
        "model_year": model_year,
        "min_confidence": min_confidence,
        "sort": sort,
        "page": page,
        "page_size": page_size,
        "hu_only": hu_only,
    }


def _enrich(item: dict) -> dict:
    item["powertrain_category"] = _CATEGORY.get(item.get("powertrain_type"), item.get("powertrain_type"))
    return item


@router.get("/cars")
def list_cars(
    q: Optional[str] = None,
    powertrain: Optional[List[str]] = Query(None),
    subtype: Optional[List[str]] = Query(None),
    drivetrain: Optional[List[str]] = Query(None),
    weight_min: Optional[int] = None,
    weight_max: Optional[int] = None,
    weight_threshold: Optional[int] = None,
    weight_cmp: Optional[str] = Query(None, pattern="^(above|below)$"),
    fee: Optional[List[str]] = Query(None),
    include_unknown_weight: bool = True,
    model_year: Optional[List[int]] = Query(None),
    min_confidence: Optional[float] = None,
    sort: str = "make",
    page: int = 1,
    page_size: int = 50,
    hu_only: bool = False,
):
    f = _collect_filters(q, powertrain, subtype, drivetrain, weight_min, weight_max,
                         weight_threshold, weight_cmp, fee, include_unknown_weight,
                         model_year, min_confidence, sort, page, page_size, hu_only)
    conn = get_conn()
    try:
        res = queries.list_cars(conn, f)
    finally:
        conn.close()
    res["items"] = [_enrich(i) for i in res["items"]]
    res["thresholds"] = THRESHOLDS
    return res


@router.get("/facets")
def facets(
    q: Optional[str] = None,
    powertrain: Optional[List[str]] = Query(None),
    subtype: Optional[List[str]] = Query(None),
    drivetrain: Optional[List[str]] = Query(None),
    weight_min: Optional[int] = None,
    weight_max: Optional[int] = None,
    weight_threshold: Optional[int] = None,
    weight_cmp: Optional[str] = Query(None, pattern="^(above|below)$"),
    fee: Optional[List[str]] = Query(None),
    include_unknown_weight: bool = True,
    model_year: Optional[List[int]] = Query(None),
    min_confidence: Optional[float] = None,
    hu_only: bool = False,
):
    f = _collect_filters(q, powertrain, subtype, drivetrain, weight_min, weight_max,
                         weight_threshold, weight_cmp, fee, include_unknown_weight,
                         model_year, min_confidence, "make", 1, 50, hu_only)
    conn = get_conn()
    try:
        return queries.facets(conn, f)
    finally:
        conn.close()


@router.get("/cars/{car_id}")
def car_detail(car_id: int, hu_only: bool = False):
    conn = get_conn()
    try:
        row = queries.get_car(conn, car_id, hu_only)
    finally:
        conn.close()
    if not row:
        return JSONResponse({"error": "not found"}, status_code=404)
    row = _enrich(row)
    pt = row.get("powertrain_type")
    thr = 2000 if pt == "BEV" else 1800
    rule = (f"{'BEV' if pt=='BEV' else (pt or 'Combustion')} over {thr} kg pays double "
            f"Budapest parking fee")
    row["fee"] = {"threshold": thr, "status": row.get("fee_status"), "rule": rule,
                  "stored_classification": row.get("db_fee_status")}
    return row


@router.get("/cars.csv")
def export_csv(
    q: Optional[str] = None,
    powertrain: Optional[List[str]] = Query(None),
    subtype: Optional[List[str]] = Query(None),
    drivetrain: Optional[List[str]] = Query(None),
    weight_min: Optional[int] = None,
    weight_max: Optional[int] = None,
    weight_threshold: Optional[int] = None,
    weight_cmp: Optional[str] = Query(None, pattern="^(above|below)$"),
    fee: Optional[List[str]] = Query(None),
    include_unknown_weight: bool = True,
    model_year: Optional[List[int]] = Query(None),
    min_confidence: Optional[float] = None,
    sort: str = "make",
    hu_only: bool = False,
):
    f = _collect_filters(q, powertrain, subtype, drivetrain, weight_min, weight_max,
                         weight_threshold, weight_cmp, fee, include_unknown_weight,
                         model_year, min_confidence, sort, 1, 10 ** 9, hu_only)
    sql, params = queries.list_sql_for_export(f)
    conn = get_conn()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="cars_export.csv"'},
    )
