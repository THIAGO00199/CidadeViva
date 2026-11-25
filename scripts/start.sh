#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

wait_for() {
  local url="$1"
  local label="$2"
  for _ in $(seq 1 30); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      printf '✓ %s disponível\n' "$label"
      return 0
    fi
    sleep 1
  done
  printf 'Aviso: %s não respondeu dentro do prazo. Consulte %s\n' "$label" "$LOG_DIR"
  return 1
}

if ! curl -fsS http://127.0.0.1:11435/api/tags >/dev/null 2>&1; then
  setsid env OLLAMA_HOST=127.0.0.1:11435 ollama serve >"$LOG_DIR/ollama.log" 2>&1 &
  echo $! > "$LOG_DIR/ollama.pid"
  wait_for http://127.0.0.1:11435/api/tags "Ollama" || true
else
  printf '✓ Ollama já está em execução\n'
fi

if ! curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
  (
    cd "$ROOT/backend"
    setsid env OLLAMA_URL=http://127.0.0.1:11435 \
      OLLAMA_MODEL=qwen2.5:3b OLLAMA_NUM_CTX=3072 \
      .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 \
      >"$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$LOG_DIR/backend.pid"
  )
  wait_for http://127.0.0.1:8000/api/health "API Cidade Viva" || true
else
  printf '✓ API Cidade Viva já está em execução\n'
fi

if ! curl -fsS http://127.0.0.1:5173/ >/dev/null 2>&1; then
  (
    cd "$ROOT/frontend"
    setsid npm run dev -- --host 127.0.0.1 --port 5173 \
      >"$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
  )
  wait_for http://127.0.0.1:5173/ "Interface Cidade Viva" || true
else
  printf '✓ Interface Cidade Viva já está em execução\n'
fi

printf '\nCidade Viva\n'
printf 'Interface: http://127.0.0.1:5173\n'
printf 'API:       http://127.0.0.1:8000/api/health\n'
printf 'Logs:      %s\n' "$LOG_DIR"
