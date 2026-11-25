#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"

for name in frontend backend ollama; do
  pid_file="$LOG_DIR/$name.pid"
  if [[ -f "$pid_file" ]]; then
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
      printf 'Encerrado: %s (grupo/PID %s)\n' "$name" "$pid"
    fi
    rm -f "$pid_file"
  fi
done

printf 'Serviços iniciados manualmente fora do script não são encerrados por este comando.\n'
