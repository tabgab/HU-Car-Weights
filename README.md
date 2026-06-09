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

## Android app (`android/`, on branch `AndroidApp`)

A native Kotlin + Jetpack Compose client that ships the same `cars.db` SQLite inside the APK
and reads it read-only against `v_parking_summary`. Four screens, three of them powered by
the fee classifier; the headline feature is a **Policy Explorer**.

- **Policy Explorer** — drag the BEV and ICE/PHEV thresholds, see in real time how many cars
  in the fleet pay double, plus a *border-cases* list of cars paying double within 5/10/25%
  of the threshold. The main benefit: helps reason about the threshold policy.
- **Lookup** — pick powertrain + weight, get the verdict + rule.
- **Browse** — search + paginated list with fee status pills (uses the bundled DB).
- **Settings** — text-size slider, HU-only toggle, refresh (future), about.

Build: `cd android && ./gradlew :app:assembleDebug` → `app/build/outputs/apk/debug/app-debug.apk`.
Unit tests: `./gradlew :app:testDebugUnitTest` (mirrors `tests/test_fees.py` 1:1).

## Web v2 UI (`web/v2/`)

A second web UI that mirrors the Android app's Policy Explorer UX in vanilla JS +
dark theme. Reach it at **[/v2/](http://127.0.0.1:8000/v2/)** (the legacy SPA at `/` has a
"📱 AndroidApp UI" button in the top-bar that switches over).

Backed by `GET /api/v2/policy?bev=N&ice=N&pt=BEV,PHEV&make=Skoda,VW&hu_only=true` — a
single server-side endpoint that returns the fleet outcome + border cases for any
user-set thresholds + filters in one round-trip. Reuses the existing classifier
logic in `app/fees.py` (single source of truth).

Settings (font size, HU-only) persist via `localStorage`.
