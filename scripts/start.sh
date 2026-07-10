#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT_DIR/.cache/uv}"

if [[ ! -f .env ]]; then
  echo "错误：缺少 .env，请先执行 task setup。"
  exit 1
fi

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

uv run --no-sync python app.py &
BACKEND_PID=$!
npm --prefix frontend run dev &
FRONTEND_PID=$!
wait -n "$BACKEND_PID" "$FRONTEND_PID"
