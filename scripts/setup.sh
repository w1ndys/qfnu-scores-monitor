#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT_DIR/.cache/uv}"

for command_name in uv npm; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "错误：未安装 ${command_name}。"
    exit 1
  fi
done

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "已从 .env.example 创建 .env，请按需修改。"
fi

uv sync --frozen
npm --prefix frontend install
echo "开发环境部署完成。"
