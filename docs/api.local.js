// api.local.js — serverless backend. Dispatches the same /api/... URLs the UI builds to the
// in-browser CarQuery port (carquery.js) over the bundled cars.json. Used by the static
// (GitHub Pages) build. Defines apiGet / apiCsv, matching api.http.js.
(function () {
  "use strict";

  function filtersFromParams(sp) {
    const f = {};
    if (sp.get("q")) f.q = sp.get("q");
    f.powertrain = sp.getAll("powertrain");
    f.subtype = sp.getAll("subtype");
    f.drivetrain = sp.getAll("drivetrain");
    f.fee = sp.getAll("fee");
    f.model_year = sp.getAll("model_year").map(Number);
    if (sp.has("weight_min")) f.weight_min = Number(sp.get("weight_min"));
    if (sp.has("weight_max")) f.weight_max = Number(sp.get("weight_max"));
    if (sp.has("weight_threshold")) f.weight_threshold = Number(sp.get("weight_threshold"));
    if (sp.get("weight_cmp")) f.weight_cmp = sp.get("weight_cmp");
    f.include_unknown_weight = sp.get("include_unknown_weight") !== "false";
    f.hu_only = sp.get("hu_only") === "true";
    if (sp.has("on_sale")) f.on_sale = sp.get("on_sale") === "true";  // tri-state like the server
    f.sort = sp.get("sort") || "make";
    if (sp.has("page")) f.page = Number(sp.get("page"));
    if (sp.has("page_size")) f.page_size = Number(sp.get("page_size"));
    return f;
  }

  function policyParams(sp) {
    return {
      bev: sp.has("bev") ? Number(sp.get("bev")) : 2000,
      ice: sp.has("ice") ? Number(sp.get("ice")) : 2000,
      pt: sp.getAll("pt"),
      make: sp.getAll("make"),
      hu_only: sp.get("hu_only") === "true",
      limit: sp.has("limit") ? Number(sp.get("limit")) : 500,
    };
  }

  window.apiGet = function (url) {
    const u = new URL(url, location.href);
    const path = u.pathname;
    const sp = u.searchParams;
    if (path.indexOf("/api/v2/policy") !== -1) return CarQuery.policy(policyParams(sp));
    if (path.indexOf("/api/v2/makes") !== -1) return CarQuery.makes();
    if (path.indexOf("/api/facets") !== -1) return CarQuery.facets(filtersFromParams(sp));
    const m = path.match(/\/api\/cars\/(\d+)/);
    if (m) return CarQuery.getCar(Number(m[1]));
    if (path.indexOf("/api/cars") !== -1) return CarQuery.listCars(filtersFromParams(sp));
    return Promise.reject(new Error("Unknown API path: " + path));
  };

  window.apiCsv = function (url) {
    const u = new URL(url, location.href);
    return CarQuery.exportCsvString(filtersFromParams(u.searchParams)).then((csv) => {
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const href = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = href;
      a.download = "cars_export.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(href), 1000);
    });
  };
})();
