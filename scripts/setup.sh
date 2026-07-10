#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "错误：未安装 uv，请参考 https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "已从 .env.example 创建 .env，请按需修改。"
fi

uv sync --frozen
echo "开发环境部署完成。"
