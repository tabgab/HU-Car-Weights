# Graph Report - .  (2026-06-09)

## Corpus Check
- Corpus is ~23,079 words - fits in a single context window. You may not need a graph.

## Summary
- 392 nodes · 726 edges · 26 communities (18 shown, 8 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 87 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_CLI Entry Points|CLI Entry Points]]
- [[_COMMUNITY_App Config & Read-DB Connection|App Config & Read-DB Connection]]
- [[_COMMUNITY_Authoritative Sources & DealerExtra-HU Scrapers|Authoritative Sources & Dealer/Extra-HU Scrapers]]
- [[_COMMUNITY_Settings, HTTP Fetch Utilities (cache, robots, polite)|Settings, HTTP Fetch Utilities (cache, robots, polite)]]
- [[_COMMUNITY_Weight Parsing & Units Normalization|Weight Parsing & Units Normalization]]
- [[_COMMUNITY_DB Repository  Idempotent Upserts|DB Repository / Idempotent Upserts]]
- [[_COMMUNITY_v2 Web UI (Policy Explorer, vanilla JS)|v2 Web UI (Policy Explorer, vanilla JS)]]
- [[_COMMUNITY_AndroidApp + SQLite contract (queries.py  v_parking_summary view)|AndroidApp + SQLite contract (queries.py / v_parking_summary view)]]
- [[_COMMUNITY_Fee Classifier (BEV 2000  ICE 1800)|Fee Classifier (BEV 2000 / ICE 1800)]]
- [[_COMMUNITY_Powertrain Classification (BEV  PHEV  HEV  MHEV  petrol  diesel)|Powertrain Classification (BEV / PHEV / HEV / MHEV / petrol / diesel)]]
- [[_COMMUNITY_Legacy Web UI (webapp.js)|Legacy Web UI (web/app.js)]]
- [[_COMMUNITY_Backup, Config, Shell Launchers|Backup, Config, Shell Launchers]]
- [[_COMMUNITY_uvicorn Launcher (run.sh)|uvicorn Launcher (run.sh)]]
- [[_COMMUNITY_DB_PATH constant|DB_PATH constant]]
- [[_COMMUNITY_DB Backup Refresh (refresh.sh)|DB Backup Refresh (refresh.sh)]]
- [[_COMMUNITY_v2 APIRouter mount point|v2 APIRouter mount point]]
- [[_COMMUNITY_fetch_log table|fetch_log table]]
- [[_COMMUNITY_provenance table|provenance table]]
- [[_COMMUNITY_schema_version table|schema_version table]]
- [[_COMMUNITY_Python Runtime Requirements|Python Runtime Requirements]]

## God Nodes (most connected - your core abstractions)
1. `$()` - 33 edges
2. `derive()` - 21 edges
3. `init_db()` - 19 edges
4. `$()` - 19 edges
5. `ingest_firstclass()` - 13 edges
6. `_store()` - 13 edges
7. `classify()` - 12 edges
8. `ingest_manual()` - 12 edges
9. `v_parking_summary view — flat row contract between scraper and FastAPI app (joins variants/models/makes/weights/parking_classification)` - 12 edges
10. `get_conn()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `test_range_cases (straddle/over/under for ICE+BEV)` --semantically_similar_to--> `derive()`  [INFERRED] [semantically similar]
  tests/test_fees.py → carweights/pipeline/derive.py
- `test_representative_value_cases (BEV 2100→double, ICE 1700→ok, etc.)` --semantically_similar_to--> `derive()`  [INFERRED] [semantically similar]
  tests/test_fees.py → carweights/pipeline/derive.py
- `crawl_brand()` --shares_data_with--> `Hungarian dealer source URLs (dealer_sources.yaml)`  [INFERRED]
  carweights/scrape/manufacturer_crawl.py → config/dealer_sources.yaml
- `get_conn()` --implements--> `Two decoupled halves (scraper + app) communicate only via the SQLite file contract (v_parking_summary view)`  [INFERRED]
  app/db.py → README.md
- `classify()` --semantically_similar_to--> `classify()`  [INFERRED] [semantically similar]
  app/fees.py → carweights/normalize/powertrain.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Hungarian PDF ingestion flow (all funnel into manufacturer_pdf.ingest)** — scrape_extra_hu_manual_pdf_records, scrape_omodajaecoo_crawl, scrape_chery_crawl, scrape_manufacturer_crawl_crawl_brand, scrape_manufacturer_pdf_ingest [INFERRED 0.85]
- **Powertrain classifier family (multiple input sources, common BEV/PHEV/ICE output)** — normalize_powertrain_classify, scrape_manufacturer_pdf_powertrain_from_text, scrape_katalogus_hu_powertrain_from_fuel, scrape_katalogus_hu_powertrain_from [INFERRED 0.85]
- **Fee threshold values propagated across backend constants, API hardcoding, and frontend display** — app_fees_threshold_bev, app_fees_threshold_combustion, app_routes_car_detail, web_index_html, budapest_parking_fee_rule [INFERRED 0.85]
- **Polite fetching layer (cache + robots + backoff + CF-bypass variants)** — fetch_http_get, fetch_dynamic_render, fetch_dynamic_render_stealth, fetch_hu_fast_get, fetch_cache_read, fetch_cache_write, fetch_robots_allowed, fetch_robots_wait, fetch_robots_crawl_delay [INFERRED 0.95]
- **Parking-fee threshold classification (canonical + two mirrors)** — app_v2_api_classify_row, app_v2_api_policy, pipeline_derive_derive, pipeline_derive_threshold, carweights_settings_threshold_bev, carweights_settings_threshold_combustion, app_config_thresholds, concept_hungarian_parking_fee [INFERRED 0.95]
- **HU-catalog ingestion chain (katalogus → hu_catalog → variants → derive)** — carweights_cli_cmd_hu, pipeline_hu_scrape_make_hu, pipeline_hu_ingest_firstclass, pipeline_hu_crosscheck, db_repository_upsert_hu_catalog, pipeline_derive_derive, fetch_hu_fast_get, fetch_dynamic_render_stealth [INFERRED 0.85]
- **Web v2 Policy Explorer (BEV/ICE sliders → debounced /api/v2/policy → fleet outcome bar + 5/10/25% border buckets)** — v2_index_html, v2_app_js, v2_app_js_runpolicy, v2_app_js_renderoutcome, v2_app_js_classifyclient, v2_styles_css [EXTRACTED 1.00]
- **v_parking_summary as the read contract between scraper (schema owner) and FastAPI app (queries.read)** — db_schema_sql_v_parking_summary, app_queries_base_cte, app_queries_list_cars, app_queries_facets, app_queries_get_car, app_queries_list_sql_for_export [EXTRACTED 1.00]
- **Fee threshold values (BEV=2000, ICE/PHEV=1800) propagated across: app.fees constants, queries.base_cte CASE, web v1 header, web v2 sliders + classifyClient** — app_fees_threshold_bev, app_fees_threshold_combustion, app_queries_base_cte, web_index_html, v2_index_html, v2_app_js_classifyclient, budapest_parking_fee_rule [INFERRED 0.85]

## Communities (26 total, 8 thin omitted)

### Community 0 - "CLI Entry Points"
Cohesion: 0.08
Nodes (47): cmd_chery(), cmd_dealer(), cmd_derive(), cmd_export(), cmd_extra_hu(), cmd_firstclass(), cmd_hu(), cmd_hu_pdf() (+39 more)

### Community 1 - "App Config & Read-DB Connection"
Cohesion: 0.07
Nodes (35): App configuration: DB path + thresholds., THRESHOLDS dict (BEV/ICE/PHEV), get_conn(), Connection, Read-only SQLite access for the app., FastAPI app instance, Path, carWeights FastAPI app: JSON API under /api + /api/v2 + static frontend at /.  T (+27 more)

### Community 2 - "Authoritative Sources & Dealer/Extra-HU Scrapers"
Cohesion: 0.08
Nodes (33): Authoritative source tiering (manufacturer PDF 0.97 > katalogus.hu 0.95 > cars-data 0.8), Zeekr 7GT product leaflet PDF (BEV), Zeekr 7X product leaflet PDF (BEV), crawl(), _fetch_pricelist_url(), cherymotors.hu — Chery Hungary importer.  The site is a React SPA backed by a pu, Return (pdf_url, original_filename) for the 'Árlista' document of a car type., Return ingest_manual records for all Chery HU models.      Each record has {make (+25 more)

### Community 3 - "Settings, HTTP Fetch Utilities (cache, robots, polite)"
Cohesion: 0.10
Nodes (33): Path, Central paths and constants for the carWeights scraper package., USER_AGENT constant, Solve-once Cloudflare bypass (clearance cookie reuse), Polite fetching: cache-first + robots-aware + retry/backoff, Exception, cache_path(), _key() (+25 more)

### Community 4 - "Weight Parsing & Units Normalization"
Cohesion: 0.08
Nodes (35): normalize_drivetrain(), detect_basis(), parse_weight(), Parse messy weight strings into integer kilograms., Normalize a single numeric token (may contain . , spaces as thousands) to kg int, Return (representative, min, max) in kg.      - "1450"            -> (1450, None, Classify the weight basis from surrounding label text., _to_int_kg() (+27 more)

### Community 5 - "DB Repository / Idempotent Upserts"
Cohesion: 0.12
Nodes (30): Connection, Connection, Variant fingerprinting for idempotent upserts, add_provenance(), Idempotent upsert helpers. All writes converge on natural/fingerprint keys., slugify(), upsert_make(), upsert_model() (+22 more)

### Community 6 - "v2 Web UI (Policy Explorer, vanilla JS)"
Cohesion: 0.08
Nodes (20): $(), classifyClient(), closeDetail(), esc(), fetchNearby(), fmt(), FONT_SCALES, openDetail() (+12 more)

### Community 7 - "AndroidApp + SQLite contract (queries.py / v_parking_summary view)"
Cohesion: 0.13
Nodes (27): Android Kotlin + Jetpack Compose client (bundles cars.db; mirrors Policy Explorer UX; four screens), Any, base_cte(), facets(), get_car(), list_cars(), list_sql_for_export(), _predicates() (+19 more)

### Community 8 - "Fee Classifier (BEV 2000 / ICE 1800)"
Cohesion: 0.21
Nodes (18): classify(), Budapest parking-fee classification — the single source of truth for the app.  R, Return 'ok' | 'double' | 'borderline' | 'unknown'., THRESHOLD_BEV constant (2000 kg), THRESHOLD_COMBUSTION constant (1800 kg), threshold_for(), car_detail(), Budapest parking fee rule (2027): BEV>2000kg or ICE/PHEV>1800kg pays double (+10 more)

### Community 9 - "Powertrain Classification (BEV / PHEV / HEV / MHEV / petrol / diesel)"
Cohesion: 0.19
Nodes (16): classify(), _has(), _has_token_ev(), PowertrainResult, Classify a car variant into BEV / PHEV / ICE from fuel/name signals.  Ordered ru, Powertrain classification (BEV/PHEV/ICE bucketing — HEV folds into ICE for fee purposes), t(), test_bev_from_battery_only() (+8 more)

### Community 10 - "Legacy Web UI (web/app.js)"
Cohesion: 0.18
Nodes (17): $(), buildParams(), countEl, emptyEl, facetGroup(), FEE_LABEL, feeBadge(), openDetail() (+9 more)

### Community 11 - "Backup, Config, Shell Launchers"
Cohesion: 0.20
Nodes (10): Backup README — restore procedure (gunzip -c backups/cars.db.gz > data/cars.db) + commands that regenerate the DB, refresh.sh — gzip data/cars.db → backups/cars.db.gz (re-snapshot the current DB), Make/model alias config (aliases.yaml), Hungarian dealer source URLs (dealer_sources.yaml), Top-20 HU market makes (makes_hu.yaml), Seed models for cars-data pipeline (seed_models.yaml), Idempotent scraper pipeline (re-runs converge; raw pages cached under data/raw/), Changan Deepal S07 product brochure (BEV/PHEV, German) — manual HU-market source for a Chinese brand (+2 more)

## Knowledge Gaps
- **35 isolated node(s):** `Connection`, `Path`, `refresh.sh script`, `Connection`, `VariantRecord` (+30 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `derive()` connect `CLI Entry Points` to `App Config & Read-DB Connection`?**
  _High betweenness centrality (0.176) - this node is a cross-community bridge._
- **Why does `policy()` connect `App Config & Read-DB Connection` to `CLI Entry Points`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Why does `classify()` connect `Powertrain Classification (BEV / PHEV / HEV / MHEV / petrol / diesel)` to `Fee Classifier (BEV 2000 / ICE 1800)`, `Authoritative Sources & Dealer/Extra-HU Scrapers`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `derive()` (e.g. with `_classify_row()` and `policy()`) actually correct?**
  _`derive()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `App configuration: DB path + thresholds.`, `Connection`, `Read-only SQLite access for the app.` to the rest of the system?**
  _107 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CLI Entry Points` be split into smaller, more focused modules?**
  _Cohesion score 0.08295625942684766 - nodes in this community are weakly interconnected._
- **Should `App Config & Read-DB Connection` be split into smaller, more focused modules?**
  _Cohesion score 0.06755260243632337 - nodes in this community are weakly interconnected._