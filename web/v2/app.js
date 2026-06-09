// carWeights v2 — web SPA mirroring the Android Compose UI.
// Uses existing /api/v2/policy for live threshold simulation.
// Tabs: Policy / Lookup / Browse / Settings.

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);
const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString('en-US'));

const POWERTRAIN_OPTIONS = ['BEV', 'PHEV', 'HEV', 'MHEV', 'petrol', 'diesel'];
const TOP_MAKES = ['Škoda', 'Volkswagen', 'BMW', 'Audi', 'Mercedes-Benz',
                    'Toyota', 'Hyundai', 'Kia', 'Ford', 'Renault'];
const FONT_SCALES = [0.85, 1.0, 1.15, 1.3, 1.5, 1.75, 2.0];

// ─── State ────────────────────────────────────────────────────────────────
const state = {
  bev: loadN('bev', 2000),
  ice: loadN('ice', 1800),
  ptFilter: new Set(loadS('pt_filter', [])),
  makeFilter: new Set(loadS('make_filter', [])),
  huOnly: loadB('hu_only', false),
  fontScale: loadN('font_scale', 1.15),
  activeTab: 'policy',
  allMakes: [],
  allCars: [],
  outcome: null,
  selectedCarId: null,
  // Lookup
  lookupPt: 'BEV',
  lookupWeight: 1800,
  // Browse
  browseQ: '',
};

// ─── localStorage helpers ──────────────────────────────────────────────────
function loadN(k, d) { const v = localStorage.getItem(k); return v == null ? d : Number(v); }
function loadS(k, d) { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); }
function loadB(k, d) { const v = localStorage.getItem(k); return v == null ? d : v === 'true'; }
function saveN(k, v) { localStorage.setItem(k, String(v)); }
function saveS(k, v) { localStorage.setItem(k, JSON.stringify([...v])); }
function saveB(k, v) { localStorage.setItem(k, String(v)); }

// ─── Tabs ─────────────────────────────────────────────────────────────────
function selectTab(name) {
  state.activeTab = name;
  $$('.tab').forEach(t => t.setAttribute('aria-selected', String(t.dataset.tab === name)));
  $$('.tabpanel').forEach(p => p.classList.toggle('active', p.id === 'tab-' + name));
}
$$('.tab').forEach(t => t.addEventListener('click', () => selectTab(t.dataset.tab)));

// ─── Apply font scale on load + on change ────────────────────────────────
function applyFontScale() {
  document.documentElement.style.setProperty('--font-scale', state.fontScale);
  const el = $('#font-current');
  if (el) el.textContent = `Current: ${state.fontScale.toFixed(2)}×`;
}
applyFontScale();

// ─── Powertrain + Make filter chips ──────────────────────────────────────
function renderPowertrainChips() {
  const row = $('#filter-powertrain');
  row.innerHTML = '';
  POWERTRAIN_OPTIONS.forEach(opt => {
    const c = document.createElement('button');
    c.className = 'chip' + (state.ptFilter.has(opt) ? ' on' : '');
    c.textContent = opt;
    c.onclick = () => {
      if (state.ptFilter.has(opt)) state.ptFilter.delete(opt); else state.ptFilter.add(opt);
      saveS('pt_filter', state.ptFilter);
      renderPowertrainChips();
      runPolicy();
    };
    row.appendChild(c);
  });
}

function renderMakeQuickChips() {
  const row = $('#filter-makes-quick');
  row.innerHTML = '';
  TOP_MAKES.forEach(m => {
    const c = document.createElement('button');
    c.className = 'chip' + (state.makeFilter.has(m) ? ' on' : '');
    c.textContent = m;
    c.onclick = () => {
      if (state.makeFilter.has(m)) state.makeFilter.delete(m); else state.makeFilter.add(m);
      saveS('make_filter', state.makeFilter);
      renderMakeQuickChips();
      updateClearMakesButton();
      runPolicy();
    };
    row.appendChild(c);
  });
  updateClearMakesButton();
}

function updateClearMakesButton() {
  $('#clear-makes').classList.toggle('hidden', state.makeFilter.size === 0);
}

// ─── Sliders ──────────────────────────────────────────────────────────────
function wireSlider(sliderId, valueId, key, onChange) {
  const s = $(sliderId);
  const v = $(valueId);
  s.value = state[key];
  v.textContent = `${state[key]} kg`;
  s.addEventListener('input', () => {
    const n = Number(s.value);
    state[key] = n;
    v.textContent = `${n} kg`;
    saveN(key, n);
    onChange();
  });
}
wireSlider('#bev-slider', '#bev-value', 'bev', runPolicy);
wireSlider('#ice-slider', '#ice-value', 'ice', runPolicy);

$('#reset-defaults').onclick = () => {
  state.bev = 2000; state.ice = 1800;
  saveN('bev', 2000); saveN('ice', 1800);
  $('#bev-slider').value = 2000; $('#bev-value').textContent = '2000 kg';
  $('#ice-slider').value = 1800; $('#ice-value').textContent = '1800 kg';
  $('#note-current').textContent = 'Currently: BEV 2000 kg · ICE 1800 kg.';
  runPolicy();
};

// ─── Make picker sheet ─────────────────────────────────────────────────────
$('#open-make-picker').onclick = openMakeSheet;
$('#make-sheet-close').onclick = closeMakeSheet;
$('#make-sheet-clear').onclick = () => { state.makeFilter = new Set(); saveS('make_filter', state.makeFilter); refreshMakeSheetList(); renderMakeQuickChips(); updateClearMakesButton(); };
$('#make-sheet-all').onclick = () => { state.makeFilter = new Set(state.allMakes); saveS('make_filter', state.makeFilter); refreshMakeSheetList(); renderMakeQuickChips(); updateClearMakesButton(); };
$('#make-sheet-reset').onclick = () => { state.makeFilter = new Set(); saveS('make_filter', state.makeFilter); closeMakeSheet(); renderMakeQuickChips(); updateClearMakesButton(); runPolicy(); };
$('#make-sheet-apply').onclick = () => { closeMakeSheet(); renderMakeQuickChips(); updateClearMakesButton(); runPolicy(); };
$('#make-search').addEventListener('input', e => { state.makeSheetQ = e.target.value; refreshMakeSheetList(); });
$('#clear-makes').onclick = () => { state.makeFilter = new Set(); saveS('make_filter', state.makeFilter); renderMakeQuickChips(); updateClearMakesButton(); runPolicy(); };

function openMakeSheet() {
  state.makeSheetQ = '';
  $('#make-search').value = '';
  $('#make-sheet').classList.remove('hidden');
  refreshMakeSheetList();
}
function closeMakeSheet() { $('#make-sheet').classList.add('hidden'); }
function refreshMakeSheetList() {
  const q = (state.makeSheetQ || '').toLowerCase();
  const list = q
    ? state.allMakes.filter(m => m.toLowerCase().includes(q))
    : state.allMakes;
  const el = $('#make-sheet-list');
  el.innerHTML = '';
  list.forEach(m => {
    const id = `mk-${m.replace(/[^a-z0-9]/gi, '')}`;
    const row = document.createElement('div');
    row.className = 'sheet-row';
    const cb = document.createElement('input');
    cb.type = 'checkbox'; cb.id = id; cb.checked = state.makeFilter.has(m);
    cb.onchange = () => {
      if (cb.checked) state.makeFilter.add(m); else state.makeFilter.delete(m);
      saveS('make_filter', state.makeFilter);
      $('#make-sheet-count').textContent = `${state.makeFilter.size} selected · ${state.allMakes.length} total`;
    };
    const label = document.createElement('label');
    label.htmlFor = id; label.textContent = m;
    row.appendChild(cb); row.appendChild(label);
    el.appendChild(row);
  });
  $('#make-sheet-count').textContent = `${state.makeFilter.size} selected · ${state.allMakes.length} total`;
}

// ─── Policy: live simulation via /api/v2/policy ──────────────────────────
let policyTimer = null;
function runPolicy() {
  if (policyTimer) clearTimeout(policyTimer);
  policyTimer = setTimeout(_runPolicy, 80);
}

async function _runPolicy() {
  const params = new URLSearchParams();
  params.set('bev', state.bev);
  params.set('ice', state.ice);
  if (state.huOnly) params.set('hu_only', 'true');
  state.ptFilter.forEach(p => params.append('pt', p));
  state.makeFilter.forEach(m => params.append('make', m));
  try {
    const r = await fetch('/api/v2/policy?' + params.toString());
    state.outcome = await r.json();
    renderOutcome();
  } catch (e) {
    console.error(e);
  }
}

function renderOutcome() {
  const o = state.outcome;
  if (!o) return;
  $('#outcome-total').textContent = `${fmt(o.total)} cars`;
  $('#legend-ok').textContent = `${fmt(o.ok)} · ${pct(o.ok, o.total)}%`;
  $('#legend-double').textContent = `${fmt(o.double)} · ${pct(o.double, o.total)}%`;
  $('#legend-borderline').textContent = `${fmt(o.borderline)} · ${pct(o.borderline, o.total)}%`;
  $('#legend-unknown').textContent = `${fmt(o.unknown)} · ${pct(o.unknown, o.total)}%`;
  // bar
  const bar = $('#outcome-bar');
  bar.innerHTML = '';
  for (const [cls, n] of [['ok', o.ok], ['double', o.double], ['borderline', o.borderline], ['unknown', o.unknown]]) {
    const p = pct(n, o.total);
    if (p > 0) {
      const seg = document.createElement('div');
      seg.className = cls;
      seg.style.width = p + '%';
      bar.appendChild(seg);
    }
  }
  // border buckets
  const b5 = o.border_cases['5pct'] || [];
  const b10 = o.border_cases['10pct'] || [];
  const b25 = o.border_cases['25pct'] || [];
  $('#b-5').textContent = fmt(b5.length);
  $('#b-10').textContent = fmt(b10.length);
  $('#b-25').textContent = fmt(b25.length);
  $('#b-hint').textContent = b25.length
    ? `Closest to threshold (top ${Math.min(b25.length, 10)}):`
    : 'No border cases at this policy.';
  // rows
  const list = $('#borders');
  list.innerHTML = '';
  b25.slice(0, 10).forEach(b => {
    const row = document.createElement('div');
    row.className = 'border-row';
    row.innerHTML = `
      <div class="make-model">
        <div class="name">${esc(b.make)} ${esc(b.model)}${b.trim ? ' · ' + esc(b.trim) : ''}</div>
        <div class="meta">${esc(b.powertrain_subtype)} · ${b.threshold} kg</div>
      </div>
      <div class="delta">${b.weight} kg  +${b.over_pct.toFixed(1)}%</div>
    `;
    row.onclick = () => openDetail(b.id);
    list.appendChild(row);
  });
  $('#note-current').textContent =
    `Currently: BEV ${state.bev} kg · ICE ${state.ice} kg.`;
}

function pct(n, total) {
  if (!total) return '0.0';
  return (100 * n / total).toFixed(1);
}

// ─── Lookup ───────────────────────────────────────────────────────────────
$$('#lookup-pt .seg').forEach(b => b.onclick = () => {
  $$('#lookup-pt .seg').forEach(s => s.classList.toggle('active', s === b));
  state.lookupPt = b.dataset.pt;
  runLookup();
});
$('#lookup-weight').addEventListener('input', e => {
  state.lookupWeight = Number(e.target.value) || 0;
  $('#lookup-slider').value = state.lookupWeight;
  runLookup();
});
$('#lookup-slider').addEventListener('input', e => {
  state.lookupWeight = Number(e.target.value);
  $('#lookup-weight').value = state.lookupWeight;
  runLookup();
});
function runLookup() {
  const w = state.lookupWeight;
  const pt = state.lookupPt;
  const t = pt === 'BEV' ? 2000 : 1800;
  $('#lookup-threshold').textContent = `Threshold: ${t} kg`;
  $('#lookup-threshold-hint').textContent = `Threshold: ${t} kg`;
  const status = classifyClient(pt, w, t);
  const pill = $('#lookup-status');
  pill.className = 'verdict-pill ' + status;
  pill.textContent = status.toUpperCase();
  const margin = w - t;
  $('#lookup-rule').textContent = w
    ? (status === 'ok' ? `${pt} at ${w} kg is ${margin} kg under the ${t} kg limit — OK.`
       : status === 'double' ? `${pt} at ${w} kg is +${margin} kg over the ${t} kg limit — pays double.`
       : '—')
    : 'Enter a weight to see the verdict.';
  // nearby cars
  fetchNearby(pt, w);
}
function classifyClient(pt, w, t) {
  if (!w) return 'unknown';
  return w > t ? 'double' : 'ok';
}
async function fetchNearby(pt, w) {
  if (!w) { $('#lookup-nearby-card').classList.add('hidden'); return; }
  const params = new URLSearchParams({ powertrain: pt, page_size: '200' });
  const r = await fetch('/api/cars?' + params.toString());
  const data = await r.json();
  const near = (data.items || [])
    .filter(c => (c.weight || c.weight_min) && Math.abs((c.weight || c.weight_min) - w) <= 50)
    .slice(0, 10);
  if (near.length === 0) { $('#lookup-nearby-card').classList.add('hidden'); return; }
  $('#lookup-nearby-card').classList.remove('hidden');
  const el = $('#lookup-nearby');
  el.innerHTML = '';
  near.forEach(c => {
    const w2 = c.weight || c.weight_min;
    const row = document.createElement('div');
    row.className = 'row';
    row.innerHTML = `
      <div class="main">
        <div class="title">${esc(c.make)} ${esc(c.model)}${c.trim ? ' · ' + esc(c.trim) : ''}</div>
        <div class="meta">${c.powertrain_subtype || c.powertrain_type} · ${c.model_year || '—'}</div>
      </div>
      <div class="w">${w2} kg</div>
    `;
    row.onclick = () => openDetail(c.id);
    el.appendChild(row);
  });
}

// ─── Browse ───────────────────────────────────────────────────────────────
$('#browse-q').addEventListener('input', e => { state.browseQ = e.target.value; runBrowse(); });
$('#browse-hu-only').addEventListener('change', e => {
  state.huOnly = e.target.checked;
  saveB('hu_only', state.huOnly);
  $('#settings-hu-only').checked = state.huOnly;
  runPolicy();
  runBrowse();
});
$('#settings-hu-only').addEventListener('change', e => {
  state.huOnly = e.target.checked;
  saveB('hu_only', state.huOnly);
  $('#browse-hu-only').checked = state.huOnly;
  runPolicy();
  runBrowse();
});

async function runBrowse() {
  const q = state.browseQ.trim();
  const params = new URLSearchParams({ q, page_size: '200' });
  if (state.huOnly) params.set('hu_only', 'true');
  const r = await fetch('/api/cars?' + params.toString());
  const data = await r.json();
  state.allCars = data.items || [];
  const total = data.total || 0;
  $('#browse-count').textContent = `${fmt(state.allCars.length)} of ${fmt(total)} cars`;
  const list = $('#browse-list');
  list.innerHTML = '';
  if (state.allCars.length === 0) {
    list.innerHTML = '<div class="muted" style="padding: 20px;">No cars match.</div>';
    return;
  }
  state.allCars.forEach(c => {
    const w = c.weight || c.weight_min;
    const row = document.createElement('div');
    row.className = 'row';
    row.innerHTML = `
      <div class="main">
        <div class="title">${esc(c.make)} ${esc(c.model)}</div>
        <div class="meta">${[c.trim, c.powertrain_type, c.drivetrain, c.model_year].filter(Boolean).join(' · ')}</div>
      </div>
      <div class="w">${w || '—'} kg</div>
      <span class="pill ${c.fee_status}">${c.fee_status ? c.fee_status.toUpperCase() : '?'}</span>
    `;
    row.onclick = () => openDetail(c.id);
    list.appendChild(row);
  });
}

// ─── Settings: font size ──────────────────────────────────────────────────
function renderFontPresets() {
  const row = $('#font-presets');
  row.innerHTML = '';
  FONT_SCALES.forEach(s => {
    const c = document.createElement('button');
    c.className = 'chip' + (Math.abs(s - state.fontScale) < 0.01 ? ' on' : '');
    c.textContent = s.toFixed(2) + '×';
    c.onclick = () => { state.fontScale = s; saveN('font_scale', s); applyFontScale(); renderFontPresets(); };
    row.appendChild(c);
  });
}
$('#font-slider').addEventListener('input', e => {
  const idx = Number(e.target.value);
  state.fontScale = FONT_SCALES[idx];
  saveN('font_scale', state.fontScale);
  applyFontScale();
  renderFontPresets();
});
$('#font-slider').value = Math.max(0, FONT_SCALES.indexOf(state.fontScale));
renderFontPresets();

// ─── Export CSV ───────────────────────────────────────────────────────────
$('#export').onclick = () => {
  const params = new URLSearchParams();
  if (state.huOnly) params.set('hu_only', 'true');
  state.ptFilter.forEach(p => params.append('subtype', p));
  state.makeFilter.forEach(m => params.append('q', m));
  window.location = '/api/cars.csv?' + params.toString();
};

// ─── Car detail drawer ────────────────────────────────────────────────────
$('#detail-close').onclick = closeDetail;
async function openDetail(id) {
  state.selectedCarId = id;
  $('#detail').classList.remove('hidden');
  const r = await fetch('/api/cars/' + id);
  if (!r.ok) { closeDetail(); return; }
  const c = await r.json();
  const fee = c.fee || {};
  const verdict = fee.status || 'unknown';
  const colorClass = `verdict-pill ${verdict}`;
  const w = c.weight || c.weight_min;
  const hu = c.hu_weight_kg;
  const disagree = hu != null && c.weight != null && hu !== c.weight;
  $('#detail-body').innerHTML = `
    <h2 class="detail-h">${esc(c.make)} ${esc(c.model)}${c.trim ? ' · ' + esc(c.trim) : ''}</h2>
    <div class="muted small">${esc(c.powertrain_subtype || c.powertrain_type)}</div>
    <div class="detail-verdict ${colorClass}">${verdict.toUpperCase()}</div>
    <div class="muted small">Threshold: ${fee.threshold || (c.powertrain_type==='BEV' ? 2000 : 1800)} kg</div>
    <div class="detail-row"><span class="k">Powertrain</span><span class="v">${esc(c.powertrain_type || '—')}</span></div>
    <div class="detail-row"><span class="k">Sub-type</span><span class="v">${esc(c.powertrain_subtype || '—')}</span></div>
    <div class="detail-row"><span class="k">Drivetrain</span><span class="v">${esc(c.drivetrain || '—')}</span></div>
    <div class="detail-row"><span class="k">Power</span><span class="v">${c.power_kw || '—'} kW</span></div>
    <div class="detail-row"><span class="k">Battery</span><span class="v">${c.battery_kwh || '—'} kWh</span></div>
    <div class="detail-row"><span class="k">Model year</span><span class="v">${c.model_year || '—'}</span></div>
    <div class="detail-row"><span class="k">Curb weight (cars-data)</span><span class="v">${w || '—'} kg</span></div>
    <div class="detail-row"><span class="k">Curb weight (HU katalógus)</span><span class="v">${hu || '—'} kg</span></div>
    ${disagree ? `<div class="detail-row"><span class="k">Disagreement</span><span class="v" style="color: var(--amber);">${(hu - c.weight) > 0 ? '+' : ''}${hu - c.weight} kg — HU is authoritative</span></div>` : ''}
    <div class="detail-row"><span class="k">Primary source</span><span class="v">${esc(c.weight_source || 'cars-data')}</span></div>
    <div class="detail-rule">${esc(fee.rule || '')}</div>
  `;
}
function closeDetail() {
  state.selectedCarId = null;
  $('#detail').classList.add('hidden');
}

// ─── Esc closes drawer/sheet, arrow-left closes detail ───────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (state.selectedCarId != null) closeDetail();
    else if (!$('#make-sheet').classList.contains('hidden')) closeMakeSheet();
  }
});
$('#detail').addEventListener('click', e => { if (e.target.id === 'detail') closeDetail(); });

// ─── Helpers ──────────────────────────────────────────────────────────────
function esc(s) {
  if (s == null) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ─── Boot ────────────────────────────────────────────────────────────────
(async function boot() {
  // Load makes
  try {
    const r = await fetch('/api/v2/makes');
    state.allMakes = await r.json();
  } catch (e) {
    state.allMakes = TOP_MAKES;
  }
  renderPowertrainChips();
  renderMakeQuickChips();
  // Reflect HU-only checkbox
  $('#browse-hu-only').checked = state.huOnly;
  $('#settings-hu-only').checked = state.huOnly;
  // Initial sim + browse
  runPolicy();
  runLookup();
  selectTab(state.activeTab);
  // Total car count
  try {
    const r = await fetch('/api/cars?page_size=1');
    const d = await r.json();
    $('#data-source').textContent = `cars.db is bundled server-side (read-only SQLite). ${fmt(d.total)} cars total.`;
  } catch (e) {}
})();
