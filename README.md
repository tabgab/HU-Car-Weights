# carWeights

A best-effort database + browser of cars on sale in the **Hungarian market**, classified
**BEV / PHEV / ICE** with **curb weight**, surfacing the **Budapest weight-based parking
surcharge** (effective 2027-01-01):

- **BEV** (fully electric) over **2000 kg** → pays double
- **ICE or PHEV** (anything with a combustion engine) over **1800 kg** → pays double

## Architecture

Two decoupled halves; the contract between them is the SQLite file `data/cars.db`
(schema in `carweights/db/schema.sql`, read by the app via the `v_parking_summary` view).

- **`carweights/`** — scraper pipeline: discover → fetch (cache + robots + rate-limit) →
  parse → normalize → classify (BEV/PHEV/ICE) → derive parking class → upsert, with
  per-field source + confidence provenance.
- **`app/`** — FastAPI backend (read-only SQLite) with filter/facet/detail/CSV endpoints.
- **`web/`** — no-build vanilla JS frontend (filter sidebar + results table + detail + CSV).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# JS-rendered sources (cars-data.com) need a browser engine:
.venv/bin/pip install -r requirements-scraping.txt
.venv/bin/python -m playwright install chromium
```

## Collect data

```bash
.venv/bin/python -m carweights.cli seed             # scrape config/seed_models.yaml
.venv/bin/python -m carweights.cli scrape <make> <model> --max-variants 8   # one model
.venv/bin/python -m carweights.cli derive           # recompute parking classification
.venv/bin/python -m carweights.cli stats            # coverage report
.venv/bin/python -m carweights.cli export           # data/exports/cars.csv
```

Expand coverage by adding entries to `config/seed_models.yaml` (cars-data.com slugs) and
re-running `seed` — the pipeline is idempotent and caches raw pages under `data/raw/`.

## Run the app

```bash
./run.sh           # http://127.0.0.1:8000
```

## Data sourcing — honest scope

There is **no single source** listing every HU-market car with curb weight per variant, so
data is assembled best-effort. The seed adapter scrapes **cars-data.com** (a Next.js app;
spec values come from its RSC payload, so a headless browser is used, politely, respecting
robots.txt and crawl-delay). Weights are tagged with source + confidence; variants with no
published weight are kept and flagged (`fee_status = unknown`). Curb weight is the EU/DIN
kerb figure; it varies by trim/options, so the app also shows the per-model range and flags
cars that **straddle** a threshold (some trims pay double, some don't).

## Tests

```bash
.venv/bin/python -m pytest tests/ -q
```
Covers the fee logic (BEV/PHEV/ICE thresholds, range straddle, boundaries), powertrain
classification edge cases (e-Power → ICE, e-tron → BEV, 4xe/Recharge → PHEV), and weight parsing.
