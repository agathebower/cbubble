#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
source venv/bin/activate
if [ -f .env ]; then
    set -a; source .env; set +a
fi
HOST="${CBUBBLE_HOST:-0.0.0.0}"
PORT="${CBUBBLE_PORT:-8800}"
ENVIRONMENT="${ENVIRONMENT:-production}"

echo "=== cBubble starting on http://${HOST}:${PORT} (env: ${ENVIRONMENT}) ==="

if [ "$ENVIRONMENT" = "development" ]; then
    exec uvicorn backend.main:app --host "$HOST" --port "$PORT" --reload
else
    exec uvicorn backend.main:app --host "$HOST" --port "$PORT"
fi
