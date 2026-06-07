#!/usr/bin/env bash
# Launch the carWeights web app locally at http://127.0.0.1:8000
set -euo pipefail
cd "$(dirname "$0")"
export CARWEIGHTS_DB="${CARWEIGHTS_DB:-$(pwd)/data/cars.db}"
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 "$@"
