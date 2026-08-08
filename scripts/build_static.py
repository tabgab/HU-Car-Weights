#!/usr/bin/env python3
"""Assemble the static GitHub Pages site under docs/ from web/.

The live FastAPI app serves web/ at the domain root, so its pages use absolute paths
(/styles.css, /app.js) and load api.http.js. A GitHub *project* site is served under
/HU-Car-Weights/, so this build:
  - copies web/ -> docs/ (and web/v2/ -> docs/v2/),
  - rewrites absolute asset/link paths to relative,
  - swaps the api.http.js include for carquery.js + api.local.js (serverless backend),
  - regenerates docs/cars.json from the DB.

Run: python3 scripts/build_static.py   (re-run after editing web/ or the data).
"""
import hashlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
DOCS = os.path.join(ROOT, "docs")

# Content hash stamped as ?v=… on cars.json and the JS includes. GitHub Pages serves
# with Cache-Control: max-age=600, so without this a visitor keeps stale data/JS for
# up to 10 minutes (and sticky browser caches even longer) after every deploy.
_VERSION = None


def version() -> str:
    global _VERSION
    if _VERSION is None:
        h = hashlib.md5()
        for rel in ["cars.json"]:
            p = os.path.join(DOCS, rel)
            if os.path.exists(p):
                h.update(open(p, "rb").read())
        for rel in VERBATIM:
            h.update(open(os.path.join(WEB, rel), "rb").read())
        _VERSION = h.hexdigest()[:10]
    return _VERSION

# Files copied verbatim (relative to web/).
VERBATIM = [
    "app.js", "styles.css", "carquery.js", "api.local.js", "i18n.js",
    "v2/app.js", "v2/styles.css",
]

# Per-file HTML rewrites: (src rel path, dst rel path, [(old, new), ...]).
# {v} in the replacement is filled with the content-hash version at build time.
HTML = [
    ("index.html", "index.html", [
        ('href="/styles.css', 'href="styles.css'),
        ('href="/v2/"', 'href="v2/"'),
        ('<script src="/i18n.js"></script>', '<script src="i18n.js?v={v}"></script>'),
        ('<script src="/api.http.js"></script>',
         '<script src="carquery.js?v={v}"></script>\n<script src="api.local.js?v={v}"></script>'),
        ('src="/app.js', 'src="app.js?v={v}'),
    ]),
    ("v2/index.html", "v2/index.html", [
        ('href="/v2/styles.css', 'href="styles.css'),
        ('href="/"', 'href="../"'),
        ('<script src="/i18n.js"></script>', '<script src="../i18n.js?v={v}"></script>'),
        ('<script src="/api.http.js"></script>',
         '<script src="../carquery.js?v={v}"></script>\n  <script src="../api.local.js?v={v}"></script>'),
        ('src="/v2/app.js"', 'src="app.js?v={v}"'),
    ]),
]

# carquery.js resolves cars.json from its own URL; stamp the version into that fetch.
_CARSJSON_OLD = 'new URL("cars.json", SCRIPT_SRC)'
_CARSJSON_NEW = 'new URL("cars.json?v={v}", SCRIPT_SRC)'


def copy_verbatim():
    for rel in VERBATIM:
        src = os.path.join(WEB, rel)
        dst = os.path.join(DOCS, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if rel == "carquery.js":
            js = open(src, encoding="utf-8").read()
            if _CARSJSON_OLD not in js:
                sys.exit(f"ERROR: cars.json fetch snippet not found in {rel}:\n  {_CARSJSON_OLD!r}")
            with open(dst, "w", encoding="utf-8") as f:
                f.write(js.replace(_CARSJSON_OLD, _CARSJSON_NEW.format(v=version())))
        else:
            shutil.copyfile(src, dst)


def transform_html():
    for src_rel, dst_rel, reps in HTML:
        with open(os.path.join(WEB, src_rel), encoding="utf-8") as f:
            html = f.read()
        for old, new in reps:
            if old not in html:
                sys.exit(f"ERROR: expected snippet not found in {src_rel}:\n  {old!r}")
            html = html.replace(old, new.format(v=version()))
        dst = os.path.join(DOCS, dst_rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(html)


def check_no_abs_refs():
    """Fail loudly if any leading-slash asset/link refs remain (they 404 under a subpath)."""
    bad = []
    for rel in ["index.html", "v2/index.html"]:
        with open(os.path.join(DOCS, rel), encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                for tok in ('href="/', 'src="/'):
                    if tok in line:
                        bad.append(f"{rel}:{i}: {line.strip()}")
    if bad:
        sys.exit("ERROR: absolute refs remain (break under /HU-Car-Weights/):\n  " +
                 "\n  ".join(bad))


def main():
    os.makedirs(os.path.join(DOCS, "v2"), exist_ok=True)
    # Regenerate the data FIRST so the cache-bust version hashes the fresh dataset.
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "export_cars_json.py")],
                   check=True)
    copy_verbatim()
    transform_html()
    check_no_abs_refs()
    # .nojekyll: serve files as-is (no Jekyll processing).
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    print(f"Built static site -> docs/  (v={version()}; open docs/index.html and docs/v2/)")


if __name__ == "__main__":
    main()
