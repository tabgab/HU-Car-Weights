"""Recompute the parking_classification table from current weights.

Deterministic full recompute (idempotent). Mirrors app/fees.py:
  over -> double, under -> ok, straddling -> borderline, unknown -> unknown.
"""
from __future__ import annotations

import sqlite3

from ..settings import THRESHOLD_BEV, THRESHOLD_COMBUSTION


def _threshold(powertrain_type: str) -> int:
    return THRESHOLD_BEV if powertrain_type == "BEV" else THRESHOLD_COMBUSTION


def derive(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        """SELECT v.variant_id, v.powertrain_type,
                  w.curb_weight_kg, w.curb_weight_min_kg, w.curb_weight_max_kg
           FROM variants v
           LEFT JOIN weights w ON w.variant_id = v.variant_id"""
    ).fetchall()

    counts = {"under": 0, "over": 0, "straddling": 0, "unknown": 0}
    conn.execute("DELETE FROM parking_classification")
    for r in rows:
        pt = r["powertrain_type"]
        t = _threshold(pt)
        fee_class = "BEV" if pt == "BEV" else "COMBUSTION"
        w = r["curb_weight_kg"]
        lo = r["curb_weight_min_kg"] if r["curb_weight_min_kg"] is not None else w
        hi = r["curb_weight_max_kg"] if r["curb_weight_max_kg"] is not None else w

        if lo is None and hi is None:
            status, pays = "unknown", None
        elif lo is not None and hi is not None and lo != hi:
            if lo > t:
                status, pays = "over", 1
            elif hi <= t:
                status, pays = "under", 0
            else:
                status, pays = "straddling", None
        else:
            rep = w if w is not None else (lo if lo is not None else hi)
            if rep is None:
                status, pays = "unknown", None
            elif rep > t:
                status, pays = "over", 1
            else:
                status, pays = "under", 0

        counts[status] += 1
        conn.execute(
            """INSERT INTO parking_classification(variant_id, fee_class, threshold_kg,
                       decision_kg, fee_status, pays_double)
               VALUES(?,?,?,?,?,?)""",
            (r["variant_id"], fee_class, t, w, status, pays),
        )
    conn.commit()
    counts["total"] = len(rows)
    return counts
