#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT_DIR/.cache/uv}"

uv run --no-sync python -m compileall -q app.py backend
npm --prefix frontend run build
