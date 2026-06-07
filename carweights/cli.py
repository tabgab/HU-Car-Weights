"""carWeights CLI: seed | scrape | derive | export | stats."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .db.connection import connect, init_db
from .pipeline.derive import derive
from .pipeline.run import run_market, run_seed, scrape_model
from .settings import CONFIG_DIR, EXPORT_DIR


def _load_seeds() -> list[dict]:
    path = CONFIG_DIR / "seed_models.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("models", [])


def _load_makes() -> list[str]:
    path = CONFIG_DIR / "makes_hu.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("makes", [])


def cmd_market(args):
    conn = init_db()
    total = run_market(conn, _load_makes(), max_models=args.max_models,
                       max_variants=args.max_variants, min_year=args.min_year)
    print("\n=== market scrape complete ===")
    print(total)
    conn.close()


def cmd_seed(args):
    conn = init_db()
    total = run_seed(conn, _load_seeds(), max_variants=args.max_variants)
    print("\n=== seed complete ===")
    print(total)
    conn.close()


def cmd_scrape(args):
    conn = init_db()
    st = scrape_model(conn, args.make, args.model,
                      max_generations=args.max_generations, max_variants=args.max_variants)
    print(st)
    derive(conn)
    conn.close()


def cmd_hu(args):
    from .pipeline.hu import scrape_make_hu, crosscheck
    conn = init_db()
    makes = args.makes.split(",") if args.makes else _load_makes()
    for mk in makes:
        st = scrape_make_hu(conn, mk.strip(), max_variants=args.max_variants,
                            per_model=args.per_model, model_filter=not args.full)
        print(f"  = HU {mk}: {st}", flush=True)
    print("cross-check:", crosscheck(conn))
    print("re-derive:", derive(conn))
    conn.close()


def cmd_dealer(args):
    """Crawl manufacturer/dealer HU spec PDFs (authoritative) -> hu_catalog + cross-check."""
    import yaml
    from .scrape import manufacturer_crawl as MC
    from .pipeline.hu import crosscheck, _ascii
    from .db import repository as R
    if args.brand and args.page:
        brands = {args.brand: args.page}
    else:
        conf = yaml.safe_load((CONFIG_DIR / "dealer_sources.yaml").read_text(encoding="utf-8")) or {}
        brands = conf.get("brands", {})
        if args.brand:
            brands = {args.brand: brands[args.brand]}
    conn = connect()  # schema already exists; avoid DDL while katalogus crawl writes
    total = 0
    for brand, page in brands.items():
        for res in MC.crawl_brand(brand, page):
            mk, md = _ascii(brand), _ascii(res["model"])
            for i, kg in enumerate(sorted(set(res["weights"]))):
                R.upsert_hu_catalog(conn, mk, md, f"{md}_dealer{i}", None, None, kg,
                                    res["source_url"] + f"#{i}")
                total += 1
        conn.commit()
    print(f"ingested {total} manufacturer weight rows")
    try:
        print("cross-check:", crosscheck(conn))
        print("re-derive:", derive(conn))
    except Exception as e:
        print(f"cross-check/derive deferred (DB busy: {e}); will be recomputed by the "
              f"katalogus crawl's final pass or `cli derive`.")
    conn.close()


def cmd_hu_pdf(args):
    """Ingest a manufacturer HU brochure PDF to fill a katalogus gap."""
    from .scrape import manufacturer_pdf as M
    from .pipeline.hu import crosscheck, _ascii
    from .db import repository as R
    res = M.ingest(args.make, args.model, args.pdf_url)
    print(f"extracted {len(res['weights'])} weight figures from {args.pdf_url}")
    for ctx, kg, pg in res["rows"][:15]:
        print(f"  p{pg}: {kg} kg  | {ctx}")
    if not res["weights"]:
        print("no 'Saját tömeg' rows found — check the PDF.")
        return
    conn = init_db()
    mk, md = _ascii(args.make), _ascii(args.model)
    for i, kg in enumerate(sorted(set(res["weights"]))):
        url = f"{args.pdf_url}#{md}-{i}"
        R.upsert_hu_catalog(conn, mk, f"{md}_pdf{i}", f"{md}_pdf{i}", None, None, kg, url)
    conn.commit()
    print("cross-check:", crosscheck(conn))
    print("re-derive:", derive(conn))
    conn.close()


def cmd_derive(args):
    conn = init_db()
    print(derive(conn))
    conn.close()


def cmd_stats(args):
    conn = init_db()
    n_makes = conn.execute("SELECT COUNT(*) FROM makes").fetchone()[0]
    n_models = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
    n_var = conn.execute("SELECT COUNT(*) FROM variants").fetchone()[0]
    n_w = conn.execute("SELECT COUNT(*) FROM weights WHERE curb_weight_kg IS NOT NULL "
                       "OR curb_weight_min_kg IS NOT NULL").fetchone()[0]
    by_pt = conn.execute("SELECT powertrain_type, COUNT(*) FROM variants GROUP BY powertrain_type").fetchall()
    by_fee = conn.execute("SELECT fee_status, COUNT(*) FROM parking_classification GROUP BY fee_status").fetchall()
    print(f"makes={n_makes} models={n_models} variants={n_var}")
    cov = (100.0 * n_w / n_var) if n_var else 0.0
    print(f"weight coverage: {n_w}/{n_var} ({cov:.1f}%)")
    print("by powertrain:", {r[0]: r[1] for r in by_pt})
    print("by fee_status:", {r[0]: r[1] for r in by_fee})
    conn.close()


def cmd_export(args):
    import pandas as pd
    conn = init_db()
    df = pd.read_sql_query("SELECT * FROM v_parking_summary ORDER BY make, model", conn)
    out = EXPORT_DIR / "cars.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} rows)")
    conn.close()


def main(argv=None):
    p = argparse.ArgumentParser(prog="carweights")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seed", help="scrape all models in config/seed_models.yaml")
    s.add_argument("--max-variants", type=int, default=8)
    s.set_defaults(func=cmd_seed)

    s = sub.add_parser("scrape", help="scrape one make/model (cars-data slugs)")
    s.add_argument("make"); s.add_argument("model")
    s.add_argument("--max-generations", type=int, default=1)
    s.add_argument("--max-variants", type=int, default=8)
    s.set_defaults(func=cmd_scrape)

    s = sub.add_parser("market", help="discover+scrape all current models of the top-20 makes")
    s.add_argument("--max-models", type=int, default=None, help="cap models per make")
    s.add_argument("--max-variants", type=int, default=3)
    s.add_argument("--min-year", type=int, default=2018)
    s.set_defaults(func=cmd_market)

    s = sub.add_parser("hu", help="scrape Hungarian catalog (katalogus.hasznaltauto.hu) + cross-check")
    s.add_argument("--makes", default=None, help="comma-separated brand slugs (default: all)")
    s.add_argument("--max-variants", type=int, default=None, help="cap HU variants per make")
    s.add_argument("--per-model", type=int, default=3, help="cap variants per model+powertrain")
    s.add_argument("--full", action="store_true",
                   help="scrape ALL catalog variants (no model filter / per-model cap)")
    s.set_defaults(func=cmd_hu)

    s = sub.add_parser("dealer", help="crawl manufacturer/dealer HU spec PDFs (config/dealer_sources.yaml)")
    s.add_argument("--brand", default=None, help="single brand slug")
    s.add_argument("--page", default=None, help="override spec-listing page URL")
    s.set_defaults(func=cmd_dealer)

    s = sub.add_parser("hu-pdf", help="ingest a manufacturer HU brochure PDF (gap-filler)")
    s.add_argument("make"); s.add_argument("model"); s.add_argument("pdf_url")
    s.set_defaults(func=cmd_hu_pdf)

    sub.add_parser("derive", help="recompute parking classification").set_defaults(func=cmd_derive)
    sub.add_parser("stats", help="coverage stats").set_defaults(func=cmd_stats)
    sub.add_parser("export", help="export v_parking_summary to CSV").set_defaults(func=cmd_export)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
