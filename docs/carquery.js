// carquery.js — client-side port of the FastAPI backend (app/fees.py, queries.py,
// v2_api.py, routes.py). Loads cars.json once and answers the same queries the server
// did, returning the identical JSON shapes the two UIs already consume. Classic script:
// defines a global `CarQuery`. Used only by the static (GitHub Pages) build.
(function () {
  "use strict";

  const THRESHOLD_BEV = 2000;
  const THRESHOLD_COMBUSTION = 2000; // ICE and PHEV
  const PT_MAP = { electric: "BEV", bev: "BEV", phev: "PHEV", ice: "ICE" };
  const CATEGORY = { BEV: "electric", PHEV: "PHEV", ICE: "ICE" };
  const PT_LABEL = { BEV: "electric", PHEV: "PHEV", ICE: "ICE" };

  // cars.json sits next to this script at the site root; resolve it from our own URL so
  // it works from both `/` and `/v2/`.
  const SCRIPT_SRC = (document.currentScript && document.currentScript.src) || "";
  const DATA_URL = new URL("cars.json?v=0fd4804329", SCRIPT_SRC).href;

  let DATA = null;
  let LOADING = null;

  function load() {
    if (DATA) return Promise.resolve(DATA);
    if (!LOADING) {
      LOADING = fetch(DATA_URL)
        .then((r) => {
          if (!r.ok) throw new Error("cars.json " + r.status);
          return r.json();
        })
        .then((rows) => {
          // Precompute the fixed-threshold fee_status used by the legacy /api endpoints.
          for (const c of rows) c._fee = classifyFixed(c);
          DATA = rows;
          return rows;
        });
    }
    return LOADING;
  }

  // ── classifier — mirrors app/fees.classify exactly ────────────────────────
  function classify(pt, weight, wmin, wmax, t) {
    const lo = wmin != null ? wmin : weight;
    const hi = wmax != null ? wmax : weight;
    if (lo == null && hi == null) return "unknown";
    if (lo != null && hi != null) {
      if (lo > t) return "double";
      if (hi <= t) return "ok";
      return "borderline";
    }
    const rep = weight != null ? weight : lo != null ? lo : hi;
    if (rep == null) return "unknown";
    return rep > t ? "double" : "ok";
  }
  function thresholdFor(pt) {
    return pt === "BEV" ? THRESHOLD_BEV : THRESHOLD_COMBUSTION;
  }
  function classifyFixed(c) {
    return classify(c.powertrain_type, c.weight, c.weight_min, c.weight_max,
                    thresholdFor(c.powertrain_type));
  }

  // ── predicates — mirrors app/queries._predicates ──────────────────────────
  // `skip` excludes one filter dimension (used for facet skip-self semantics).
  function makePredicate(f, skip) {
    const tests = [];
    if (f.hu_only) tests.push((c) => c.source !== "cars-data");

    if (f.on_sale != null) {
      const want = f.on_sale ? 1 : 0;
      tests.push((c) => c.on_sale_hu === want);
    }

    if (f.q) {
      // Tokenized: every token must match somewhere in "make model trim" combined,
      // so "Toyota RAV4" works and a trailing space doesn't blank the results.
      const toks = String(f.q).toLowerCase().split(/\s+/).filter(Boolean);
      if (toks.length) {
        tests.push((c) => {
          const hay =
            ((c.make || "") + " " + (c.model || "") + " " + (c.trim || "")).toLowerCase();
          return toks.every((t) => hay.includes(t));
        });
      }
    }
    if (skip !== "powertrain" && f.powertrain && f.powertrain.length) {
      const vals = new Set(f.powertrain.map((v) => PT_MAP[String(v).toLowerCase()]).filter(Boolean));
      if (vals.size) tests.push((c) => vals.has(c.powertrain_type));
    }
    if (skip !== "subtype" && f.subtype && f.subtype.length) {
      const vals = new Set(f.subtype);
      tests.push((c) => vals.has(c.powertrain_subtype));
    }
    if (skip !== "drivetrain" && f.drivetrain && f.drivetrain.length) {
      const vals = new Set(f.drivetrain);
      tests.push((c) => vals.has(c.drivetrain));
    }
    if (f.weight_min != null) tests.push((c) => c.weight != null && c.weight >= f.weight_min);
    if (f.weight_max != null) tests.push((c) => c.weight != null && c.weight <= f.weight_max);
    if (f.weight_threshold != null && f.weight_cmp) {
      tests.push((c) => c.weight != null &&
        (f.weight_cmp === "above" ? c.weight > f.weight_threshold : c.weight <= f.weight_threshold));
    }
    if (skip !== "fee" && f.fee && f.fee.length) {
      const vals = new Set(f.fee);
      tests.push((c) => vals.has(c._fee));
    }
    if (f.include_unknown_weight === false) tests.push((c) => c.weight != null);
    if (skip !== "model_year" && f.model_year && f.model_year.length) {
      const vals = new Set(f.model_year.map(Number));
      tests.push((c) => vals.has(c.model_year));
    }
    return (c) => tests.every((t) => t(c));
  }

  // ── sorting — mirrors app/queries._SORTS ──────────────────────────────────
  const COLL = (a, b) =>
    String(a || "").localeCompare(String(b || ""), undefined, { sensitivity: "base" });
  const SORTERS = {
    make: (a, b) => COLL(a.make, b.make) || COLL(a.model, b.model) || COLL(a.trim, b.trim),
    weight_asc: (a, b) =>
      (a.weight == null) - (b.weight == null) || (a.weight || 0) - (b.weight || 0),
    weight_desc: (a, b) =>
      (a.weight == null) - (b.weight == null) || (b.weight || 0) - (a.weight || 0),
    year_desc: (a, b) =>
      (a.model_year == null) - (b.model_year == null) || (b.model_year || 0) - (a.model_year || 0),
  };

  function enrich(c) {
    return Object.assign({}, c, {
      fee_status: c._fee,
      powertrain_category: CATEGORY[c.powertrain_type] || c.powertrain_type,
    });
  }

  const THRESHOLDS = { BEV: 2000, ICE: 2000, PHEV: 2000 };

  // ── /api/cars ─────────────────────────────────────────────────────────────
  async function listCars(f) {
    const rows = await load();
    const pred = makePredicate(f, null);
    let items = rows.filter(pred);
    const sorter = SORTERS[f.sort] || SORTERS.make;
    items = items.slice().sort(sorter);
    const total = items.length;
    const page = Math.max(1, Number(f.page) || 1);
    const pageSize = Math.min(200, Math.max(1, Number(f.page_size) || 50));
    const start = (page - 1) * pageSize;
    const pageItems = items.slice(start, start + pageSize).map(enrich);
    return { total, page, page_size: pageSize, items: pageItems, thresholds: THRESHOLDS };
  }

  // ── /api/facets ───────────────────────────────────────────────────────────
  async function facets(f) {
    const rows = await load();
    function grouped(col, skip) {
      const sub = rows.filter(makePredicate(f, skip));
      const counts = new Map();
      for (const c of sub) {
        const v = col === "fee_status" ? c._fee : c[col];
        if (v == null) continue;
        counts.set(v, (counts.get(v) || 0) + 1);
      }
      return [...counts.entries()]
        .map(([value, count]) => ({ value, count }))
        .sort((a, b) => b.count - a.count);
    }
    const fullSub = rows.filter(makePredicate(f, null));
    let mn = null, mx = null;
    for (const c of fullSub) {
      if (c.weight == null) continue;
      mn = mn == null ? c.weight : Math.min(mn, c.weight);
      mx = mx == null ? c.weight : Math.max(mx, c.weight);
    }
    const pt = grouped("powertrain_type", "powertrain").map((x) => ({
      value: PT_LABEL[x.value] || x.value,
      count: x.count,
    }));
    return {
      powertrain: pt,
      subtype: grouped("powertrain_subtype", "subtype"),
      drivetrain: grouped("drivetrain", "drivetrain"),
      fee_status: grouped("fee_status", "fee"),
      model_year: grouped("model_year", "model_year"),
      weight_bounds: { min: mn, max: mx },
    };
  }

  // ── /api/cars/{id} ────────────────────────────────────────────────────────
  async function getCar(id) {
    const rows = await load();
    const c = rows.find((r) => r.id === Number(id));
    if (!c) return null;
    const row = enrich(c);
    const pt = c.powertrain_type;
    const thr = 2000;
    const rule = `Any car over ${thr} kg pays double Budapest parking fee`;
    row.fee = { threshold: thr, status: row.fee_status, rule, stored_classification: row.fee_status };
    return row;
  }

  // ── /api/v2/policy ────────────────────────────────────────────────────────
  async function policy(p) {
    const rows = await load();
    const bev = clampInt(p.bev, 2000, 500, 5000);
    const ice = clampInt(p.ice, 2000, 500, 5000);
    const limit = clampInt(p.limit, 500, 1, 2000);
    const ptSet = p.pt && p.pt.length ? new Set(p.pt) : null;
    const makeSet = p.make && p.make.length ? new Set(p.make) : null;

    let ok = 0, dbl = 0, borderline = 0, unknown = 0;
    const borders = [];
    for (const c of rows) {
      if ((c.is_missing || 0) !== 0) continue;
      if (c.on_sale_hu !== 1) continue;
      if (p.hu_only && c.hu_weight_kg == null) continue;
      // COALESCE-style: untyped rows still match their base type, so a BEV/PHEV
      // chip never silently drops rows whose subtype is unknown.
      if (ptSet && !ptSet.has(c.powertrain_subtype || c.powertrain_type)) continue;
      if (makeSet && !makeSet.has(c.make)) continue;

      const ptType = c.powertrain_type;
      const t = ptType === "BEV" ? bev : ice;
      const status = classify(ptType, c.weight, c.weight_min, c.weight_max, t);
      if (status === "ok") ok++;
      else if (status === "double") dbl++;
      else if (status === "borderline") borderline++;
      else unknown++;

      // Range-only rows (weight null, min/max set) classified 'double' must show in
      // border cases too: their lowest weight is the decisive figure.
      const repW = c.weight != null ? c.weight : c.weight_min;
      if (status === "double" && repW != null && t > 0) {
        const overPct = ((repW - t) / t) * 100;
        if (overPct > 0 && overPct <= 25) {
          borders.push({
            id: c.id, make: c.make, model: c.model, trim: c.trim,
            powertrain_subtype: c.powertrain_subtype || ptType,
            weight: repW, threshold: t, over_pct: overPct,
          });
        }
      }
    }
    borders.sort((a, b) => a.over_pct - b.over_pct);
    const b5 = borders.filter((b) => b.over_pct <= 5).slice(0, limit);
    const b10 = borders.filter((b) => b.over_pct <= 10).slice(0, limit);
    const b25 = borders.slice(0, limit);
    return {
      total: ok + dbl + borderline + unknown,
      ok, double: dbl, borderline, unknown,
      bev_threshold: bev, ice_threshold: ice,
      border_cases: { "5pct": b5, "10pct": b10, "25pct": b25 },
      thresholds: { BEV: bev, ICE: ice, PHEV: ice, HEV: ice, MHEV: ice, petrol: ice, diesel: ice },
    };
  }

  // ── /api/v2/makes ─────────────────────────────────────────────────────────
  async function makes() {
    const rows = await load();
    const set = new Set();
    for (const c of rows) if (c.on_sale_hu === 1 && c.make) set.add(c.make);
    return [...set].sort(COLL);
  }

  // ── /api/cars.csv ─────────────────────────────────────────────────────────
  const CSV_COLS = ["make", "model", "trim", "powertrain_type", "powertrain_subtype",
    "drivetrain", "power_kw", "battery_kwh", "model_year", "weight", "weight_min",
    "weight_max", "weight_unit", "hu_weight_kg", "n_sources", "sources_agree",
    "threshold", "fee_status", "weight_source", "weight_source_url"];

  function csvCell(v) {
    if (v == null) return "";
    const s = String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }
  async function exportCsvString(f) {
    const rows = await load();
    let items = rows.filter(makePredicate(f, null)).slice().sort(SORTERS[f.sort] || SORTERS.make);
    const lines = [CSV_COLS.join(",")];
    for (const c of items) {
      const rec = Object.assign({}, c, {
        threshold: 2000,
        fee_status: c._fee,
      });
      lines.push(CSV_COLS.map((k) => csvCell(rec[k])).join(","));
    }
    return lines.join("\n") + "\n";
  }

  function clampInt(v, dflt, lo, hi) {
    let n = Number(v);
    if (!Number.isFinite(n)) n = dflt;
    n = Math.round(n);
    return Math.max(lo, Math.min(hi, n));
  }

  window.CarQuery = { load, classify, listCars, facets, getCar, policy, makes, exportCsvString };
})();
