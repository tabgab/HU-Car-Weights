-- carWeights canonical schema. The SQLite file built from this is the contract
-- consumed by the FastAPI app (which reads it read-only, primarily via v_parking_summary).
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS makes (
    make_id        INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    slug           TEXT NOT NULL UNIQUE,
    on_sale_hu     INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS models (
    model_id        INTEGER PRIMARY KEY,
    make_id         INTEGER NOT NULL REFERENCES makes(make_id) ON DELETE CASCADE,
    canonical_name  TEXT NOT NULL,
    slug            TEXT NOT NULL,
    body_type       TEXT,
    model_year_from INTEGER,
    model_year_to   INTEGER,
    on_sale_hu      INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (make_id, slug)
);
CREATE INDEX IF NOT EXISTS ix_models_make ON models(make_id);

CREATE TABLE IF NOT EXISTS variants (
    variant_id         INTEGER PRIMARY KEY,
    model_id           INTEGER NOT NULL REFERENCES models(model_id) ON DELETE CASCADE,
    trim_name          TEXT,
    powertrain_type    TEXT NOT NULL CHECK (powertrain_type IN ('BEV','PHEV','ICE')),
    powertrain_subtype TEXT CHECK (powertrain_subtype IN
                          ('petrol','diesel','MHEV','HEV','PHEV','BEV')),
    drivetrain         TEXT CHECK (drivetrain IN ('2WD','4WD')),
    power_kw           INTEGER,
    battery_kwh        REAL,
    model_year         INTEGER,
    on_sale_hu         INTEGER NOT NULL DEFAULT 1,
    fingerprint        TEXT NOT NULL,
    created_at         TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (model_id, fingerprint)
);
CREATE INDEX IF NOT EXISTS ix_variants_model ON variants(model_id);
CREATE INDEX IF NOT EXISTS ix_variants_ptype ON variants(powertrain_type);

CREATE TABLE IF NOT EXISTS weights (
    weight_id          INTEGER PRIMARY KEY,
    variant_id         INTEGER NOT NULL REFERENCES variants(variant_id) ON DELETE CASCADE,
    unit               TEXT NOT NULL DEFAULT 'kg' CHECK (unit = 'kg'),
    curb_weight_kg     INTEGER,
    curb_weight_min_kg INTEGER,
    curb_weight_max_kg INTEGER,
    weight_basis       TEXT CHECK (weight_basis IN
                          ('curb','mass_in_running_order','dry','unknown')),
    is_missing         INTEGER NOT NULL DEFAULT 0,
    -- cross-source fields (populated by pipeline/crosscheck.py)
    hu_weight_kg       INTEGER,        -- authoritative HU-catalog curb weight (saját tömeg)
    hu_weight_url      TEXT,
    n_sources          INTEGER NOT NULL DEFAULT 1,
    sources_agree      INTEGER,        -- 1 agree, 0 conflict, NULL single-source/unknown
    primary_source     TEXT,           -- the source whose value is canonical
    created_at         TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (variant_id)
);

-- Hungarian-market catalog (katalogus.hasznaltauto.hu). Authoritative HU source.
CREATE TABLE IF NOT EXISTS hu_catalog (
    hu_id           INTEGER PRIMARY KEY,
    make_slug       TEXT NOT NULL,
    model_slug      TEXT NOT NULL,
    variant_slug    TEXT NOT NULL,
    powertrain_type TEXT,
    drivetrain      TEXT,
    weight_kg       INTEGER,
    source_url      TEXT NOT NULL UNIQUE,
    scraped_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_hu_make_model ON hu_catalog(make_slug, model_slug);

CREATE TABLE IF NOT EXISTS provenance (
    provenance_id  INTEGER PRIMARY KEY,
    entity_type    TEXT NOT NULL CHECK (entity_type IN ('make','model','variant','weight')),
    entity_id      INTEGER NOT NULL,
    field          TEXT NOT NULL,
    value_text     TEXT,
    source_name    TEXT NOT NULL,
    source_url     TEXT,
    confidence     REAL NOT NULL DEFAULT 0.5,
    scraped_at     TEXT NOT NULL DEFAULT (datetime('now')),
    raw_cache_path TEXT,
    UNIQUE (entity_type, entity_id, field, source_name)
);
CREATE INDEX IF NOT EXISTS ix_prov_entity ON provenance(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS fetch_log (
    fetch_id     INTEGER PRIMARY KEY,
    url          TEXT NOT NULL,
    source_name  TEXT NOT NULL,
    http_status  INTEGER,
    cache_path   TEXT,
    fetched_at   TEXT NOT NULL DEFAULT (datetime('now')),
    etag         TEXT,
    content_hash TEXT
);
CREATE INDEX IF NOT EXISTS ix_fetch_url ON fetch_log(url);

CREATE TABLE IF NOT EXISTS parking_classification (
    variant_id   INTEGER PRIMARY KEY REFERENCES variants(variant_id) ON DELETE CASCADE,
    fee_class    TEXT NOT NULL CHECK (fee_class IN ('BEV','COMBUSTION')),
    threshold_kg INTEGER NOT NULL,
    decision_kg  INTEGER,
    fee_status   TEXT NOT NULL CHECK (fee_status IN ('under','over','straddling','unknown')),
    pays_double  INTEGER,
    computed_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- min/max curb weight across a model's trims (the "range")
CREATE VIEW IF NOT EXISTS v_model_weight_range AS
SELECT v.model_id,
       MIN(COALESCE(w.curb_weight_min_kg, w.curb_weight_kg)) AS model_min_kg,
       MAX(COALESCE(w.curb_weight_max_kg, w.curb_weight_kg)) AS model_max_kg,
       CAST(AVG(w.curb_weight_kg) AS INTEGER)                AS model_repr_kg,
       COUNT(w.curb_weight_kg)                               AS n_known,
       COUNT(*)                                              AS n_variants
FROM variants v
LEFT JOIN weights w ON w.variant_id = v.variant_id
GROUP BY v.model_id;

-- flat row the FastAPI app reads
DROP VIEW IF EXISTS v_parking_summary;
CREATE VIEW v_parking_summary AS
SELECT v.variant_id                                AS id,
       mk.canonical_name                           AS make,
       md.canonical_name                           AS model,
       v.trim_name                                 AS trim,
       v.powertrain_type,
       v.powertrain_subtype,
       v.drivetrain,
       v.power_kw,
       v.battery_kwh,
       v.model_year,
       w.curb_weight_kg                            AS weight,
       w.curb_weight_min_kg                        AS weight_min,
       w.curb_weight_max_kg                        AS weight_max,
       w.unit                                      AS weight_unit,
       w.is_missing,
       w.hu_weight_kg,
       w.hu_weight_url,
       w.n_sources,
       w.sources_agree,
       w.primary_source,
       pc.fee_class,
       pc.threshold_kg,
       pc.decision_kg,
       pc.fee_status   AS db_fee_status,
       pc.pays_double  AS db_pays_double,
       w.primary_source                            AS weight_source,
       w.hu_weight_url                             AS weight_source_url
FROM variants v
JOIN models md ON md.model_id = v.model_id
JOIN makes  mk ON mk.make_id = md.make_id
LEFT JOIN weights w  ON w.variant_id = v.variant_id
LEFT JOIN parking_classification pc ON pc.variant_id = v.variant_id;
