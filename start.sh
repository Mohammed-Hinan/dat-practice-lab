#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting DAT Practice Lab..."
echo "  Backend API: http://127.0.0.1:8000"
echo "  Frontend UI: http://localhost:5173"

OLLAMA_PID=""
if command -v ollama >/dev/null 2>&1; then
  if ! curl -sf --max-time 1 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "  Starting tuned local Ollama server (http://127.0.0.1:11434)..."
    OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_FLASH_ATTENTION=1 OLLAMA_KEEP_ALIVE=15m ollama serve >/tmp/dat_practice_lab_ollama.log 2>&1 &
    OLLAMA_PID=$!
    sleep 2
  fi
fi

cleanup() {
  echo ""
  echo "Stopping DAT Practice Lab..."
  kill $BACKEND_PID $FRONTEND_PID ${OLLAMA_PID:+$OLLAMA_PID} 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd "$ROOT_DIR/backend"
  .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

(
  cd "$ROOT_DIR/frontend"
  npm run dev -- --port 5173
) &
FRONTEND_PID=$!

wait
