// i18n.js — tiny shared localization layer for both UIs (classic script -> window.I18N).
// Picks HU/EN, persists the choice, fills [data-i18n]/[data-i18n-ph]/[data-i18n-title]
// from the dictionary, and notifies the app to re-render dynamic content on change.
(function () {
  "use strict";

  const STRINGS = {
    en: {
      // ── shared ──
      page_title_legacy: "Hungarian Car Weights — Budapest Parking Fee",
      page_title_v2: "carWeights HU — Policy Explorer",
      brand: "🅿️ Hungarian Car Weights",
      subtitle: "Budapest weight-based parking fee (from 2027): any car > 2000 kg → double",
      export_csv: "⬇ Export CSV",
      nav_android: "📱 AndroidApp UI",
      nav_classic: "← Classic UI",
      // ── legacy sidebar ──
      search_label: "Search",
      search_ph: "make / model / trim",
      hu_only_label: "🇭🇺 HU data only",
      hu_only_hint: "use only Hungarian-sourced weights",
      filter_on_sale: "On sale in Hungary",
      f_powertrain: "Powertrain",
      f_fee: "Fee status",
      f_subtype: "Sub-type",
      f_drivetrain: "Drivetrain",
      f_weight: "Curb weight (kg)",
      ph_min: "min",
      ph_max: "max",
      include_unknown: "include unknown weight",
      sort_label: "Sort",
      sort_make: "Make / model",
      sort_wdesc: "Weight ↓",
      sort_wasc: "Weight ↑",
      sort_ydesc: "Year ↓",
      reset_filters: "Reset filters",
      // ── legacy table ──
      th_make: "Make", th_model: "Model", th_trim: "Trim", th_drive: "Drive",
      th_power: "Power", th_year: "Year", th_weight: "Curb weight", th_fee: "Fee", th_source: "Source",
      empty: "No cars match these filters.",
      prev: "← Prev", next: "Next →",
      page_of: "Page {0} / {1}",
      cars_n: "{0} cars",
      // ── legacy detail ──
      d_powertrain: "Powertrain", d_subtype: "Sub-type", d_drivetrain: "Drivetrain",
      d_power: "Power", d_battery: "Battery", d_year: "Model year",
      d_weight_cd: "Curb weight (cars-data)", d_weight_hu: "Curb weight (HU catalogue)",
      d_sources: "Sources", d_threshold: "Threshold",
      weight_unknown: "unknown",
      // ── sources cell / tooltip ──
      src_2: "✓ 2 src", src_2_title: "confirmed by 2 sources",
      src_hu_title: "HU = {0} kg vs intl = {1} kg", src_hu: "HU", src_carsdata: "cars-data",
      tip_sources: "Curb weight sources:",
      tip_intl: "  • cars-data (intl): {0} kg",
      tip_hu: "  • katalogus.hu (HU): {0} kg",
      tip_agree: "✓ sources agree",
      tip_disagree: "⚠ sources disagree — HU is authoritative",
      tip_nomatch: "  • (no Hungarian-catalogue match yet)",
      // ── fee + powertrain labels ──
      fee_ok: "OK", fee_double: "DOUBLE", fee_borderline: "BORDERLINE", fee_unknown: "UNKNOWN",
      pt_electric: "Electric", pt_phev: "PHEV", pt_ice: "ICE",
      // ── parking rule ──
      parking_rule: "{0} over {1} kg pays double Budapest parking fee",
      rule_pt_bev: "BEV", rule_pt_phev: "PHEV", rule_pt_ice: "ICE",
      // ── v2 tabs ──
      tab_policy: "Policy", tab_lookup: "Lookup", tab_browse: "Browse", tab_settings: "Settings",
      // ── v2 policy ──
      v2_filter: "Filter", v2_powertrain: "Powertrain", v2_make: "Make",
      v2_pick_makes: "Pick all makes…", v2_clear_makes: "Clear makes",
      v2_bev_threshold: "BEV (electric) threshold", v2_ice_threshold: "ICE / PHEV / HEV threshold",
      v2_reset_defaults: "↺ Reset to defaults (2000 / 2000)",
      v2_fleet_outcome: "Fleet outcome ·",
      leg_ok: "OK", leg_double: "Double", leg_borderline: "Borderline", leg_unknown: "Unknown",
      v2_border_title: "Border cases — cars paying double within…",
      v2_note_default: "Default 2027 rule: any car (BEV, ICE, PHEV) > 2000 kg.",
      v2_note_current: "Currently: BEV {0} kg · ICE {1} kg.",
      v2_funfact: "💡 Fun fact: even the 1999 kg XPeng P7+ sedan sits just under 2 tonnes. But fit a tow bar (e.g. for a bike rack, ~15–25 kg) and its kerb weight tips over 2 tonnes — so it pays double. A single accessory decides it; countless examples like this show how misguided the idea is.",
      v2_border_hint_top: "Closest to threshold (top {0}):",
      v2_border_hint_none: "No border cases at this policy.",
      // ── v2 lookup ──
      v2_lookup_powertrain: "Powertrain", v2_lookup_weight: "Curb weight (kg)",
      v2_threshold: "Threshold: {0} kg",
      v2_near_title: "Cars near this weight (within 50 kg)",
      v2_lookup_under: "{0} at {1} kg is {2} kg under the {3} kg limit — OK.",
      v2_lookup_over: "{0} at {1} kg is +{2} kg over the {3} kg limit — pays double.",
      v2_lookup_enter: "Enter a weight to see the verdict.",
      // ── v2 browse ──
      v2_browse_ph: "Search make / model / trim",
      v2_browse_count: "{0} of {1} cars",
      v2_browse_empty: "No cars match.",
      v2_hu_catalog_only: "HU-catalogue only",
      // ── v2 settings ──
      v2_text_size: "Text size",
      v2_text_size_hint: "Scales every text on every tab. Persists across launches.",
      v2_current_scale: "Current: {0}×",
      v2_data_source: "Data source",
      v2_data_source_loading: "Loading…",
      v2_data_source_n: "{0} cars in the dataset.",
      v2_filter_hu_hint: "Filter the fleet to variants with a Hungarian-catalogue weight.",
      v2_refresh: "Refresh data",
      v2_refresh_hint: "In-app download of a newer cars.db.gz (configured in a future release).",
      v2_about: "About",
      v2_about_1: "Curb weights from cars-data.com and katalogus.hasznaltauto.hu. The default 2027 policy is any car > 2000 kg.",
      v2_about_2: "UI mirror of the native Android app (Policy Explorer with live threshold simulation).",
      // ── v2 detail + make sheet ──
      v2_close: "✕ Close",
      v2_disagreement: "Disagreement", v2_hu_authoritative: "HU is authoritative",
      v2_primary_source: "Primary source",
      v2_make_filter: "Make filter", v2_make_search_ph: "Search makes…",
      v2_make_count: "{0} selected · {1} total",
      v2_clear: "Clear", v2_all: "All", v2_reset: "Reset", v2_apply: "Apply",
    },
    hu: {
      // ── shared ──
      page_title_legacy: "Magyar autótömegek — budapesti parkolási díj",
      page_title_v2: "carWeights HU — Szabály-böngésző",
      brand: "🅿️ Magyar autótömegek",
      subtitle: "Budapesti súlyalapú parkolási díj (2027-től): minden autó > 2000 kg → dupla",
      export_csv: "⬇ CSV exportálás",
      nav_android: "📱 AndroidApp felület",
      nav_classic: "← Klasszikus felület",
      // ── legacy sidebar ──
      search_label: "Keresés",
      search_ph: "márka / modell / kivitel",
      hu_only_label: "🇭🇺 Csak HU adatok",
      hu_only_hint: "csak magyar forrású tömegadatok",
      filter_on_sale: "Jelenleg kapható Magyarországon",
      f_powertrain: "Hajtáslánc",
      f_fee: "Díj státusz",
      f_subtype: "Altípus",
      f_drivetrain: "Hajtás",
      f_weight: "Saját tömeg (kg)",
      ph_min: "min",
      ph_max: "max",
      include_unknown: "ismeretlen tömeg is",
      sort_label: "Rendezés",
      sort_make: "Márka / modell",
      sort_wdesc: "Tömeg ↓",
      sort_wasc: "Tömeg ↑",
      sort_ydesc: "Évjárat ↓",
      reset_filters: "Szűrők törlése",
      // ── legacy table ──
      th_make: "Márka", th_model: "Modell", th_trim: "Kivitel", th_drive: "Hajtás",
      th_power: "Teljesítmény", th_year: "Évjárat", th_weight: "Saját tömeg", th_fee: "Díj", th_source: "Forrás",
      empty: "Nincs a szűrőkre illeszkedő autó.",
      prev: "← Előző", next: "Következő →",
      page_of: "{0}. / {1}. oldal",
      cars_n: "{0} autó",
      // ── legacy detail ──
      d_powertrain: "Hajtáslánc", d_subtype: "Altípus", d_drivetrain: "Hajtás",
      d_power: "Teljesítmény", d_battery: "Akkumulátor", d_year: "Évjárat",
      d_weight_cd: "Saját tömeg (cars-data)", d_weight_hu: "Saját tömeg (HU katalógus)",
      d_sources: "Források", d_threshold: "Küszöb",
      weight_unknown: "ismeretlen",
      // ── sources cell / tooltip ──
      src_2: "✓ 2 forrás", src_2_title: "két forrás megerősítette",
      src_hu_title: "HU = {0} kg vs nemzetközi = {1} kg", src_hu: "HU", src_carsdata: "cars-data",
      tip_sources: "Saját tömeg források:",
      tip_intl: "  • cars-data (nemzetközi): {0} kg",
      tip_hu: "  • katalogus.hu (HU): {0} kg",
      tip_agree: "✓ a források egyeznek",
      tip_disagree: "⚠ a források eltérnek — a HU a mérvadó",
      tip_nomatch: "  • (még nincs magyar katalógus-találat)",
      // ── fee + powertrain labels ──
      fee_ok: "OK", fee_double: "DUPLA", fee_borderline: "HATÁRESET", fee_unknown: "ISMERETLEN",
      pt_electric: "Elektromos", pt_phev: "PHEV", pt_ice: "Belső égésű",
      // ── parking rule ──
      parking_rule: "{0} {1} kg felett dupla budapesti parkolási díjat fizet",
      rule_pt_bev: "Az elektromos", rule_pt_phev: "A PHEV", rule_pt_ice: "A belső égésű",
      // ── v2 tabs ──
      tab_policy: "Szabály", tab_lookup: "Kalkulátor", tab_browse: "Böngészés", tab_settings: "Beállítások",
      // ── v2 policy ──
      v2_filter: "Szűrő", v2_powertrain: "Hajtáslánc", v2_make: "Márka",
      v2_pick_makes: "Összes márka…", v2_clear_makes: "Márkák törlése",
      v2_bev_threshold: "Elektromos (BEV) küszöb", v2_ice_threshold: "Belső égésű / PHEV / HEV küszöb",
      v2_reset_defaults: "↺ Alapértékek (2000 / 2000)",
      v2_fleet_outcome: "Flotta eredmény ·",
      leg_ok: "OK", leg_double: "Dupla", leg_borderline: "Határeset", leg_unknown: "Ismeretlen",
      v2_border_title: "Határesetek — dupla díjat fizetők ezen belül…",
      v2_note_default: "Alap 2027-es szabály: minden autó (elektromos és belső égésű egyaránt) > 2000 kg.",
      v2_note_current: "Jelenleg: elektromos {0} kg · belső égésű {1} kg.",
      v2_funfact: "💡 Fun fact: az 1999 kg-os XPeng P7+ szedán is épphogy a 2 tonna alatt van. De szereltess rá egy vonóhorgot (pl. kerékpárszállításhoz, ~15–25 kg), és a saját tömege átlépi a 2 tonnát — máris dupla díj. Egyetlen kiegészítő dönt; számtalan ilyen példa mutatja, mennyire elhibázott ez az elképzelés.",
      v2_border_hint_top: "Küszöbhöz legközelebb (első {0}):",
      v2_border_hint_none: "Nincs határeset ennél a szabálynál.",
      // ── v2 lookup ──
      v2_lookup_powertrain: "Hajtáslánc", v2_lookup_weight: "Saját tömeg (kg)",
      v2_threshold: "Küszöb: {0} kg",
      v2_near_title: "Autók e tömeg közelében (±50 kg)",
      v2_lookup_under: "{0} {1} kg-nál {2} kg-mal a {3} kg-os határ alatt — OK.",
      v2_lookup_over: "{0} {1} kg-nál +{2} kg-mal a {3} kg-os határ felett — dupla díj.",
      v2_lookup_enter: "Adj meg egy tömeget az eredményhez.",
      // ── v2 browse ──
      v2_browse_ph: "Keresés márka / modell / kivitel",
      v2_browse_count: "{0} / {1} autó",
      v2_browse_empty: "Nincs találat.",
      v2_hu_catalog_only: "Csak HU katalógus",
      // ── v2 settings ──
      v2_text_size: "Betűméret",
      v2_text_size_hint: "Minden fül minden szövegét méretezi. Megmarad az indítások között.",
      v2_current_scale: "Jelenleg: {0}×",
      v2_data_source: "Adatforrás",
      v2_data_source_loading: "Betöltés…",
      v2_data_source_n: "{0} autó az adatbázisban.",
      v2_filter_hu_hint: "Szűrés a magyar katalógusban szereplő tömegű változatokra.",
      v2_refresh: "Adatok frissítése",
      v2_refresh_hint: "Újabb cars.db.gz letöltése az appból (későbbi kiadásban).",
      v2_about: "Névjegy",
      v2_about_1: "Saját tömegek a cars-data.com és a katalogus.hasznaltauto.hu forrásból. Az alap 2027-es szabály: minden autó > 2000 kg.",
      v2_about_2: "A natív Android app webes mása (Szabály-böngésző élő küszöb-szimulációval).",
      // ── v2 detail + make sheet ──
      v2_close: "✕ Bezárás",
      v2_disagreement: "Eltérés", v2_hu_authoritative: "a HU a mérvadó",
      v2_primary_source: "Elsődleges forrás",
      v2_make_filter: "Márkaszűrő", v2_make_search_ph: "Márkák keresése…",
      v2_make_count: "{0} kiválasztva · {1} összesen",
      v2_clear: "Törlés", v2_all: "Összes", v2_reset: "Alaphelyzet", v2_apply: "Alkalmaz",
    },
  };

  const LS_KEY = "lang";
  let lang = localStorage.getItem(LS_KEY) || "hu";
  if (!STRINGS[lang]) lang = "hu";

  const listeners = [];

  function t(key) {
    let s = (STRINGS[lang] && STRINGS[lang][key]);
    if (s == null) s = (STRINGS.en[key] != null ? STRINGS.en[key] : key);
    if (arguments.length > 1) {
      const args = arguments;
      s = s.replace(/\{(\d+)\}/g, (m, i) => {
        const v = args[Number(i) + 1];
        return v == null ? m : String(v);
      });
    }
    return s;
  }

  function applyStatic(root) {
    root = root || document;
    root.querySelectorAll("[data-i18n]").forEach((el) => {
      el.textContent = t(el.getAttribute("data-i18n"));
    });
    root.querySelectorAll("[data-i18n-ph]").forEach((el) => {
      el.setAttribute("placeholder", t(el.getAttribute("data-i18n-ph")));
    });
    root.querySelectorAll("[data-i18n-title]").forEach((el) => {
      el.setAttribute("title", t(el.getAttribute("data-i18n-title")));
    });
  }

  function updateToggle() {
    const btn = document.getElementById("lang-toggle");
    if (btn) {
      btn.textContent = "🌐 " + (lang === "hu" ? "EN" : "HU");
      btn.setAttribute("title", lang === "hu" ? "Switch to English" : "Váltás magyarra");
    }
  }

  function setLang(next) {
    if (!STRINGS[next] || next === lang) return;
    lang = next;
    localStorage.setItem(LS_KEY, lang);
    document.documentElement.lang = lang;
    applyStatic(document);
    updateToggle();
    listeners.forEach((fn) => { try { fn(lang); } catch (e) { console.error(e); } });
  }

  function onChange(fn) { listeners.push(fn); }

  // Wire up immediately: the toggle button + static text live above this script in <body>.
  document.documentElement.lang = lang;
  applyStatic(document);
  (function wireToggle() {
    const btn = document.getElementById("lang-toggle");
    if (btn) {
      btn.addEventListener("click", () => setLang(lang === "hu" ? "en" : "hu"));
      updateToggle();
    }
  })();

  window.I18N = { t, lang: () => lang, setLang, applyStatic, onChange };
})();
