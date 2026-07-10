#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  echo "错误：缺少 .env，请先执行 task setup。"
  exit 1
fi

exec uv run --no-sync python app.py
