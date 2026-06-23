#!/usr/bin/env python3
"""Export the full fleet from cars.db to a compact static JSON for the browser.

The static GitHub Pages site reads this file instead of calling the FastAPI backend.
It carries every column both UIs need; the JS port (docs/assets/carquery.js) does the
filtering / faceting / classification client-side.

Usage:
    python3 scripts/export_cars_json.py [OUTPUT]
Default OUTPUT: docs/cars.json

Read-only against the DB. Re-run + commit whenever data/cars.db changes.
"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("CARWEIGHTS_DB", os.path.join(ROOT, "data", "cars.db"))
DEFAULT_OUT = os.path.join(ROOT, "docs", "cars.json")

# Superset of the fields the two UIs need. Mirrors app/queries.py _PROJECT (minus the
# never-displayed hu_weight_url) plus on_sale_hu (used by /api/v2/policy, not in the view).
COLUMNS = [
    "id", "make", "model", "trim", "powertrain_type", "powertrain_subtype",
    "drivetrain", "power_kw", "battery_kwh", "model_year", "source",
    "weight", "weight_min", "weight_max", "weight_unit", "is_missing", "on_sale_hu",
    "hu_weight_kg", "n_sources", "sources_agree", "primary_source",
    "weight_source", "weight_source_url",
]

SQL = """
SELECT vp.id, vp.make, vp.model, vp.trim, vp.powertrain_type, vp.powertrain_subtype,
       vp.drivetrain, vp.power_kw, vp.battery_kwh, vp.model_year, vp.source,
       vp.weight, vp.weight_min, vp.weight_max, vp.weight_unit, vp.is_missing,
       v.on_sale_hu, vp.hu_weight_kg, vp.n_sources, vp.sources_agree,
       vp.primary_source, vp.weight_source, vp.weight_source_url
FROM v_parking_summary vp
JOIN variants v ON v.variant_id = vp.id
ORDER BY vp.id
"""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(SQL).fetchall()
    finally:
        conn.close()

    records = [{c: r[c] for c in COLUMNS} for r in rows]

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        # minified; ensure_ascii=False keeps accented makes (Škoda) compact + readable
        json.dump(records, f, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(out)
    print(f"Wrote {len(records)} cars -> {out} ({size//1024} KB)")
    # quick sanity counts
    by_pt = {}
    for r in records:
        by_pt[r["powertrain_type"]] = by_pt.get(r["powertrain_type"], 0) + 1
    print("  by powertrain:", by_pt)


if __name__ == "__main__":
    main()
