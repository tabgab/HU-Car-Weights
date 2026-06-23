// api.http.js — talks to the live FastAPI backend. Used by the server-hosted UI.
// Defines the same globals (apiGet / apiCsv) as api.local.js so the app code is identical
// whichever backend is in play.
(function () {
  "use strict";
  window.apiGet = function (url) {
    return fetch(url).then((r) => r.json());
  };
  window.apiCsv = function (url) {
    window.location = url; // server streams text/csv with a download disposition
  };
})();
