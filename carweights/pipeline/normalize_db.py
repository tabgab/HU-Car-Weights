"""Re-apply name canonicalization (config/aliases.yaml) to rows already in the DB.

Canonical names are stamped at scrape time, so additions to the alias map only
affect future rows. This pass recomputes canonical_name for every make and model,
renaming in place and merging rows that collapse to the same canonical name
(variants are repointed; true duplicates — same model + fingerprint — are dropped).
Idempotent: a second run is a no-op.
"""
from __future__ import annotations

import sqlite3

from ..db.repository import slugify
from ..normalize.names import canonical_make, canonical_model


def _canon(current: str, slug: str, fn) -> str:
    new = fn(current)
    if new == current:
        alt = fn(slug)
        if alt != slug:
            new = alt
    return new


def _merge_variants(conn: sqlite3.Connection, src_model: int, dst_model: int, st: dict):
    for v in conn.execute(
            "SELECT variant_id, fingerprint FROM variants WHERE model_id=?", (src_model,)).fetchall():
        dupe = conn.execute(
            "SELECT variant_id FROM variants WHERE model_id=? AND fingerprint=?",
            (dst_model, v["fingerprint"])).fetchone()
        if dupe:
            conn.execute("DELETE FROM variants WHERE variant_id=?", (v["variant_id"],))
            st["dupe_variants_dropped"] += 1
        else:
            conn.execute("UPDATE variants SET model_id=? WHERE variant_id=?",
                         (dst_model, v["variant_id"]))
            st["variants_repointed"] += 1


def _merge_or_rename_model(conn: sqlite3.Connection, model_id: int, make_id: int,
                           new_name: str, st: dict):
    # slug is re-derived from the canonical name (matching upsert_model), so a rename
    # that collides with an existing row on either key becomes a merge instead.
    new_slug = slugify(new_name)
    target = conn.execute(
        "SELECT model_id FROM models WHERE make_id=? AND (canonical_name=? OR slug=?) "
        "AND model_id<>?",
        (make_id, new_name, new_slug, model_id)).fetchone()
    if target:
        _merge_variants(conn, model_id, target["model_id"], st)
        conn.execute("DELETE FROM models WHERE model_id=?", (model_id,))
        conn.execute("UPDATE models SET canonical_name=?, updated_at=datetime('now') "
                     "WHERE model_id=?", (new_name, target["model_id"]))
        st["models_merged"] += 1
    else:
        conn.execute("UPDATE models SET canonical_name=?, slug=?, updated_at=datetime('now') "
                     "WHERE model_id=?", (new_name, new_slug, model_id))
        st["models_renamed"] += 1


def normalize_names(conn: sqlite3.Connection) -> dict:
    st = {"makes_renamed": 0, "makes_merged": 0, "models_renamed": 0, "models_merged": 0,
          "variants_repointed": 0, "dupe_variants_dropped": 0,
          "orphan_models_dropped": 0, "orphan_makes_dropped": 0}

    # --- makes: rename, or merge into an existing make of the same canonical name ---
    for mk in conn.execute("SELECT make_id, canonical_name, slug FROM makes").fetchall():
        new = _canon(mk["canonical_name"], mk["slug"], canonical_make)
        new_slug = slugify(new)
        if new == mk["canonical_name"] and new_slug == mk["slug"]:
            continue
        target = conn.execute(
            "SELECT make_id FROM makes WHERE (canonical_name=? OR slug=?) AND make_id<>?",
            (new, new_slug, mk["make_id"])).fetchone()
        if target:
            for md in conn.execute("SELECT model_id, slug FROM models WHERE make_id=?",
                                   (mk["make_id"],)).fetchall():
                clash = conn.execute(
                    "SELECT model_id FROM models WHERE make_id=? AND slug=?",
                    (target["make_id"], md["slug"])).fetchone()
                if clash:
                    _merge_variants(conn, md["model_id"], clash["model_id"], st)
                    conn.execute("DELETE FROM models WHERE model_id=?", (md["model_id"],))
                    st["models_merged"] += 1
                else:
                    conn.execute("UPDATE models SET make_id=? WHERE model_id=?",
                                 (target["make_id"], md["model_id"]))
            conn.execute("DELETE FROM makes WHERE make_id=?", (mk["make_id"],))
            st["makes_merged"] += 1
        else:
            conn.execute("UPDATE makes SET canonical_name=?, slug=?, updated_at=datetime('now') "
                         "WHERE make_id=?", (new, new_slug, mk["make_id"]))
            st["makes_renamed"] += 1

    # --- models: rename, or merge when two rows collapse to one canonical name.
    # Slug drift (slug != slugify(canonical), e.g. after the '+'-aware slugify change)
    # is repaired too, so later upserts hit the same row instead of colliding. ---
    for md in conn.execute(
            """SELECT md.model_id, md.make_id, md.canonical_name, md.slug,
                      mk.canonical_name AS make_name
               FROM models md JOIN makes mk ON mk.make_id = md.make_id""").fetchall():
        # row may have been merged away above
        if not conn.execute("SELECT 1 FROM models WHERE model_id=?", (md["model_id"],)).fetchone():
            continue
        fn = lambda n: canonical_model(n, make=md["make_name"])
        new = _canon(md["canonical_name"], md["slug"], fn)
        if new != md["canonical_name"] or slugify(new) != md["slug"]:
            _merge_or_rename_model(conn, md["model_id"], md["make_id"], new, st)

    st["orphan_models_dropped"] = conn.execute(
        "DELETE FROM models WHERE model_id NOT IN (SELECT model_id FROM variants)").rowcount
    st["orphan_makes_dropped"] = conn.execute(
        "DELETE FROM makes WHERE make_id NOT IN (SELECT make_id FROM models)").rowcount
    conn.commit()
    st.update(apply_on_sale(conn))
    st.update(apply_weight_overrides(conn))
    return st


def apply_on_sale(conn: sqlite3.Connection) -> dict:
    """Sync models/variants.on_sale_hu from config/discontinued.yaml (source of truth:
    unlisted models are reset to on-sale, so removing an entry re-enables the model)."""
    import yaml

    from ..settings import CONFIG_DIR

    path = CONFIG_DIR / "discontinued.yaml"
    listed = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("discontinued", {}) \
        if path.exists() else {}
    conn.execute("UPDATE models SET on_sale_hu=1")
    conn.execute("UPDATE variants SET on_sale_hu=1")
    marked = 0
    for make, slugs in listed.items():
        for slug in slugs:
            cur = conn.execute(
                """UPDATE models SET on_sale_hu=0, updated_at=datetime('now')
                   WHERE slug=? AND make_id=(SELECT make_id FROM makes WHERE canonical_name=?)""",
                (str(slug), make))
            marked += cur.rowcount
    conn.execute("""UPDATE variants SET on_sale_hu=0 WHERE model_id IN
                    (SELECT model_id FROM models WHERE on_sale_hu=0)""")
    conn.execute("""UPDATE makes SET on_sale_hu=CASE WHEN make_id IN
                    (SELECT make_id FROM models WHERE on_sale_hu=1) THEN 1 ELSE 0 END""")
    conn.commit()
    return {"models_marked_off_sale": marked}


def apply_weight_overrides(conn: sqlite3.Connection) -> dict:
    """Apply curated weight corrections (config/weight_overrides.yaml) on top of
    scraped values. Runs after every rebuild, so corrections survive re-ingests."""
    import yaml

    from ..settings import CONFIG_DIR

    path = CONFIG_DIR / "weight_overrides.yaml"
    entries = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("overrides", []) \
        if path.exists() else []
    n = 0
    for o in entries:
        rows = conn.execute(
            """SELECT v.variant_id FROM variants v
               JOIN models md ON md.model_id = v.model_id
               JOIN makes mk ON mk.make_id = md.make_id
               WHERE mk.canonical_name=? AND md.canonical_name=?
                 AND INSTR(LOWER(COALESCE(v.trim_name,'')), LOWER(?)) > 0""",
            (o["make"], o["model"], o["trim_contains"])).fetchall()
        for r in rows:
            cur = conn.execute(
                "UPDATE weights SET curb_weight_kg=?, hu_weight_kg=?, hu_weight_url=?, "
                "primary_source='curated-override', updated_at=datetime('now') "
                "WHERE variant_id=? AND curb_weight_kg IS NOT ?",
                (o["weight_kg"], o["weight_kg"], o.get("source_url"),
                 r["variant_id"], o["weight_kg"]))
            n += cur.rowcount
    conn.commit()
    return {"weights_overridden": n}
