#!/usr/bin/env bash
# Re-snapshot the current DB into the repo backup.
set -euo pipefail
cd "$(dirname "$0")/.."
gzip -c data/cars.db > backups/cars.db.gz
echo "backup refreshed: $(ls -lh backups/cars.db.gz | awk '{print $5}')"
