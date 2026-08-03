#!/usr/bin/env bash
# Re-snapshot the current DB into the repo backup.
#
# The DB runs in WAL mode (carweights/db/connection.py), so freshly committed pages
# may still live only in data/cars.db-wal. Gzipping data/cars.db on its own can
# therefore silently drop recent writes, or capture a torn page if a scrape is
# mid-write. sqlite3's .backup uses the online backup API instead: it takes a read
# lock, folds the WAL in, and produces one consistent self-contained file that needs
# no -wal/-shm sidecar to restore.
set -euo pipefail
cd "$(dirname "$0")/.."

DB="${CARWEIGHTS_DB:-data/cars.db}"
OUT="backups/cars.db.gz"
# Temp files live beside the target so the final mv is an atomic same-filesystem
# rename; *.db is gitignored, so the snapshot never shows up as untracked.
TMPDB="backups/.refresh-$$.db"
TMPGZ="backups/.refresh-$$.db.gz"
trap 'rm -f "$TMPDB" "$TMPDB-wal" "$TMPDB-shm" "$TMPGZ"' EXIT INT TERM

[[ -f "$DB" ]] || { echo "ERROR: no database at $DB" >&2; exit 1; }
command -v sqlite3 >/dev/null || { echo "ERROR: sqlite3 not found on PATH" >&2; exit 1; }

# .timeout matches the 30s busy_timeout the pipeline uses, so a concurrent scrape
# makes this wait rather than fail outright.
sqlite3 -cmd '.timeout 30000' "$DB" ".backup '$TMPDB'"

# A corrupt snapshot is worse than a stale one — never publish one that fails to verify.
check="$(sqlite3 "$TMPDB" 'PRAGMA integrity_check;')"
[[ "$check" == "ok" ]] || { echo "ERROR: snapshot failed integrity_check: $check" >&2; exit 1; }
variants="$(sqlite3 "$TMPDB" 'SELECT COUNT(*) FROM variants;')"

gzip -c "$TMPDB" > "$TMPGZ"
mv "$TMPGZ" "$OUT"   # atomic: an interrupted run leaves the previous backup intact

echo "backup refreshed: $OUT ($(du -h "$OUT" | cut -f1), $variants variants)"
