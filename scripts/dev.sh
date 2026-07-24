#!/usr/bin/env bash
# Launch backend + frontend in parallel. Stops both on Ctrl-C.
#
# Usage:  ./scripts/dev.sh
# Requires: Python venv at backend/.venv with deps installed, Node at frontend/node_modules.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cleanup() {
  echo "Shutting down…"
  kill "${BACKEND_PID:-0}" "${FRONTEND_PID:-0}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Backend
if [ ! -d backend/.venv ]; then
  echo "backend/.venv missing — run: cd backend && python -m venv .venv && pip install -e '.[dev]'"
  exit 1
fi
echo "[backend] http://127.0.0.1:8000"
(cd backend && . .venv/bin/activate && dazuoagent-api) &
BACKEND_PID=$!

# Frontend
if [ ! -d frontend/node_modules ]; then
  echo "frontend/node_modules missing — run: cd frontend && npm install"
  exit 1
fi
echo "[frontend] http://127.0.0.1:5173"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

wait