#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${1:-thinkpad}"
PORT="${2:-22}"
REMOTE_USER="${3:-w1ndys}"
REMOTE_DIR="${4:-/opt/$(basename "$ROOT_DIR")}"
PROJECT_NAME="$(basename "$ROOT_DIR")"
IMAGE_NAME="${PROJECT_NAME}:latest"
BASE_IMAGE="ghcr.io/astral-sh/uv:python3.11-bookworm-slim"
BUILD_DIR="$(mktemp -d)"
ARCHIVE_NAME="${PROJECT_NAME}-deploy.tar.gz"
REMOTE_ARCHIVE="/tmp/${ARCHIVE_NAME}"

cleanup() {
  rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

for command_name in docker ssh scp tar gzip; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "错误：缺少命令 ${command_name}。"
    exit 1
  fi
done

if ! docker compose version >/dev/null 2>&1; then
  echo "错误：未安装 Docker Compose 插件。"
  exit 1
fi

if [[ -f .env.production ]]; then
  ENV_FILE=.env.production
elif [[ -f .env ]]; then
  ENV_FILE=.env
else
  ENV_FILE=.env.example
  echo "警告：未找到 .env.production 或 .env，将使用 .env.example。"
fi

echo "[1/6] 拉取构建所需镜像：${BASE_IMAGE}"
docker pull "$BASE_IMAGE"

echo "[2/6] 本地构建应用镜像：${IMAGE_NAME}"
docker compose build --pull app

echo "[3/6] 导出镜像并打包运维配置"
docker save "$IMAGE_NAME" | gzip -1 >"$BUILD_DIR/image.tar.gz"
cp compose.yaml "$BUILD_DIR/compose.yaml"
cp "$ENV_FILE" "$BUILD_DIR/.env"
tar -C "$BUILD_DIR" -czf "$BUILD_DIR/$ARCHIVE_NAME" image.tar.gz compose.yaml .env

echo "[4/6] 上传部署包到 ${REMOTE_USER}@${HOST}:${REMOTE_ARCHIVE}"
scp -P "$PORT" "$BUILD_DIR/$ARCHIVE_NAME" "${REMOTE_USER}@${HOST}:${REMOTE_ARCHIVE}"

echo "[5/6] 远端加载镜像并启动服务"
ssh -p "$PORT" "${REMOTE_USER}@${HOST}" bash -s -- "$REMOTE_DIR" "$REMOTE_ARCHIVE" <<'REMOTE_SCRIPT'
set -Eeuo pipefail

REMOTE_DIR="$1"
REMOTE_ARCHIVE="$2"

if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
elif command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
  DOCKER=(sudo docker)
else
  echo "错误：当前远端用户无法访问 Docker。"
  exit 1
fi

if [[ -w "$(dirname "$REMOTE_DIR")" ]] || [[ -d "$REMOTE_DIR" && -w "$REMOTE_DIR" ]]; then
  mkdir -p "$REMOTE_DIR/data"
  tar -xzf "$REMOTE_ARCHIVE" -C "$REMOTE_DIR"
  rm -f "$REMOTE_ARCHIVE"
else
  sudo mkdir -p "$REMOTE_DIR/data"
  sudo tar -xzf "$REMOTE_ARCHIVE" -C "$REMOTE_DIR"
  sudo chown -R "$(id -u):$(id -g)" "$REMOTE_DIR"
  rm -f "$REMOTE_ARCHIVE"
fi

cd "$REMOTE_DIR"
gzip -dc image.tar.gz | "${DOCKER[@]}" load
"${DOCKER[@]}" compose up -d --remove-orphans --no-build
rm -f image.tar.gz
"${DOCKER[@]}" image prune -f
REMOTE_SCRIPT

echo "[6/6] 部署完成：http://${HOST}"
