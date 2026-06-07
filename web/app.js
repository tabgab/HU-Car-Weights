const state = {
  q: "", powertrain: new Set(), fee: new Set(), subtype: new Set(),
  drivetrain: new Set(), weight_min: null, weight_max: null,
  include_unknown_weight: true, sort: "make", page: 1, page_size: 50,
};

const $ = (s) => document.querySelector(s);
const rowsEl = $("#rows"), emptyEl = $("#empty"), countEl = $("#count");

function buildParams(forExport = false) {
  const p = new URLSearchParams();
  if (state.q) p.set("q", state.q);
  for (const v of state.powertrain) p.append("powertrain", v);
  for (const v of state.fee) p.append("fee", v);
  for (const v of state.subtype) p.append("subtype", v);
  for (const v of state.drivetrain) p.append("drivetrain", v);
  if (state.weight_min != null) p.set("weight_min", state.weight_min);
  if (state.weight_max != null) p.set("weight_max", state.weight_max);
  if (!state.include_unknown_weight) p.set("include_unknown_weight", "false");
  p.set("sort", state.sort);
  if (!forExport) { p.set("page", state.page); p.set("page_size", state.page_size); }
  return p;
}

const FEE_LABEL = { ok: "OK", double: "DOUBLE", borderline: "BORDERLINE", unknown: "UNKNOWN" };
function feeBadge(s) { return `<span class="badge badge--${s}">${FEE_LABEL[s] || s}</span>`; }
function confDot(c) {
  if (c == null) return `<span class="muted">—</span>`;
  const lvl = c >= 0.8 ? "high" : c >= 0.6 ? "medium" : "low";
  return `<span class="dot dot--${lvl}"></span>${lvl}`;
}
function weightText(r) {
  if (r.weight == null && r.weight_min == null && r.weight_max == null)
    return `<span class="muted"><i>unknown</i></span>`;
  if (r.weight_min != null && r.weight_max != null && r.weight_min !== r.weight_max)
    return `${r.weight_min}–${r.weight_max}${r.weight != null ? ` (≈${r.weight})` : ""} kg`;
  return `${r.weight ?? r.weight_min ?? r.weight_max} kg`;
}
const PT_LABEL = { electric: "Electric", PHEV: "PHEV", ICE: "ICE" };

async function refresh() {
  const [list, facets] = await Promise.all([
    fetch("/api/cars?" + buildParams()).then((r) => r.json()),
    fetch("/api/facets?" + buildParams()).then((r) => r.json()),
  ]);
  renderRows(list);
  renderFacets(facets);
  countEl.textContent = `${list.total.toLocaleString()} cars`;
  const pages = Math.max(1, Math.ceil(list.total / list.page_size));
  $("#pageinfo").textContent = `Page ${list.page} / ${pages}`;
  $("#prev").disabled = list.page <= 1;
  $("#next").disabled = list.page >= pages;
}

function renderRows(list) {
  rowsEl.innerHTML = "";
  emptyEl.hidden = list.total > 0;
  for (const r of list.items) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.make}</td><td>${r.model}</td><td>${r.trim ?? '<span class="muted">—</span>'}</td>
      <td>${r.drivetrain ?? "—"}</td><td class="nowrap">${r.power_kw != null ? r.power_kw + " kW" : "—"}</td>
      <td>${r.model_year ?? "—"}</td>
      <td class="nowrap">${weightText(r)}</td>
      <td>${feeBadge(r.fee_status)}</td>
      <td class="nowrap">${confDot(r.weight_confidence)}</td>`;
    tr.onclick = () => openDetail(r.id);
    rowsEl.appendChild(tr);
  }
}

function renderFacets(f) {
  facetGroup("#f-powertrain", "powertrain", f.powertrain, PT_LABEL);
  facetGroup("#f-fee", "fee", f.fee_status, FEE_LABEL);
  facetGroup("#f-subtype", "subtype", f.subtype, {});
  facetGroup("#f-drivetrain", "drivetrain", f.drivetrain, {});
}

function facetGroup(sel, key, buckets, labels) {
  const el = $(sel);
  el.innerHTML = "";
  for (const b of buckets || []) {
    const id = `${key}:${b.value}`;
    const checked = state[key].has(String(b.value)) ? "checked" : "";
    const lab = document.createElement("label");
    lab.innerHTML = `<input type="checkbox" ${checked} data-key="${key}" data-val="${b.value}">
      ${labels[b.value] || b.value} <span class="cnt">${b.count}</span>`;
    el.appendChild(lab);
  }
  el.querySelectorAll("input").forEach((cb) => {
    cb.onchange = () => {
      const set = state[cb.dataset.key];
      cb.checked ? set.add(cb.dataset.val) : set.delete(cb.dataset.val);
      state.page = 1; refresh();
    };
  });
}

async function openDetail(id) {
  const r = await fetch("/api/cars/" + id).then((x) => x.json());
  const row = (k, v) => `<div class="detail-row"><span class="k">${k}</span><span>${v}</span></div>`;
  $("#detail-body").innerHTML = `
    <h2 class="detail-h">${r.make} ${r.model}</h2>
    <div class="muted">${r.trim ?? ""}</div>
    <div style="margin:14px 0">${feeBadge(r.fee_status)}</div>
    ${row("Powertrain", PT_LABEL[r.powertrain_category] || r.powertrain_type)}
    ${row("Sub-type", r.powertrain_subtype ?? "—")}
    ${row("Drivetrain", r.drivetrain ?? "—")}
    ${row("Power", r.power_kw != null ? r.power_kw + " kW" : "—")}
    ${row("Battery", r.battery_kwh != null ? r.battery_kwh + " kWh" : "—")}
    ${row("Model year", r.model_year ?? "—")}
    ${row("Curb weight", weightText(r))}
    ${row("Threshold", (r.fee?.threshold ?? "—") + " kg")}
    ${row("Confidence", confDot(r.weight_confidence))}
    ${row("Source", r.weight_source_url ? `<a href="${r.weight_source_url}" target="_blank">${r.weight_source ?? "link"}</a>` : (r.weight_source ?? "—"))}
    <div class="rule">${r.fee?.rule ?? ""}</div>`;
  $("#detail").hidden = false;
}

// wiring
let qTimer;
$("#q").oninput = (e) => { clearTimeout(qTimer); qTimer = setTimeout(() => { state.q = e.target.value; state.page = 1; refresh(); }, 250); };
$("#wmin").onchange = (e) => { state.weight_min = e.target.value ? +e.target.value : null; state.page = 1; refresh(); };
$("#wmax").onchange = (e) => { state.weight_max = e.target.value ? +e.target.value : null; state.page = 1; refresh(); };
$("#incl-unknown").onchange = (e) => { state.include_unknown_weight = e.target.checked; state.page = 1; refresh(); };
$("#sort").onchange = (e) => { state.sort = e.target.value; refresh(); };
$("#prev").onclick = () => { if (state.page > 1) { state.page--; refresh(); } };
$("#next").onclick = () => { state.page++; refresh(); };
$("#export").onclick = () => { window.location = "/api/cars.csv?" + buildParams(true); };
$("#detail-close").onclick = () => { $("#detail").hidden = true; };
$("#detail").onclick = (e) => { if (e.target.id === "detail") $("#detail").hidden = true; };
$("#reset").onclick = () => {
  Object.assign(state, { q: "", powertrain: new Set(), fee: new Set(), subtype: new Set(),
    drivetrain: new Set(), weight_min: null, weight_max: null, include_unknown_weight: true,
    sort: "make", page: 1 });
  $("#q").value = ""; $("#wmin").value = ""; $("#wmax").value = "";
  $("#incl-unknown").checked = true; $("#sort").value = "make";
  refresh();
};

refresh();
