#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
echo "=== cBubble Setup ==="
cd "$PROJECT_DIR"
if [ ! -d "venv" ]; then
    echo "[+] Creating Python virtual environment..."
    python3 -m venv venv
fi
echo "[+] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
if [ ! -f ".env" ]; then
    echo "[+] Creating .env from .env.example..."
    cp .env.example .env
    chmod 600 .env
    echo "    ⚠️  Please edit .env and add your API keys!"
fi
for dir in backend backend/llm backend/feeds backend/abstracts backend/workers backend/api; do
    touch "$dir/__init__.py"
done
echo ""
echo "=== Setup complete ==="
echo "  1. Edit .env with your API keys"
echo "  2. Run: ./scripts/run.sh"
